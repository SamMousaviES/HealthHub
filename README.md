# Health Subdomain Project

Separate movable copy of the Control Deck app for `health.sam-mousavi.com`.

This copy is intended to run independently from the main dashboard deployment:

- no `Servers` tab on the health hostname
- its own user database
- its own knowledge database
- its own attachment storage
- registration allowed for member users

## Purpose

Use this project when you want a health-focused deployment that keeps:

- `Health`
- `Diet`
- `Gym`
- `Coach`

and leaves infrastructure controls only on the main dashboard host.

## Project Layout

- `app.py`: Flask entrypoint
- `src/dashboard/`: auth, remote helpers, gym, diet, and coach logic
- `templates/`: HTML templates
- `static/`: CSS and client-side behavior
- `service/health-dashboard.service`: systemd service for the health deployment
- `nginx/health.sam-mousavi.com.conf`: nginx TLS site
- `nginx/health.sam-mousavi.com.http.conf`: nginx HTTP redirect site
- `data/`: local runtime data and SQLite files

## Data Separation

This project should not share its runtime files with the main dashboard deployment.

Keep these health-local paths separate:

- `data/gym_user.db`
- `data/gym_knowledge.db`
- `data/coach_uploads/`
- `data/history.json`
- `data/settings.json`
- `data/exercise_media_cache.json`

The provided `.env.example` already points to these local paths so the folder can be moved freely.

## Users

Default intended seeded accounts for this health copy:

- `sam`
- `melina`
- `nora`

Usernames are case-insensitive.

New users can register from the login page on the health host and are created as `member` users.

## Environment

Copy `.env.example` to `.env` and adjust anything environment-specific.

Important defaults in this health copy:

- `DASHBOARD_PORT=8092`
- `DASHBOARD_EXTRA_DEFAULT_USERS=melina,nora`
- local `data/...` database and storage paths

Optional values you may need to change:

- `DASHBOARD_USERNAME`
- `DASHBOARD_PASSWORD`
- `DASHBOARD_SECRET_KEY`
- `REMOTE118_*`
- `DASHBOARD_OPENAI_API_KEY`

## Local Run

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Default local port:

- `8092`

## Production Deploy

Recommended target on server `106`:

- project path: `/home/sam/Docker/health`
- service file: `/etc/systemd/system/health-dashboard.service`
- nginx site: `/etc/nginx/sites-available/health.sam-mousavi.com`
- reverse proxy target: `127.0.0.1:8092`

Typical deploy flow:

1. Copy this project folder to `/home/sam/Docker/health`
2. Copy `.env.example` to `.env` and adjust secrets
3. Create `.venv`
4. Install requirements
5. Install `service/health-dashboard.service`
6. Install `nginx/health.sam-mousavi.com.conf`
7. Reload `systemd` and `nginx`

## Notes

- This copy is designed to be separate from the main dashboard deployment.
- If you also run `dashboard.sam-mousavi.com`, point that deployment at different DB and storage paths.
- `118` remains optional AI compute only. The health site should keep working even when `118` is offline.
