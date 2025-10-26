Railway / Render — Use Waitress instead of gunicorn

Why this file

If gunicorn caused runtime problems on Railway (or if you're unsure which WSGI server to use), Waitress is a pure-Python WSGI server that's simple, reliable, and well-supported across platforms. This project has been updated to use Waitress by default inside the Docker image.

Options

1) Deploy with the included Dockerfile (recommended)
- The repository contains `Dockerfile` which copies a tiny `start.sh` and runs Waitress.
- Steps:
  - Push the repo to GitHub and connect it to Railway.
  - Railway will build the Docker image using the `Dockerfile` in the repo.
  - Ensure environment variables are set (e.g., `SECRET_KEY`, `DATABASE_URL`) in Railway.
  - The container will start and Waitress will bind to the `PORT` Railway provides.

2) Deploy without Docker (Platform builds a Python app)
- If you choose to let Railway build from the repo (no Docker), set the start command to:

  waitress-serve --listen=0.0.0.0:$PORT app:app

- Ensure `requirements.txt` is used by the build and that `waitress` is present (it is included in `requirements.txt`).
- Add necessary environment variables in Railway (e.g., `SECRET_KEY`, `DATABASE_URL`).

Notes & troubleshooting

- Why Waitress? It's simple, cross-platform, and doesn't require the system-specific binary packaging that gunicorn sometimes expects.
- If you previously saw an error about `gunicorn: executable not found`, that should no longer happen after the rebuild because the project now uses Waitress.
- If the container still fails to start, check Railway logs for the first error line and share it.

Local testing

- To test locally (without Docker), create a virtualenv, install requirements, and run:

  python -m venv .venv
  .\.venv\Scripts\Activate.ps1  # PowerShell on Windows
  pip install -r requirements.txt
  set PORT=5000; waitress-serve --listen=0.0.0.0:5000 app:app

(Or on PowerShell use $Env:PORT=5000; waitress-serve --listen=0.0.0.0:5000 app:app)

If you want me to also remove the gunicorn mention from other docs or add a `Procfile` for other hosts, tell me which file to edit and I'll update it.