import os
from pathlib import Path


APP_TITLE = "Control Deck"
REFRESH_SECONDS = int(os.getenv("DASHBOARD_REFRESH_SECONDS", "20"))
CLIENT_POLL_SECONDS = int(os.getenv("DASHBOARD_CLIENT_POLL_SECONDS", "5"))
SAMPLE_SECONDS = int(os.getenv("DASHBOARD_SAMPLE_SECONDS", str(REFRESH_SECONDS)))
HISTORY_SECONDS = int(os.getenv("DASHBOARD_HISTORY_SECONDS", "600"))
FORTUM_SPOT_URL = os.getenv("DASHBOARD_FORTUM_SPOT_URL", "https://www.fortum.com/fi/sahkoa/sahkon-hinta/spot-hinta")
FORTUM_PRICE_AREA = os.getenv("DASHBOARD_FORTUM_PRICE_AREA", "FI")
FORTUM_CACHE_SECONDS = int(os.getenv("DASHBOARD_FORTUM_CACHE_SECONDS", "300"))
DEFAULT_MSI_AUTO_POWEROFF_THRESHOLD = float(os.getenv("DASHBOARD_MSI_AUTO_POWEROFF_THRESHOLD", "2.000"))
MSI_AUTO_POWEROFF_COOLDOWN_SECONDS = int(os.getenv("DASHBOARD_MSI_AUTO_POWEROFF_COOLDOWN_SECONDS", "1800"))
APP_ROOT = Path(__file__).resolve().parents[2]
HISTORY_FILE = Path(os.getenv("DASHBOARD_HISTORY_FILE", str(APP_ROOT / "data" / "history.json")))
SETTINGS_FILE = Path(os.getenv("DASHBOARD_SETTINGS_FILE", str(APP_ROOT / "data" / "settings.json")))
GYM_USER_DB_FILE = Path(os.getenv("DASHBOARD_GYM_USER_DB_FILE", str(APP_ROOT / "data" / "gym_user.db")))
GYM_KNOWLEDGE_DB_FILE = Path(os.getenv("DASHBOARD_GYM_KNOWLEDGE_DB_FILE", str(APP_ROOT / "data" / "gym_knowledge.db")))
COACH_ATTACHMENTS_DIR = Path(os.getenv("DASHBOARD_COACH_ATTACHMENTS_DIR", str(APP_ROOT / "data" / "coach_uploads")))
COACH_ATTACHMENT_RETENTION_SECONDS = int(os.getenv("DASHBOARD_COACH_ATTACHMENT_RETENTION_SECONDS", "604800"))
COACH_ATTACHMENT_MAX_FILE_BYTES = int(os.getenv("DASHBOARD_COACH_ATTACHMENT_MAX_FILE_BYTES", "8388608"))
COACH_ATTACHMENT_MAX_TOTAL_BYTES_PER_USER = int(os.getenv("DASHBOARD_COACH_ATTACHMENT_MAX_TOTAL_BYTES_PER_USER", "67108864"))
COACH_ATTACHMENT_MAX_FILES_PER_MESSAGE = int(os.getenv("DASHBOARD_COACH_ATTACHMENT_MAX_FILES_PER_MESSAGE", "4"))
OPENAI_API_BASE_URL = os.getenv("DASHBOARD_OPENAI_API_BASE_URL", "https://api.openai.com/v1").rstrip("/")
OPENAI_API_KEY = os.getenv("DASHBOARD_OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", "")).strip()
OPENAI_VISION_MODEL = os.getenv("DASHBOARD_OPENAI_VISION_MODEL", "gpt-4.1-mini").strip() or "gpt-4.1-mini"
OPENAI_VISION_DETAIL = os.getenv("DASHBOARD_OPENAI_VISION_DETAIL", "high").strip().lower() or "high"
OPENAI_VISION_TIMEOUT_SECONDS = int(os.getenv("DASHBOARD_OPENAI_VISION_TIMEOUT_SECONDS", "45"))
OPENAI_VISION_MAX_IMAGES_PER_MESSAGE = int(os.getenv("DASHBOARD_OPENAI_VISION_MAX_IMAGES_PER_MESSAGE", "2"))
GYM_MISC_DIR = APP_ROOT / "misc"
GRAPH_WIDTH = 164
GRAPH_HEIGHT = 50
GRAPH_PADDING = 6
GRAPH_GAP_SECONDS = max(45, SAMPLE_SECONDS * 3)
HISTORY_METRICS = ("cpu_percent", "memory_percent", "disk_percent", "temperature_c")
DEFAULT_GYM_PREFERRED_MINUTES = 60
DEFAULT_GYM_DAYS_PER_WEEK = 4
DEFAULT_DIET_MEALS_PER_DAY = 3
DIET_PLANNER_VERSION = 3
EXERCISE_DB_URL = os.getenv("DASHBOARD_EXERCISE_DB_URL", "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json")
EXERCISE_IMAGE_BASE_URL = os.getenv("DASHBOARD_EXERCISE_IMAGE_BASE_URL", "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/")
EXERCISE_MEDIA_CACHE_FILE = Path(os.getenv("DASHBOARD_EXERCISE_MEDIA_CACHE_FILE", str(APP_ROOT / "data" / "exercise_media_cache.json")))
EXERCISE_MEDIA_CACHE_SECONDS = int(os.getenv("DASHBOARD_EXERCISE_MEDIA_CACHE_SECONDS", "86400"))
AGENT_REMOTE_TIMEOUT_SECONDS = int(os.getenv("DASHBOARD_AGENT_REMOTE_TIMEOUT_SECONDS", "180"))
AGENT_OUTPUT_MAX_CHARS = int(os.getenv("DASHBOARD_AGENT_OUTPUT_MAX_CHARS", "1400"))
GYM_PROFILE_GOALS = {
    "fat_loss": "Fat loss with muscle retention",
    "recomp": "Body recomposition",
    "muscle_gain": "Lean muscle gain",
    "strength": "Strength and performance",
}
HEALTH_GENDER_OPTIONS = {
    "unspecified": "Not set",
    "female": "Female",
    "male": "Male",
}
AGENT_DISPLAY_NAMES = {
    "diet": "Diet AI Coach",
    "gym": "Gym AI Coach",
}
SUPERAGENT_NAME = "Control Deck Coach"
ASSISTANT_ALLOWED_ACTIONS = {
    "record_weight_checkin": "Record a weight check-in",
    "record_health_measurement": "Record a health measurement",
    "update_height_cm": "Update height",
    "update_age_years": "Update age",
    "update_target_weight": "Update target weight",
    "update_gender": "Update gender",
    "update_goal": "Update training goal",
    "update_training_days_per_week": "Change training days per week",
    "update_session_minutes": "Change session length",
    "update_meals_per_day": "Change meals per day",
    "set_diet_preferences": "Adjust diet preferences",
    "customize_diet_meal": "Customize a diet meal",
    "set_gym_split": "Change gym split",
    "replace_gym_exercise": "Replace a gym exercise",
    "update_gym_exercise_scheme": "Adjust gym sets, reps, or rest",
    "update_gym_exercise_load": "Adjust gym suggested load",
    "refresh_diet_plan": "Refresh today's diet plan",
}
COACH_SCOPE_OPTIONS = {
    "today": "Today only",
    "long_term": "Regular plan",
}
DIET_MEAL_CUSTOMIZATION_MODES = {
    "append": "Add to the current meal",
    "replace": "Replace the current meal",
}
DIET_PREFERENCE_OPTIONS = {
    "balanced": "Balanced",
    "high_protein": "High protein",
    "lower_carb": "Lower carb",
    "higher_carb": "Higher carb",
    "lighter_day": "Lighter day",
    "easy_prep": "Easy prep",
}
COACH_DIET_MEAL_FOOD_OPTIONS = (
    {
        "key": "boiled_egg",
        "label": "boiled egg",
        "serving_text": "1 boiled egg",
        "aliases": ("boiled egg", "boiled eggs", "hard boiled egg", "hard-boiled egg", "egg", "eggs"),
        "calories": 78,
        "nutrients": {"protein_g": 6.3, "carbs_g": 0.6, "fat_g": 5.3, "fiber_g": 0.0},
    },
    {
        "key": "egg_white",
        "label": "egg white",
        "serving_text": "1 egg white",
        "aliases": ("egg white", "egg whites", "white egg", "white eggs"),
        "calories": 17,
        "nutrients": {"protein_g": 3.6, "carbs_g": 0.2, "fat_g": 0.1, "fiber_g": 0.0},
    },
    {
        "key": "latte",
        "label": "latte",
        "serving_text": "1 latte",
        "aliases": ("latte", "caffe latte", "cafe latte"),
        "calories": 120,
        "nutrients": {"protein_g": 6.0, "carbs_g": 10.0, "fat_g": 6.0, "fiber_g": 0.0},
    },
    {
        "key": "greek_yogurt",
        "label": "Greek yogurt",
        "serving_text": "150 g Greek yogurt",
        "aliases": ("greek yogurt", "yogurt", "yoghurt"),
        "calories": 100,
        "nutrients": {"protein_g": 15.0, "carbs_g": 5.0, "fat_g": 0.0, "fiber_g": 0.0},
    },
    {
        "key": "skyr",
        "label": "skyr",
        "serving_text": "150 g skyr",
        "aliases": ("skyr",),
        "calories": 95,
        "nutrients": {"protein_g": 17.0, "carbs_g": 6.0, "fat_g": 0.5, "fiber_g": 0.0},
    },
    {
        "key": "rolled_oats",
        "label": "rolled oats",
        "serving_text": "40 g rolled oats",
        "aliases": ("rolled oats", "oats", "porridge oats"),
        "calories": 156,
        "nutrients": {"protein_g": 5.3, "carbs_g": 26.5, "fat_g": 2.8, "fiber_g": 4.2},
    },
    {
        "key": "banana",
        "label": "banana",
        "serving_text": "1 banana",
        "aliases": ("banana", "bananas"),
        "calories": 105,
        "nutrients": {"protein_g": 1.3, "carbs_g": 27.0, "fat_g": 0.4, "fiber_g": 3.1},
    },
    {
        "key": "apple",
        "label": "apple",
        "serving_text": "1 apple",
        "aliases": ("apple", "apples"),
        "calories": 95,
        "nutrients": {"protein_g": 0.5, "carbs_g": 25.0, "fat_g": 0.3, "fiber_g": 4.4},
    },
    {
        "key": "cottage_cheese",
        "label": "cottage cheese",
        "serving_text": "150 g cottage cheese",
        "aliases": ("cottage cheese",),
        "calories": 135,
        "nutrients": {"protein_g": 18.0, "carbs_g": 6.0, "fat_g": 3.5, "fiber_g": 0.0},
    },
    {
        "key": "whole_grain_toast",
        "label": "whole-grain toast",
        "serving_text": "2 slices whole-grain toast",
        "aliases": ("whole-grain toast", "whole grain toast", "toast", "bread"),
        "calories": 180,
        "nutrients": {"protein_g": 8.0, "carbs_g": 30.0, "fat_g": 2.2, "fiber_g": 5.0},
    },
    {
        "key": "chicken_breast",
        "label": "chicken breast",
        "serving_text": "120 g chicken breast",
        "aliases": ("chicken breast", "chicken"),
        "calories": 198,
        "nutrients": {"protein_g": 37.0, "carbs_g": 0.0, "fat_g": 4.3, "fiber_g": 0.0},
    },
    {
        "key": "cooked_rice",
        "label": "cooked rice",
        "serving_text": "150 g cooked rice",
        "aliases": ("cooked rice", "rice"),
        "calories": 195,
        "nutrients": {"protein_g": 3.8, "carbs_g": 42.5, "fat_g": 0.4, "fiber_g": 0.6},
    },
    {
        "key": "tuna",
        "label": "tuna",
        "serving_text": "1 can tuna",
        "aliases": ("tuna", "tuna in water", "tuna can"),
        "calories": 132,
        "nutrients": {"protein_g": 29.0, "carbs_g": 0.0, "fat_g": 1.0, "fiber_g": 0.0},
    },
)
DIET_MEAL_COUNT_OPTIONS = (3, 5)
REMOTE118 = {
    "host": os.getenv("REMOTE118_HOST", "192.168.1.118"),
    "user": os.getenv("REMOTE118_USER", "sam"),
    "port": int(os.getenv("REMOTE118_PORT", "22")),
    "key_path": os.getenv("REMOTE118_KEY_PATH", "/home/sam/.ssh/dashboard_118"),
    "mac": os.getenv("REMOTE118_MAC", "44:8a:5b:41:79:c0"),
    "wake_broadcast": os.getenv("REMOTE118_WAKE_BROADCAST", "192.168.1.255"),
}
REMOTE_SNAPSHOT_SCRIPT = r"""
import json
import os
import shutil
import subprocess
import time


def cpu_percent(delay=0.15):
    def read():
        with open('/proc/stat', 'r', encoding='utf-8') as handle:
            parts = handle.readline().split()[1:]
        values = [int(item) for item in parts]
        idle = values[3] + values[4]
        total = sum(values)
        return idle, total

    idle1, total1 = read()
    time.sleep(delay)
    idle2, total2 = read()
    idle_delta = idle2 - idle1
    total_delta = total2 - total1
    if total_delta <= 0:
        return 0.0
    return round(100.0 * (1.0 - (idle_delta / total_delta)), 1)


def meminfo():
    values = {}
    with open('/proc/meminfo', 'r', encoding='utf-8') as handle:
        for line in handle:
            key, value = line.split(':', 1)
            values[key] = int(value.strip().split()[0])
    total = values.get('MemTotal', 0)
    available = values.get('MemAvailable', 0)
    used = max(total - available, 0)
    percent = round((used / total) * 100, 1) if total else 0.0
    return {
        'total_gb': round(total / 1024 / 1024, 2),
        'used_gb': round(used / 1024 / 1024, 2),
        'percent': percent,
    }


def temperature():
    probes = [
        '/sys/class/thermal/thermal_zone0/temp',
        '/sys/class/thermal/thermal_zone1/temp',
    ]
    for probe in probes:
        if os.path.exists(probe):
            with open(probe, 'r', encoding='utf-8') as handle:
                raw = handle.read().strip()
            try:
                value = float(raw)
            except ValueError:
                continue
            return round(value / 1000.0, 1) if value > 1000 else round(value, 1)
    return None


def containers():
    result = subprocess.run(
        ['docker', 'ps', '-a', '--format', '{{json .}}'],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    items = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        items.append(
            {
                'name': payload.get('Names', ''),
                'image': payload.get('Image', ''),
                'status_text': payload.get('Status', ''),
            }
        )
    return items, (result.stderr or '').strip() if result.returncode else ''


disk = shutil.disk_usage('/')
container_items, container_error = containers()
payload = {
    'reachable': True,
    'hostname': subprocess.run(['hostname'], capture_output=True, text=True, check=False).stdout.strip() or 'server-118',
    'cpu_percent': cpu_percent(),
    'load_avg': [round(value, 2) for value in os.getloadavg()],
    'memory': meminfo(),
    'disk': {
        'total_gb': round(disk.total / 1024 / 1024 / 1024, 1),
        'used_gb': round((disk.total - disk.free) / 1024 / 1024 / 1024, 1),
        'percent': round(((disk.total - disk.free) / disk.total) * 100, 1) if disk.total else 0.0,
    },
    'temperature_c': temperature(),
    'uptime_seconds': int(float(open('/proc/uptime', 'r', encoding='utf-8').read().split()[0])),
    'containers': container_items,
    'container_error': container_error,
}

print(json.dumps(payload))
"""
