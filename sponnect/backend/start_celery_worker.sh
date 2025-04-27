#!/bin/bash

# Start Celery Worker for the Sponnect application
# This script starts a Celery worker that will process tasks including the minute reminder

echo "Starting Celery Worker for Sponnect..."
celery -A workers.celery worker --loglevel=info 