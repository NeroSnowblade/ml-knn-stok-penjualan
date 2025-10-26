Render deployment guide for this Flask app

This document walks you through deploying the project to Render (https://render.com). It assumes you have a GitHub repository for the project and a Render account.

Overview
- We provide two options on Render:
  1. Auto-build from repo (Python environment) — set Build & Start commands.
  2. Deploy using Dockerfile (recommended for exact parity).

Quick checklist before deploying
1. Ensure `requirements.txt` is up-to-date.
2. Ensure `app.py` exposes `app = create_app()` (present in repo).
3. Do NOT commit any secret keys. Use Render Environment variables to provide `SECRET_KEY` and `DATABASE_URL`.

Recommended: use Render's Managed Postgres for production DB.

Option A — Deploy with Dockerfile (recommended)
1. Commit and push the repo (including this Dockerfile) to GitHub.
2. On Render:
   - Create a new Web Service -> Connect a repository -> select your repo and branch.
   - Choose "Docker" (Render will use the Dockerfile).
   - Set environment variables (in the Render service settings):
     - SECRET_KEY (set to a secure random string)
     - FLASK_ENV=production
     - (optional) other secrets like EMAIL credentials
   - If you will use Postgres, create a Managed Database on Render (see below) and set `DATABASE_URL` in the Web Service's environment variables to the value given by the managed DB.
   - Deploy.

Option B — Deploy by letting Render install deps (no Dockerfile)
1. Create Web Service -> connect repo
2. Environment: Python
3. Build Command: pip install -r requirements.txt
4. Start Command: gunicorn app:app --workers 3 --bind 0.0.0.0:$PORT
5. Set environment variables (SECRET_KEY, FLASK_ENV=production, DATABASE_URL).
6. Deploy.

Managed Postgres on Render
1. In Render dashboard, create a new "Postgres" instance.
2. After it's ready, go to the DB details. Copy the DATABASE_URL connection string.
3. Add `DATABASE_URL` as an Environment Variable in the Web Service (or use the Render UI datastore linking if available).

Database initialization & seeding
- On first deploy the app will run normally but may require creating tables and seeding data.
- You have options:
  1. Use Render's Web Console (open a shell) and run a Python one-liner to create tables and seed:
     - Example commands (in Render shell):
       python -c "from app import create_app; app=create_app(); from app import db; from app.utils import seed_dummy_electronics_data; with app.app_context(): db.create_all(); seed_dummy_electronics_data(12)"
  2. Or, after deploy, visit the admin-only URL `/admin/seed-dummy` (login as admin/admin123) to trigger seeding. Make sure the default admin exists (seed_default_admin runs at startup).

Environment variables you should set on Render
- SECRET_KEY — random secret
- FLASK_ENV — production
- DATABASE_URL — connection string for Postgres (optional; if omitted the app will use sqlite:///app.db)

Ports and Webserver
- Render sets $PORT automatically. The Dockerfile and `gunicorn ... $PORT` command above honor this.

Logging & troubleshooting
- Use Render logs to see startup errors.
- If you see import issues, check `requirements.txt`.
- If DB fails, open the Render DB console and test connections.

Optional: use a background job or Render cron to run periodic maintenance.

Want me to create a Render `render.yaml` too?
- I can produce a `render.yaml` with a web service and managed DB resources, but linking managed DB automatically sometimes requires Render-specific service names.
- Tell me if you want the `render.yaml` and I’ll add a draft you can adapt.

If you'd like, I can also:
- Add a small `Makefile` with convenience commands for local run / build.
- Add a tiny `start.sh` to ensure `$PORT` fallback.

