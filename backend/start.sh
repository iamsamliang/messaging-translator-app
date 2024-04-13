#! /usr/bin/env bash

# Exit on any error
set -e

# To make sure Python sees the `app` module in backend directory otherwise `python app/backend_prestart.py` won't work
if [[ ":$PYTHONPATH:" != *":/home/ec2-user/translation-messaging-backend:"* ]]; then
    export PYTHONPATH="/home/ec2-user/translation-messaging-backend:$PYTHONPATH"
fi

# Activate the virtual environment
VENV_PATH="/path/to/your/project/venv"

# Test DB connection
$VENV_PATH/bin/python /app/backend_prestart.py

# Run DB migrations
$VENV_PATH/bin/alembic upgrade head

# Run FastAPI app using Uvicorn
$VENV_PATH/bin/uvicorn app.main:app