#!/usr/bin/env python3
"""
Test script for Sponnect notification tasks.
This script runs all notification tasks for testing.
"""

import os
import sys
from flask import Flask
from models import db, User, AdRequest, Campaign
from task import send_minute_activity_update
from user_notifications import (
    send_login_stats,
    send_registration_pending_notification,
    send_account_approval_notification,
    notify_admin_pending_approvals
)

def print_separator(title):
    """Print a separator with title"""
    print("\n" + "=" * 50)
    print(f" {title} ".center(50, "="))
    print("=" * 50 + "\n")

def test_notifications():
    """Run all notification tasks for testing"""
    # Create a minimal Flask app for testing
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sponnect.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        # Get test users
        admin = User.query.filter_by(role='admin').first()
        sponsor = User.query.filter_by(role='sponsor', is_active=True).first()
        influencer = User.query.filter_by(role='influencer', is_active=True).first()
        pending_user = User.query.filter_by(is_active=False).first()
        
        # Check if we have all needed users
        if not admin:
            print("WARNING: No admin user found")
        if not sponsor:
            print("WARNING: No active sponsor found")
        if not influencer:
            print("WARNING: No active influencer found")
        if not pending_user:
            print("WARNING: No pending user found")
        
        # Test all notification functions
        print_separator("Testing Minute Activity Update")
        send_minute_activity_update()
        
        if sponsor:
            print_separator("Testing Sponsor Login Stats")
            send_login_stats(sponsor.id)
        
        if influencer:
            print_separator("Testing Influencer Login Stats")
            send_login_stats(influencer.id)
        
        if pending_user:
            print_separator("Testing Registration Pending Notification")
            send_registration_pending_notification(pending_user.id)
        
        if sponsor:
            print_separator("Testing Sponsor Approval Notification")
            send_account_approval_notification(sponsor.id)
        
        if influencer:
            print_separator("Testing Influencer Approval Notification")
            send_account_approval_notification(influencer.id)
        
        print_separator("Testing Admin Pending Approvals Notification")
        notify_admin_pending_approvals()
        
        print_separator("Test Completed")
        print("All notification tests complete! Check Mailhog for test emails.\n")

if __name__ == "__main__":
    print("Testing Sponnect notification tasks...")
    test_notifications()
    print("Done!") 