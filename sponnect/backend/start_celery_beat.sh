#!/bin/bash

# Start Celery Beat for the Sponnect application
# This script starts Celery Beat for scheduled tasks

echo "Starting Celery Beat for Sponnect..."
celery -A workers.celery beat --loglevel=info 