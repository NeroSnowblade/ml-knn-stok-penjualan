#!/bin/sh
# start.sh - tiny entrypoint to run the Flask app with Waitress
# This script respects the $PORT env var provided by platforms like Railway.

PORT_NUMBER="${PORT:-5000}"  # default to 5000 if not set

echo "Starting app with Waitress on 0.0.0.0:${PORT_NUMBER}"
# exec so PID 1 is the server process
exec waitress-serve --listen=0.0.0.0:${PORT_NUMBER} "wsgi:app"
