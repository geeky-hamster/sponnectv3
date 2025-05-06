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

@celery.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    # Daily reminder for pending ad requests - now run every minute
    sender.add_periodic_task(
        60.0,  # Run every 60 seconds
        send_pending_request_reminders.s(),
        name='send_pending_request_reminders'
    )
    
    # Weekly summary for sponsors - now run every minute
    sender.add_periodic_task(
        60.0,  # Run every 60 seconds
        send_weekly_sponsor_summary.s(),
        name='send_weekly_sponsor_summary'
    )
    
    # Monthly analytics report for admins - now run every minute
    sender.add_periodic_task(
        60.0,  # Run every 60 seconds
        send_monthly_admin_report.s(),
        name='send_monthly_admin_report'
    )
    
    # Check for stale ad requests - now run every minute
    sender.add_periodic_task(
        60.0,  # Run every 60 seconds
        check_stale_ad_requests.s(),
        name='check_stale_ad_requests'
    )
    
    # Test minute activity update - already runs every minute
    sender.add_periodic_task(
        60.0,  # Run every 60 seconds
        send_minute_activity_update.s(),
        name='send_minute_activity_update'
    )
    
    # Daily check for pending user approvals - now run every minute
    sender.add_periodic_task(
        60.0,  # Run every 60 seconds
        notify_admin_pending_approvals.s(),
        name='notify_admin_pending_approvals'
    )
    
    # Check for expired campaigns and mark them as completed
    sender.add_periodic_task(
        60.0,  # Run every 60 seconds
        update_expired_campaigns.s(),
        name='update_expired_campaigns'
    )
    
    # NEW TASKS - Detailed stats for all user types
    
    # Sponsor detailed stats - every minute
    sender.add_periodic_task(
        60.0,  # Run every 60 seconds
        send_sponsor_stats_update.s(),
        name='send_sponsor_stats_update'
    )
    
    # Influencer detailed stats - every minute
    sender.add_periodic_task(
        60.0,  # Run every 60 seconds
        send_influencer_stats_update.s(),
        name='send_influencer_stats_update'
    )
    
    # Admin daily report - every minute
    sender.add_periodic_task(
        60.0,  # Run every 60 seconds
        send_admin_daily_report.s(),
        name='send_admin_daily_report'
    )


