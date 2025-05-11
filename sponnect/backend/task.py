from workers import celery
from models import db, User, Campaign, AdRequest, Payment, ProgressUpdate
from celery.schedules import crontab
from mailer import send_email
from flask import render_template, render_template_string
from datetime import datetime, timedelta
import os
import csv
import uuid
import json
import logging
from sqlalchemy import desc, func
from app import app as flask_app
from user_notifications import (
    send_minute_activity_update,
    send_registration_pending_notification,
    send_account_approval_notification,
    send_login_stats,
    notify_admin_pending_approvals,
    # New detailed stats tasks
    send_sponsor_stats_update,
    send_influencer_stats_update,
    send_admin_daily_report
)

# Import the update_expired_campaigns task
from app import update_expired_campaigns

# Set up logging
logger = logging.getLogger('celery.tasks')

# Define beat schedule directly
celery.conf.beat_schedule = {
    'send-minute-activity-update': {
        'task': 'user_notifications.send_minute_activity_update',
        'schedule': 60.0,
        'args': ()
    },
    'notify-admin-pending-approvals': {
        'task': 'user_notifications.notify_admin_pending_approvals',
        'schedule': 60.0,
        'args': ()
    },
    'update-expired-campaigns': {
        'task': 'app.update_expired_campaigns',
        'schedule': 60.0,
        'args': ()
    },
    'send-sponsor-stats-update': {
        'task': 'user_notifications.send_sponsor_stats_update',
        'schedule': 60.0,
        'args': ()
    },
    'send-influencer-stats-update': {
        'task': 'user_notifications.send_influencer_stats_update',
        'schedule': 60.0,
        'args': ()
    },
    'send-admin-daily-report': {
        'task': 'user_notifications.send_admin_daily_report',
        'schedule': 60.0,
        'args': ()
    }
}

@celery.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    logger.info("Setting up periodic tasks")
    logger.info("All periodic tasks have been registered via beat_schedule configuration")


