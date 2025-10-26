from app import create_app

# WSGI entrypoint used by production servers (waitress, gunicorn, etc.)
# This keeps the module name separate from the `app` package to avoid
# import-name collisions that can happen when a top-level module and a
# package share the same name.

app = create_app()
