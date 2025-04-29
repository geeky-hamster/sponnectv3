"""
User notification tasks for the Sponnect application.
This module contains Celery tasks for sending notifications to users.
"""

from workers import celery
from models import db, User, Campaign, AdRequest, NegotiationHistory, ProgressUpdate, Payment
from mailer import send_email
from datetime import datetime, timedelta
from flask import render_template, render_template_string
from app import app as flask_app
import os
from flask import current_app
from sqlalchemy import func, and_, or_

@celery.task()
def send_minute_activity_update():
    """
    Send activity updates to relevant users (admins, sponsors, influencers)
    This is meant to be run by a scheduled task (e.g., Celery)
    """
    # Get statistics
    total_users = User.query.count()
    total_campaigns = Campaign.query.count()
    total_ad_requests = AdRequest.query.count()
    
    # Recent activity (past day)
    day_ago = func.datetime('now', '-1 day')
    new_users = User.query.filter(User.created_at > day_ago).count()
    new_campaigns = Campaign.query.filter(Campaign.created_at > day_ago).count()
    new_ad_requests = AdRequest.query.filter(AdRequest.created_at > day_ago).count()
    
    # SEND TO ADMINS
    admins = User.query.filter_by(role='admin').all()
    for admin in admins:
        subject = "Sponnect Platform Daily Activity Update"
        
        body = f"""
        <h2>Sponnect Platform Activity Update</h2>
        <p>Hello {admin.username},</p>
        <p>Here's a summary of the current platform status:</p>
        
        <h3>Platform Totals:</h3>
        <ul>
            <li><strong>Total Users:</strong> {total_users}</li>
            <li><strong>Total Campaigns:</strong> {total_campaigns}</li>
            <li><strong>Total Ad Requests:</strong> {total_ad_requests}</li>
        </ul>
        
        <h3>Recent Activity (Last 24 Hours):</h3>
        <ul>
            <li><strong>New Users:</strong> {new_users}</li>
            <li><strong>New Campaigns:</strong> {new_campaigns}</li>
            <li><strong>New Ad Requests:</strong> {new_ad_requests}</li>
        </ul>
        
        <p>Visit your <a href="{os.environ.get('FRONTEND_URL', 'http://localhost:5173')}/admin/dashboard">admin dashboard</a> for more details.</p>
        <p>Best regards,<br>The Sponnect System</p>
        """
        
        send_email(admin.email, subject, body)
    
    # SEND TO SPONSORS
    # For each sponsor, include info about their campaigns and pending requests
    sponsors = User.query.filter_by(role='sponsor', is_active=True).all()
    for sponsor in sponsors:
        sponsor_campaigns = Campaign.query.filter_by(sponsor_id=sponsor.id).count()
        pending_requests = AdRequest.query.join(Campaign).filter(
            Campaign.sponsor_id == sponsor.id,
            AdRequest.status == 'pending'
        ).count()
        
        # Only send if they have pending requests or recent activity
        if pending_requests > 0:
            subject = "Sponnect: Campaign Activity Update"
            
            body = f"""
            <h2>Your Sponnect Campaign Update</h2>
            <p>Hello {sponsor.username},</p>
            <p>Here's a summary of your campaign activity:</p>
            <ul>
                <li><strong>Your Active Campaigns:</strong> {sponsor_campaigns}</li>
                <li><strong>Pending Ad Requests:</strong> {pending_requests}</li>
            </ul>
            <p>Please review and respond to pending applications to keep your campaigns moving.</p>
            <p>Visit your <a href="{os.environ.get('FRONTEND_URL', 'http://localhost:5173')}/sponsor/dashboard">sponsor dashboard</a> to manage your campaigns.</p>
            <p>Best regards,<br>The Sponnect Team</p>
            """
            
            send_email(sponsor.email, subject, body)
    
    # SEND TO INFLUENCERS
    # For each influencer, include matching campaigns and pending applications
    influencers = User.query.filter_by(role='influencer', is_active=True).all()
    for influencer in influencers:
        # Get pending applications
        pending_apps = AdRequest.query.filter_by(
            influencer_id=influencer.id,
            status='pending'
        ).count()
        
        # Get matching campaigns
        matching_campaigns = Campaign.query.filter(
            Campaign.visibility == 'public',
            (Campaign.category == influencer.category) | (Campaign.category == 'any')
        ).count()
        
        # Only send if they have matching campaigns or pending applications
        if matching_campaigns > 0 or pending_apps > 0:
            subject = "Sponnect: Campaign Opportunities Update"
            
            body = f"""
            <h2>Your Sponnect Opportunities Update</h2>
            <p>Hello {influencer.username},</p>
            <p>Here's a summary of your current opportunities:</p>
            <ul>
                <li><strong>Campaigns Matching Your Profile:</strong> {matching_campaigns}</li>
                <li><strong>Your Pending Applications:</strong> {pending_apps}</li>
            </ul>
            <p>Visit your <a href="{os.environ.get('FRONTEND_URL', 'http://localhost:5173')}/influencer/dashboard">influencer dashboard</a> to browse campaigns and check on your applications.</p>
            <p>Best regards,<br>The Sponnect Team</p>
            """
            
            send_email(influencer.email, subject, body)
    
    return "Activity updates sent to all relevant users"


@celery.task()
def send_registration_pending_notification(user_id):
    """
    Send notification to user when they register and are waiting for admin approval
    """
    user = User.query.get(user_id)
    if not user:
        return "User not found"
    
    subject = "Your Sponnect Registration is Pending Approval"
    
    body = f"""
    <h2>Welcome to Sponnect!</h2>
    <p>Hello {user.username},</p>
    <p>Thank you for registering on Sponnect as a {user.role.capitalize()}.</p>
    <p>Your account is currently under review by our admin team. You will receive an email notification once your account is approved.</p>
    <p>This process typically takes 1-2 business days.</p>
    <p>If you have any questions, please contact our support team.</p>
    <p>Best regards,<br>The Sponnect Team</p>
    """
    
    # Send the email
    send_email(user.email, subject, body)
    
    # Also notify admins
    notify_admin_pending_approvals()
    
    return f"Registration pending notification sent to {user.email}"


@celery.task()
def send_account_approval_notification(user_id):
    """
    Send notification to user when their account is approved by an admin
    """
    user = User.query.get(user_id)
    if not user:
        return "User not found"
    
    subject = "Your Sponnect Account Has Been Approved!"
    
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    login_url = f"{frontend_url}/login"
    dashboard_url = f"{frontend_url}/{user.role}/dashboard"
    
    body = f"""
    <h2>Account Approved!</h2>
    <p>Hello {user.username},</p>
    <p>Great news! Your Sponnect account as a {user.role.capitalize()} has been approved by our admin team.</p>
    <p>You can now <a href="{login_url}">log in to your account</a> and start using the platform.</p>
    <p>Visit your <a href="{dashboard_url}">dashboard</a> to:</p>
    """
    
    if user.role == 'sponsor':
        body += """
        <ul>
            <li>Create new campaigns</li>
            <li>Browse influencers</li>
            <li>Manage ad requests</li>
        </ul>
        """
    elif user.role == 'influencer':
        body += """
        <ul>
            <li>Browse available campaigns</li>
            <li>Apply to campaigns</li>
            <li>Manage your partnerships</li>
        </ul>
        """
    
    body += """
    <p>If you have any questions, please contact our support team.</p>
    <p>Best regards,<br>The Sponnect Team</p>
    """
    
    # Send the email
    send_email(user.email, subject, body)
    return f"Account approval notification sent to {user.email}"


@celery.task()
def send_login_stats(user_id):
    """
    Send login stats notification to user
    Called when a user logs in to display pending items and account status
    """
    user = User.query.get(user_id)
    if not user:
        return "User not found"
    
    subject = f"Welcome back to Sponnect, {user.username}!"
    
    if user.role == 'admin':
        # Get stats for admin
        pending_users = User.query.filter(
            ((User.role == 'sponsor') & (User.sponsor_approved.is_(None))) |
            ((User.role == 'influencer') & (User.influencer_approved.is_(None)))
        ).count()
        
        total_users = User.query.count()
        total_campaigns = Campaign.query.count()
        total_ad_requests = AdRequest.query.count()
        
        body = f"""
        <h2>Admin Dashboard Summary</h2>
        <p>Here's a quick summary of your Sponnect platform:</p>
        <ul>
            <li><strong>Pending Approvals:</strong> {pending_users}</li>
            <li><strong>Total Users:</strong> {total_users}</li>
            <li><strong>Active Campaigns:</strong> {total_campaigns}</li>
            <li><strong>Ad Requests:</strong> {total_ad_requests}</li>
        </ul>
        <p>Visit your <a href="{os.environ.get('FRONTEND_URL', 'http://localhost:5173')}/admin/dashboard">admin dashboard</a> to manage the platform.</p>
        """
    
    elif user.role == 'sponsor':
        # Get stats for sponsor
        total_campaigns = Campaign.query.filter_by(sponsor_id=user_id).count()
        pending_requests = AdRequest.query.join(Campaign).filter(
            Campaign.sponsor_id == user_id,
            AdRequest.status == 'pending'
        ).count()
        approved_requests = AdRequest.query.join(Campaign).filter(
            Campaign.sponsor_id == user_id,
            AdRequest.status == 'approved'
        ).count()
        
        body = f"""
        <h2>Sponsor Dashboard Summary</h2>
        <p>Welcome back to your Sponnect sponsor dashboard!</p>
        <ul>
            <li><strong>Your Active Campaigns:</strong> {total_campaigns}</li>
            <li><strong>Pending Ad Requests:</strong> {pending_requests}</li>
            <li><strong>Approved Partnerships:</strong> {approved_requests}</li>
        </ul>
        <p>Visit your <a href="{os.environ.get('FRONTEND_URL', 'http://localhost:5173')}/sponsor/dashboard">sponsor dashboard</a> to manage your campaigns.</p>
        """
    
    elif user.role == 'influencer':
        # Get stats for influencer
        pending_requests = AdRequest.query.filter_by(
            influencer_id=user_id,
            status='pending'
        ).count()
        approved_requests = AdRequest.query.filter_by(
            influencer_id=user_id,
            status='approved'
        ).count()
        
        # Get recently added campaigns that match influencer's niche/category
        matching_campaigns = Campaign.query.filter(
            Campaign.visibility == 'public',
            (Campaign.category == user.category) | (Campaign.category == 'any')
        ).order_by(Campaign.created_at.desc()).limit(3).all()
        
        campaign_list = ""
        if matching_campaigns:
            campaign_list = "<ul>"
            for campaign in matching_campaigns:
                campaign_list += f"<li><strong>{campaign.name}</strong> - {campaign.description[:100]}...</li>"
            campaign_list += "</ul>"
        
        body = f"""
        <h2>Influencer Dashboard Summary</h2>
        <p>Welcome back to your Sponnect influencer dashboard!</p>
        <ul>
            <li><strong>Pending Applications:</strong> {pending_requests}</li>
            <li><strong>Approved Partnerships:</strong> {approved_requests}</li>
        </ul>
        
        <h3>New Campaigns That Match Your Profile:</h3>
        {campaign_list if matching_campaigns else "<p>No new matching campaigns at the moment.</p>"}
        
        <p>Visit your <a href="{os.environ.get('FRONTEND_URL', 'http://localhost:5173')}/influencer/dashboard">influencer dashboard</a> to browse campaigns and manage your applications.</p>
        """
    
    else:
        return f"Unknown user role: {user.role}"
    
    # Send the email
    send_email(user.email, subject, body)
    return f"Login stats sent to {user.email}"


def notify_admin_pending_approvals():
    """
    Notify admins about pending user approvals
    """
    # Get counts of pending approvals
    pending_sponsors = User.query.filter(
        (User.role == 'sponsor') & (User.sponsor_approved.is_(None))
    ).count()
    
    pending_influencers = User.query.filter(
        (User.role == 'influencer') & (User.influencer_approved.is_(None))
    ).count()
    
    if pending_sponsors == 0 and pending_influencers == 0:
        return "No pending approvals"
    
    # Get admin emails
    admins = User.query.filter_by(role='admin').all()
    if not admins:
        return "No admin users found"
    
    subject = "Sponnect: Pending User Approvals"
    
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    admin_url = f"{frontend_url}/admin/approvals"
    
    body = f"""
    <h2>Pending User Approvals</h2>
    <p>Hello Sponnect Admin,</p>
    <p>There are new users waiting for your approval:</p>
    <ul>
        <li><strong>Pending Sponsors:</strong> {pending_sponsors}</li>
        <li><strong>Pending Influencers:</strong> {pending_influencers}</li>
    </ul>
    <p>Please <a href="{admin_url}">visit the admin panel</a> to review these applications.</p>
    <p>Best regards,<br>The Sponnect System</p>
    """
    
    # Send to all admins
    for admin in admins:
        send_email(admin.email, subject, body)
    
    return f"Pending approvals notification sent to {len(admins)} admins"


@celery.task()
def send_sponsor_stats_update():
    """
    Send detailed stats to sponsors every minute
    Includes: pending ad requests, negotiations, campaigns, etc.
    """
    sponsors = User.query.filter_by(role='sponsor', is_active=True, sponsor_approved=True).all()
    
    for sponsor in sponsors:
        # Get campaign stats
        active_campaigns = Campaign.query.filter(
            Campaign.sponsor_id == sponsor.id,
            Campaign.end_date >= datetime.utcnow()
        ).count()
        
        total_campaigns = Campaign.query.filter_by(sponsor_id=sponsor.id).count()
        
        # Get ad request stats
        pending_requests = AdRequest.query.join(Campaign).filter(
            Campaign.sponsor_id == sponsor.id,
            AdRequest.status == 'Pending'
        ).count()
        
        # Get negotiation stats
        active_negotiations = AdRequest.query.join(Campaign).filter(
            Campaign.sponsor_id == sponsor.id,
            AdRequest.status == 'Negotiating'
        ).count()
        
        # Get accepted partnerships
        accepted_partnerships = AdRequest.query.join(Campaign).filter(
            Campaign.sponsor_id == sponsor.id,
            AdRequest.status == 'Accepted'
        ).count()
        
        # Get progress updates
        pending_progress_updates = ProgressUpdate.query.join(AdRequest).join(Campaign).filter(
            Campaign.sponsor_id == sponsor.id,
            ProgressUpdate.status == 'Pending'
        ).count()
        
        # Generate stats summary email
        subject = f"Sponnect Sponsor Status Update - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
        
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                h1, h2, h3 {{ color: #4a6ee0; }}
                .stats-container {{ border: 1px solid #ddd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .stat-item {{ margin-bottom: 10px; }}
                .highlight {{ background-color: #fff3cd; padding: 5px; border-left: 4px solid #ffc107; }}
                .action-needed {{ background-color: #f8d7da; padding: 5px; border-left: 4px solid #dc3545; }}
            </style>
        </head>
        <body>
            <h1>Sponnect Sponsor Dashboard Update</h1>
            <p>Hello {sponsor.username},</p>
            <p>Here's your current status on Sponnect:</p>
            
            <div class="stats-container">
                <h2>Campaign Summary</h2>
                <div class="stat-item">Active Campaigns: <strong>{active_campaigns}</strong></div>
                <div class="stat-item">Total Campaigns: <strong>{total_campaigns}</strong></div>
            </div>
            
            <div class="stats-container">
                <h2>Partnership Status</h2>
                <div class="stat-item {'' if pending_requests == 0 else 'action-needed'}">
                    Pending Ad Requests: <strong>{pending_requests}</strong>
                </div>
                <div class="stat-item {'' if active_negotiations == 0 else 'highlight'}">
                    Active Negotiations: <strong>{active_negotiations}</strong>
                </div>
                <div class="stat-item">
                    Accepted Partnerships: <strong>{accepted_partnerships}</strong>
                </div>
            </div>
            
            <div class="stats-container">
                <h2>Content Progress</h2>
                <div class="stat-item {'' if pending_progress_updates == 0 else 'action-needed'}">
                    Pending Progress Reviews: <strong>{pending_progress_updates}</strong>
                </div>
            </div>
            
            <p>Visit your <a href="{os.environ.get('FRONTEND_URL', 'http://localhost:5173')}/sponsor/dashboard">sponsor dashboard</a> to take action on these items.</p>
            <p>Best regards,<br>The Sponnect Team</p>
        </body>
        </html>
        """
        
        # Send the email
        send_email(sponsor.email, subject, body)
    
    return f"Sponsor stats update sent to {len(sponsors)} sponsors"


@celery.task()
def send_influencer_stats_update():
    """
    Send detailed stats to influencers every minute
    Includes: pending ad requests, negotiations, progress tracking, etc.
    """
    influencers = User.query.filter_by(role='influencer', is_active=True, influencer_approved=True).all()
    
    for influencer in influencers:
        # Get ad request stats
        pending_requests = AdRequest.query.filter(
            AdRequest.influencer_id == influencer.id,
            AdRequest.status == 'Pending'
        ).count()
        
        # Get negotiation stats
        active_negotiations = AdRequest.query.filter(
            AdRequest.influencer_id == influencer.id,
            AdRequest.status == 'Negotiating'
        ).count()
        
        # Get accepted partnerships
        accepted_partnerships = AdRequest.query.filter(
            AdRequest.influencer_id == influencer.id,
            AdRequest.status == 'Accepted'
        ).count()
        
        # Get progress updates
        pending_content_submissions = ProgressUpdate.query.join(AdRequest).filter(
            AdRequest.influencer_id == influencer.id,
            ProgressUpdate.status == 'Pending'
        ).count()
        
        # Get matching campaigns
        matching_campaigns = Campaign.query.filter(
            Campaign.visibility == 'public',
            Campaign.end_date >= datetime.utcnow(),
            or_(
                Campaign.category == influencer.category,
                Campaign.category == 'any'
            )
        ).count()
        
        # Generate stats summary email
        subject = f"Sponnect Influencer Status Update - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
        
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                h1, h2, h3 {{ color: #4a6ee0; }}
                .stats-container {{ border: 1px solid #ddd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .stat-item {{ margin-bottom: 10px; }}
                .highlight {{ background-color: #fff3cd; padding: 5px; border-left: 4px solid #ffc107; }}
                .action-needed {{ background-color: #f8d7da; padding: 5px; border-left: 4px solid #dc3545; }}
                .opportunity {{ background-color: #d4edda; padding: 5px; border-left: 4px solid #28a745; }}
            </style>
        </head>
        <body>
            <h1>Sponnect Influencer Dashboard Update</h1>
            <p>Hello {influencer.username},</p>
            <p>Here's your current status on Sponnect:</p>
            
            <div class="stats-container">
                <h2>Partnership Status</h2>
                <div class="stat-item {'' if pending_requests == 0 else 'action-needed'}">
                    Pending Ad Requests: <strong>{pending_requests}</strong>
                </div>
                <div class="stat-item {'' if active_negotiations == 0 else 'highlight'}">
                    Active Negotiations: <strong>{active_negotiations}</strong>
                </div>
                <div class="stat-item">
                    Accepted Partnerships: <strong>{accepted_partnerships}</strong>
                </div>
            </div>
            
            <div class="stats-container">
                <h2>Content Progress</h2>
                <div class="stat-item {'' if pending_content_submissions == 0 else 'action-needed'}">
                    Pending Content Submissions: <strong>{pending_content_submissions}</strong>
                </div>
            </div>
            
            <div class="stats-container">
                <h2>Opportunities</h2>
                <div class="stat-item opportunity">
                    Matching Campaigns Available: <strong>{matching_campaigns}</strong>
                </div>
            </div>
            
            <p>Visit your <a href="{os.environ.get('FRONTEND_URL', 'http://localhost:5173')}/influencer/dashboard">influencer dashboard</a> to take action on these items.</p>
            <p>Best regards,<br>The Sponnect Team</p>
        </body>
        </html>
        """
        
        # Send the email
        send_email(influencer.email, subject, body)
    
    return f"Influencer stats update sent to {len(influencers)} influencers"


@celery.task()
def send_admin_daily_report():
    """
    Send detailed platform stats to admins every minute
    Includes: overall user stats, campaigns, requests, payments, etc.
    """
    admins = User.query.filter_by(role='admin', is_active=True).all()
    
    # Get platform stats
    total_users = User.query.count()
    total_sponsors = User.query.filter_by(role='sponsor').count()
    total_influencers = User.query.filter_by(role='influencer').count()
    
    # Get approval stats
    pending_sponsor_approvals = User.query.filter(
        User.role == 'sponsor',
        User.sponsor_approved.is_(None)
    ).count()
    
    pending_influencer_approvals = User.query.filter(
        User.role == 'influencer',
        User.influencer_approved.is_(None)
    ).count()
    
    # Get campaign stats
    total_campaigns = Campaign.query.count()
    active_campaigns = Campaign.query.filter(
        Campaign.end_date >= datetime.utcnow()
    ).count()
    
    # Get ad request stats
    total_ad_requests = AdRequest.query.count()
    pending_ad_requests = AdRequest.query.filter_by(status='Pending').count()
    negotiating_ad_requests = AdRequest.query.filter_by(status='Negotiating').count()
    accepted_ad_requests = AdRequest.query.filter_by(status='Accepted').count()
    
    # Get payment stats
    total_payments = Payment.query.count()
    total_payment_amount = db.session.query(func.sum(Payment.amount)).scalar() or 0
    total_platform_fees = db.session.query(func.sum(Payment.platform_fee)).scalar() or 0
    
    for admin in admins:
        # Generate stats summary email
        subject = f"Sponnect Admin Daily Report - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
        
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                h1, h2, h3 {{ color: #4a6ee0; }}
                .stats-container {{ border: 1px solid #ddd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .stat-item {{ margin-bottom: 10px; }}
                .highlight {{ background-color: #fff3cd; padding: 5px; border-left: 4px solid #ffc107; }}
                .action-needed {{ background-color: #f8d7da; padding: 5px; border-left: 4px solid #dc3545; }}
                .stats-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
            </style>
        </head>
        <body>
            <h1>Sponnect Admin Daily Report</h1>
            <p>Hello {admin.username},</p>
            <p>Here's the current status of the Sponnect platform:</p>
            
            <div class="stats-container">
                <h2>User Statistics</h2>
                <div class="stats-grid">
                    <div class="stat-item">Total Users: <strong>{total_users}</strong></div>
                    <div class="stat-item">Total Sponsors: <strong>{total_sponsors}</strong></div>
                    <div class="stat-item">Total Influencers: <strong>{total_influencers}</strong></div>
                </div>
            </div>
            
            <div class="stats-container">
                <h2>Pending Approvals</h2>
                <div class="stats-grid">
                    <div class="stat-item {'' if pending_sponsor_approvals == 0 else 'action-needed'}">
                        Pending Sponsor Approvals: <strong>{pending_sponsor_approvals}</strong>
                    </div>
                    <div class="stat-item {'' if pending_influencer_approvals == 0 else 'action-needed'}">
                        Pending Influencer Approvals: <strong>{pending_influencer_approvals}</strong>
                    </div>
                </div>
            </div>
            
            <div class="stats-container">
                <h2>Campaign Statistics</h2>
                <div class="stats-grid">
                    <div class="stat-item">Total Campaigns: <strong>{total_campaigns}</strong></div>
                    <div class="stat-item">Active Campaigns: <strong>{active_campaigns}</strong></div>
                </div>
            </div>
            
            <div class="stats-container">
                <h2>Ad Request Statistics</h2>
                <div class="stats-grid">
                    <div class="stat-item">Total Ad Requests: <strong>{total_ad_requests}</strong></div>
                    <div class="stat-item {'' if pending_ad_requests == 0 else 'highlight'}">
                        Pending Ad Requests: <strong>{pending_ad_requests}</strong>
                    </div>
                    <div class="stat-item {'' if negotiating_ad_requests == 0 else 'highlight'}">
                        Negotiating Ad Requests: <strong>{negotiating_ad_requests}</strong>
                    </div>
                    <div class="stat-item">Accepted Ad Requests: <strong>{accepted_ad_requests}</strong></div>
                </div>
            </div>
            
            <div class="stats-container">
                <h2>Payment Statistics</h2>
                <div class="stats-grid">
                    <div class="stat-item">Total Payments: <strong>{total_payments}</strong></div>
                    <div class="stat-item">Total Payment Amount: <strong>₹{total_payment_amount:,.2f}</strong></div>
                    <div class="stat-item">Total Platform Fees: <strong>₹{total_platform_fees:,.2f}</strong></div>
                </div>
            </div>
            
            <p>Visit your <a href="{os.environ.get('FRONTEND_URL', 'http://localhost:5173')}/admin/dashboard">admin dashboard</a> to manage the platform.</p>
            <p>Best regards,<br>The Sponnect System</p>
        </body>
        </html>
        """
        
        # Send the email
        send_email(admin.email, subject, body)
    
    return f"Admin daily report sent to {len(admins)} admins" 