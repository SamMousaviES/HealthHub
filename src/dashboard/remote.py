import base64
import json
import shlex
import socket
import subprocess

import paramiko

from .config import AGENT_OUTPUT_MAX_CHARS, AGENT_REMOTE_TIMEOUT_SECONDS, REMOTE118, REMOTE_SNAPSHOT_SCRIPT


def _truncate_text(value: str | None, limit: int):
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "..."


def run_local(command, timeout=20):
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)


def remote_client():
    key_path = REMOTE118["key_path"]
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        REMOTE118["host"],
        port=REMOTE118["port"],
        username=REMOTE118["user"],
        key_filename=key_path,
        look_for_keys=False,
        allow_agent=False,
        timeout=6,
        banner_timeout=6,
        auth_timeout=6,
    )
    return client


def run_remote(command: str, timeout: int = 25):
    client = remote_client()
    try:
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()
        return {
            "returncode": exit_code,
            "stdout": stdout.read().decode("utf-8", errors="replace"),
            "stderr": stderr.read().decode("utf-8", errors="replace"),
        }
    finally:
        client.close()


def remote_codex_exec(prompt: str, timeout: int = AGENT_REMOTE_TIMEOUT_SECONDS):
    prompt_b64 = base64.b64encode(prompt.encode("utf-8")).decode("ascii")
    remote_script = f"""
import base64
import json
import pathlib
import subprocess
import tempfile

prompt = base64.b64decode({prompt_b64!r}).decode("utf-8")
output_file = tempfile.NamedTemporaryFile(prefix="codex-agent-", suffix=".txt", delete=False)
output_path = pathlib.Path(output_file.name)
output_file.close()
cmd = [
    "/usr/local/bin/codex",
    "exec",
    "--skip-git-repo-check",
    "--cd",
    "/home/sam",
    "--ephemeral",
    "-s",
    "read-only",
    "--color",
    "never",
    "-o",
    str(output_path),
    prompt,
]
try:
    completed = subprocess.run(cmd, capture_output=True, text=True, timeout={max(30, timeout)})
    content = ""
    if output_path.exists():
        content = output_path.read_text(encoding="utf-8", errors="replace")
    payload = {{
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "content": content,
    }}
except subprocess.TimeoutExpired as exc:
    payload = {{
        "returncode": 124,
        "stdout": exc.stdout or "",
        "stderr": exc.stderr or "Timed out while waiting for Codex.",
        "content": "",
    }}
finally:
    try:
        output_path.unlink(missing_ok=True)
    except Exception:
        pass
print(json.dumps(payload))
""".strip()
    result = run_remote("python3 - <<'PY'\n" + remote_script + "\nPY", timeout=max(timeout + 20, 60))
    if result["returncode"] != 0:
        raise RuntimeError(result["stderr"].strip() or "Remote Codex runner failed.")
    try:
        payload = json.loads(result["stdout"])
    except json.JSONDecodeError as exc:
        raise RuntimeError("Remote Codex response was not valid JSON.") from exc
    if payload.get("returncode") != 0:
        stderr_text = _truncate_text(payload.get("stderr") or payload.get("stdout") or "Codex execution failed.", 260)
        raise RuntimeError(stderr_text)
    content = str(payload.get("content") or "").strip()
    if not content:
        raise RuntimeError("Codex returned an empty response.")
    return _truncate_text(content, AGENT_OUTPUT_MAX_CHARS)


def collect_remote_snapshot():
    command = "python3 - <<'PY'\n" + REMOTE_SNAPSHOT_SCRIPT + "\nPY"
    try:
        result = run_remote(command, timeout=30)
    except Exception as exc:
        return {
            "reachable": False,
            "error": str(exc),
            "containers": [],
        }
    if result["returncode"] != 0:
        return {
            "reachable": False,
            "error": result["stderr"].strip() or "Remote collection failed",
            "containers": [],
        }
    try:
        return json.loads(result["stdout"])
    except json.JSONDecodeError:
        return {
            "reachable": False,
            "error": "Remote data was not valid JSON",
            "containers": [],
        }


def compose_shell(path: str, action: str, sudo_prefix: str = "") -> str:
    safe_path = shlex.quote(path)
    if action == "start":
        body = "(docker-compose up -d || docker compose up -d)"
    elif action == "stop":
        body = "(docker-compose stop || docker compose stop)"
    elif action == "restart":
        body = "(docker-compose restart || docker compose restart)"
    else:
        raise ValueError("Unsupported compose action")
    if sudo_prefix:
        body = body.replace("docker-compose", f"{sudo_prefix}docker-compose").replace("docker compose", f"{sudo_prefix}docker compose")
    return f"cd {safe_path} && {body}"


def container_shell(containers, action: str, sudo_prefix: str = "") -> str:
    safe_names = " ".join(shlex.quote(item) for item in containers)
    if action == "start":
        verb = "start"
    elif action == "stop":
        verb = "stop"
    elif action == "restart":
        verb = "restart"
    else:
        raise ValueError("Unsupported container action")
    return f"{sudo_prefix}docker {verb} {safe_names}"


def wake_host(mac: str, broadcast: str):
    normalized = mac.replace("-", "").replace(":", "").strip()
    if len(normalized) != 12:
        raise ValueError("Invalid MAC address")
    payload = bytes.fromhex("FF" * 6 + normalized * 16)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(payload, (broadcast, 9))


def remote_host_action(action: str):
    if action == "wake":
        wake_host(REMOTE118["mac"], REMOTE118["wake_broadcast"])
        return "Wake-on-LAN packet sent to server 118."
    if action == "reboot":
        run_remote("bash -lc 'sudo -n systemctl reboot >/dev/null 2>&1 &'")
        return "Reboot command sent to server 118."
    if action == "poweroff":
        run_remote("bash -lc 'sudo -n systemctl poweroff >/dev/null 2>&1 &'")
        return "Poweroff command sent to server 118."
    raise ValueError("Unsupported host action")


def local_host_action(action: str):
    if action != "reboot":
        raise ValueError("Unsupported host action")
    command = "nohup bash -lc 'sleep 3; sudo -n systemctl reboot' >/dev/null 2>&1 &"
    result = run_local(["bash", "-lc", command], timeout=10)
    if result.returncode != 0:
        message = (result.stderr or result.stdout or "Failed to queue reboot").strip()
        raise RuntimeError(message)
    return "Reboot command queued for server 106."
