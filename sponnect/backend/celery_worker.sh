#!/bin/bash
cd "$(dirname "$0")"
celery -A workers.celery worker --loglevel=info
