#!/bin/bash
cd "$(dirname "$0")"
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --debug
