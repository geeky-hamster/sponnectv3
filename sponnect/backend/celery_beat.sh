#!/bin/bash
cd "$(dirname "$0")"
celery -A workers.celery beat --loglevel=info
