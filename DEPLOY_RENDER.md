
Railway deployment guide for this Flask app

This document walks you through deploying the project to Railway (https://railway.app). It assumes you have a GitHub repository for the project and a Railway account.

Overview
- Railway supports deploying from a repository (auto-build) or using a Dockerfile. Railway provides a managed PostgreSQL plugin which exposes a `DATABASE_URL` environment variable — this is convenient for production.

Quick checklist before deploying
1. Ensure `requirements.txt` is up-to-date.
2. Ensure `app.py` exposes `app = create_app()` (present in repo).
3. Do NOT commit any secret keys. Use Railway Environment variables to provide `SECRET_KEY` and `DATABASE_URL`.

Recommended: use Railway's Managed Postgres plugin for production.

Option A — Deploy with Dockerfile (recommended for parity)
1. Commit and push the repo (including the Dockerfile) to GitHub.
2. On Railway:
   - Create a new Project -> Deploy from GitHub -> select your repository and branch.
   - Railway will detect the Dockerfile and build accordingly.
   - In the project settings (Variables), add environment variables:
     - `SECRET_KEY` — a secure random string
     - `FLASK_ENV=production`
     - (optional) other secrets like email credentials
   - If you want a managed Postgres, in your Railway project add the Postgres plugin (Add Plugin -> Postgres). Railway will provision a DB and make a `DATABASE_URL` variable available to your service.
   - Deploy the service.

Option B — Deploy without Docker (Railway auto-build Python)
1. Create a new Project -> Deploy from GitHub -> select the repo/branch.
2. Railway will try to detect the project type. If it selects Python, ensure the following settings are present:
   - Build command: pip install -r requirements.txt
   - Start command: gunicorn app:app --workers 3 --bind 0.0.0.0:$PORT
3. Set environment variables (SECRET_KEY, FLASK_ENV=production, DATABASE_URL if using external DB).
4. Deploy.

Managed Postgres on Railway
1. In the Railway project UI, click "Add Plugin" and choose Postgres.
2. After provisioning, Railway will expose a `DATABASE_URL` environment variable in the project environment automatically.
3. The web service inherits these variables; confirm `DATABASE_URL` is present under variables for the service.

Database initialization & seeding
- After the first deploy you must create tables and (optionally) seed dummy data. Options:
  1. Use Railway's web "Run" command to execute a one-off command in the deployed environment. Example (Railway Web or CLI):
     ```bash
     # With Railway CLI
     railway run python -c "from app import create_app; app=create_app(); from app import db; from app.utils import seed_dummy_electronics_data; with app.app_context(): db.create_all(); seed_dummy_electronics_data(12)"
     ```
     Or use the Railway web "Run" UI to execute the same python -c command.
  2. Simpler: after deploying, visit the admin-only URL `/admin/seed-dummy` (login as admin/admin123) to trigger seeding. The app seeds a default admin at startup.

Environment variables you should set on Railway
- `SECRET_KEY` — a secure random secret
- `FLASK_ENV` — production
- `DATABASE_URL` — connection string from Railway Postgres plugin (if using)

Ports and Webserver
- Railway exposes the `$PORT` environment variable. The Dockerfile and the recommended start command use `$PORT`.

Railway CLI (optional)
- Install the Railway CLI to run commands locally against your Railway project:
  - https://docs.railway.app/develop/cli
- Example one-off run with CLI:
  ```powershell
  railway login
  railway link # link to project
  railway run python -c "from app import create_app; app=create_app(); from app import db; from app.utils import seed_dummy_electronics_data; with app.app_context(): db.create_all(); seed_dummy_electronics_data(12)"
  ```

Logging & troubleshooting
- Use Railway deployments/logs to inspect startup output and errors.
- Common causes of failure: missing env vars, missing dependencies in `requirements.txt`, DB connection string not set.

Optional extras
- If you prefer IaC, I can draft a `railway.json` or `railway` config snippet but Railway’s project linking typically expects you to select plugins via the web UI.
- I can also add a `start.sh` script to the repo to ensure `$PORT` fallback and provide a `Makefile` with convenience targets for local dev.

Next steps I can do for you
- Create a `railway` config draft.
- Add a `start.sh`/`Makefile` for convenience.
- Walk through the Railway dashboard with the exact fields to change.



