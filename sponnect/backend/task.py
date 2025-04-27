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

@celery.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    # Daily reminder for pending ad requests - run at 9 AM every day
    sender.add_periodic_task(
        crontab(hour=9, minute=0),
        send_pending_request_reminders.s(),
        name='send_pending_request_reminders'
    )
    
    # Weekly summary for sponsors - run every Monday at 7 AM
    sender.add_periodic_task(
        crontab(day_of_week=1, hour=7, minute=0),
        send_weekly_sponsor_summary.s(),
        name='send_weekly_sponsor_summary'
    )
    
    # Monthly analytics report for admins - run 1st day of month at 6 AM
    sender.add_periodic_task(
        crontab(day_of_month=1, hour=6, minute=0),
        send_monthly_admin_report.s(),
        name='send_monthly_admin_report'
    )
    
    # Check for stale ad requests daily at 1 AM
    sender.add_periodic_task(
        crontab(hour=1, minute=0),
        check_stale_ad_requests.s(),
        name='check_stale_ad_requests'
    )


@celery.task()
def send_pending_request_reminders():
    """Send reminders to influencers and sponsors about pending ad requests"""
    now = datetime.utcnow()
    three_days_ago = now - timedelta(days=3)
    seven_days_ago = now - timedelta(days=7)
    
    # Get pending ad requests that haven't been updated in 3-7 days (first reminder)
    first_reminder_requests = AdRequest.query.filter(
        AdRequest.status == 'pending',
        AdRequest.updated_at >= seven_days_ago,
        AdRequest.updated_at <= three_days_ago
    ).all()
    
    # Get pending ad requests that haven't been updated in more than 7 days (urgent reminder)
    urgent_reminder_requests = AdRequest.query.filter(
        AdRequest.status == 'pending',
        AdRequest.updated_at < seven_days_ago
    ).all()
    
    results = []
    
    # Process first reminders
    for ad_request in first_reminder_requests:
        # Get associated user data
        sponsor = User.query.get(ad_request.sponsor_id)
        influencer = User.query.get(ad_request.influencer_id)
        campaign = Campaign.query.get(ad_request.campaign_id)
        
        if not sponsor or not influencer or not campaign:
            continue
            
        # Send reminder to sponsor
        sponsor_html = render_template(
            'emails/pending_request_reminder.html',
            user_type='sponsor',
            user=sponsor,
            ad_request=ad_request,
            campaign=campaign,
            influencer=influencer,
            days_pending=3,
            urgent=False
        )
        
        send_email(
            subject=f"Reminder: Pending Ad Request for {campaign.name}",
            to=sponsor.email,
            body=sponsor_html
        )
        
        # Send reminder to influencer
        influencer_html = render_template(
            'emails/pending_request_reminder.html',
            user_type='influencer',
            user=influencer,
            ad_request=ad_request,
            campaign=campaign,
            sponsor=sponsor,
            days_pending=3,
            urgent=False
        )
        
        send_email(
            subject=f"Reminder: Pending Campaign Request from {sponsor.username}",
            to=influencer.email,
            body=influencer_html
        )
        
        results.append(f"First reminder sent for ad request {ad_request.id} to {sponsor.email} and {influencer.email}")
    
    # Process urgent reminders
    for ad_request in urgent_reminder_requests:
        # Get associated user data
        sponsor = User.query.get(ad_request.sponsor_id)
        influencer = User.query.get(ad_request.influencer_id)
        campaign = Campaign.query.get(ad_request.campaign_id)
        
        if not sponsor or not influencer or not campaign:
            continue
            
        # Send urgent reminder to sponsor
        sponsor_html = render_template(
            'emails/pending_request_reminder.html',
            user_type='sponsor',
            user=sponsor,
            ad_request=ad_request,
            campaign=campaign,
            influencer=influencer,
            days_pending=7,
            urgent=True
        )
        
        send_email(
            subject=f"URGENT: Action Required on Ad Request for {campaign.name}",
            to=sponsor.email,
            body=sponsor_html
        )
        
        # Send urgent reminder to influencer
        influencer_html = render_template(
            'emails/pending_request_reminder.html',
            user_type='influencer',
            user=influencer,
            ad_request=ad_request,
            campaign=campaign,
            sponsor=sponsor,
            days_pending=7,
            urgent=True
        )
        
        send_email(
            subject=f"URGENT: Action Required on Campaign Request from {sponsor.username}",
            to=influencer.email,
            body=influencer_html
        )
        
        results.append(f"Urgent reminder sent for ad request {ad_request.id} to {sponsor.email} and {influencer.email}")
    
    return "\n".join(results) if results else "No pending request reminders needed"


@celery.task()
def send_weekly_sponsor_summary():
    """Send weekly summary of campaign performance to sponsors"""
    sponsors = User.query.filter_by(role='sponsor', is_active=True).all()
    now = datetime.utcnow()
    one_week_ago = now - timedelta(days=7)
    
    results = []
    
    for sponsor in sponsors:
        # Get sponsor's campaigns
        campaigns = Campaign.query.filter_by(sponsor_id=sponsor.id).all()
        
        if not campaigns:
            continue
            
        # Get stats for each campaign
        campaign_stats = []
        total_ad_requests = 0
        new_ad_requests = 0
        accepted_requests = 0
        completed_updates = 0
        
        for campaign in campaigns:
            # All ad requests for this campaign
            all_requests = AdRequest.query.filter_by(campaign_id=campaign.id).count()
            
            # New ad requests this week
            new_requests = AdRequest.query.filter_by(campaign_id=campaign.id).filter(
                AdRequest.created_at >= one_week_ago
            ).count()
            
            # Accepted ad requests for this campaign
            accepted = AdRequest.query.filter_by(
                campaign_id=campaign.id,
                status='accepted'
            ).count()
            
            # Progress updates submitted this week
            updates = ProgressUpdate.query.join(AdRequest).filter(
                AdRequest.campaign_id == campaign.id,
                ProgressUpdate.created_at >= one_week_ago
            ).count()
            
            campaign_stats.append({
                'campaign': campaign,
                'all_requests': all_requests,
                'new_requests': new_requests,
                'accepted': accepted,
                'updates': updates
            })
            
            total_ad_requests += all_requests
            new_ad_requests += new_requests
            accepted_requests += accepted
            completed_updates += updates
        
        # Only send email if there's activity
        if total_ad_requests > 0 or new_ad_requests > 0 or accepted_requests > 0 or completed_updates > 0:
            html_content = render_template(
                'emails/weekly_sponsor_summary.html',
                sponsor=sponsor,
                campaign_stats=campaign_stats,
                total_ad_requests=total_ad_requests,
                new_ad_requests=new_ad_requests,
                accepted_requests=accepted_requests,
                completed_updates=completed_updates,
                date_range=f"{one_week_ago.strftime('%b %d, %Y')} - {now.strftime('%b %d, %Y')}"
            )
            
            send_email(
                subject=f"Sponnect Weekly Summary: {one_week_ago.strftime('%b %d')} - {now.strftime('%b %d')}",
                to=sponsor.email,
                body=html_content
            )
            
            results.append(f"Weekly summary sent to sponsor {sponsor.username} ({sponsor.email})")
    
    return "\n".join(results) if results else "No weekly summaries sent"


@celery.task()
def send_monthly_admin_report():
    """Generate and send monthly platform analytics to admin users"""
    admins = User.query.filter_by(role='admin', is_active=True).all()
    
    if not admins:
        return "No active admin users found"
    
    now = datetime.utcnow()
    first_day_of_month = datetime(now.year, now.month, 1)
    if now.month == 1:
        first_day_of_prev_month = datetime(now.year - 1, 12, 1)
    else:
        first_day_of_prev_month = datetime(now.year, now.month - 1, 1)
    
    # User growth stats
    total_users = User.query.count()
    new_users_this_month = User.query.filter(
        User.created_at >= first_day_of_month,
        User.created_at < now
    ).count()
    new_users_prev_month = User.query.filter(
        User.created_at >= first_day_of_prev_month,
        User.created_at < first_day_of_month
    ).count()
    
    # Role breakdown
    sponsors_count = User.query.filter_by(role='sponsor').count()
    influencers_count = User.query.filter_by(role='influencer').count()
    
    # Campaign stats
    total_campaigns = Campaign.query.count()
    new_campaigns_this_month = Campaign.query.filter(
        Campaign.created_at >= first_day_of_month,
        Campaign.created_at < now
    ).count()
    active_campaigns = Campaign.query.filter_by(visibility='public').count()
    
    # Ad request stats
    total_ad_requests = AdRequest.query.count()
    new_ad_requests_this_month = AdRequest.query.filter(
        AdRequest.created_at >= first_day_of_month,
        AdRequest.created_at < now
    ).count()
    
    ad_requests_by_status = {}
    for status in ['pending', 'negotiating', 'accepted', 'rejected', 'completed']:
        ad_requests_by_status[status] = AdRequest.query.filter_by(status=status).count()
    
    # Payment stats
    total_payments = db.session.query(func.sum(Payment.amount)).scalar() or 0
    total_platform_fees = db.session.query(func.sum(Payment.platform_fee)).scalar() or 0
    
    # Payments this month
    payments_this_month = db.session.query(func.sum(Payment.amount)).filter(
        Payment.created_at >= first_day_of_month,
        Payment.created_at < now
    ).scalar() or 0
    
    fees_this_month = db.session.query(func.sum(Payment.platform_fee)).filter(
        Payment.created_at >= first_day_of_month,
        Payment.created_at < now
    ).scalar() or 0
    
    # Compile statistics
    report_data = {
        'date_range': f"{first_day_of_month.strftime('%B %Y')}",
        'generated_at': now.strftime('%Y-%m-%d %H:%M:%S'),
        'user_stats': {
            'total_users': total_users,
            'new_users_this_month': new_users_this_month,
            'new_users_prev_month': new_users_prev_month,
            'user_growth_rate': ((new_users_this_month - new_users_prev_month) / max(new_users_prev_month, 1)) * 100,
            'sponsors_count': sponsors_count,
            'influencers_count': influencers_count
        },
        'campaign_stats': {
            'total_campaigns': total_campaigns,
            'new_campaigns_this_month': new_campaigns_this_month,
            'active_campaigns': active_campaigns
        },
        'ad_request_stats': {
            'total_ad_requests': total_ad_requests,
            'new_ad_requests_this_month': new_ad_requests_this_month,
            'by_status': ad_requests_by_status
        },
        'payment_stats': {
            'total_payments': total_payments,
            'total_platform_fees': total_platform_fees,
            'payments_this_month': payments_this_month,
            'fees_this_month': fees_this_month
        }
    }
    
    results = []
    
    # Send to each admin
    for admin in admins:
        html_content = render_template(
            'emails/monthly_admin_report.html',
            admin=admin,
            report=report_data
        )
        
        send_email(
            subject=f"Sponnect Monthly Analytics Report - {first_day_of_month.strftime('%B %Y')}",
            to=admin.email,
            body=html_content
        )
        
        results.append(f"Monthly admin report sent to {admin.email}")
    
    # Also save report to file
    reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    report_file = os.path.join(reports_dir, f"admin_report_{first_day_of_month.strftime('%Y_%m')}.json")
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2, default=str)
    
    results.append(f"Monthly report saved to {report_file}")
    
    return "\n".join(results)


@celery.task()
def check_stale_ad_requests():
    """Identify and notify about stale ad requests"""
    now = datetime.utcnow()
    fourteen_days_ago = now - timedelta(days=14)
    thirty_days_ago = now - timedelta(days=30)
    
    # Stale negotiating requests (no activity for 14+ days)
    stale_negotiating = AdRequest.query.filter(
        AdRequest.status == 'negotiating',
        AdRequest.updated_at <= fourteen_days_ago
    ).all()
    
    # Very stale requests (no activity for 30+ days)
    very_stale = AdRequest.query.filter(
        AdRequest.status.in_(['pending', 'negotiating']),
        AdRequest.updated_at <= thirty_days_ago
    ).all()
    
    results = []
    
    # Process stale negotiating requests
    for ad_request in stale_negotiating:
        sponsor = User.query.get(ad_request.sponsor_id)
        influencer = User.query.get(ad_request.influencer_id)
        campaign = Campaign.query.get(ad_request.campaign_id)
        
        if not sponsor or not influencer or not campaign:
            continue
        
        # Notify both parties
        html_content = render_template(
            'emails/stale_request_notification.html',
            ad_request=ad_request,
            campaign=campaign,
            sponsor=sponsor,
            influencer=influencer,
            days_inactive=14,
            very_stale=False
        )
        
        send_email(
            subject=f"Action Required: Inactive Negotiation for {campaign.name}",
            to=[sponsor.email, influencer.email],
            body=html_content
        )
        
        results.append(f"Stale negotiation reminder sent for ad request {ad_request.id}")
    
    # Process very stale requests
    for ad_request in very_stale:
        sponsor = User.query.get(ad_request.sponsor_id)
        influencer = User.query.get(ad_request.influencer_id)
        campaign = Campaign.query.get(ad_request.campaign_id)
        
        if not sponsor or not influencer or not campaign:
            continue
        
        # Notify both parties and admin
        html_content = render_template(
            'emails/stale_request_notification.html',
            ad_request=ad_request,
            campaign=campaign,
            sponsor=sponsor,
            influencer=influencer,
            days_inactive=30,
            very_stale=True
        )
        
        send_email(
            subject=f"URGENT: Very Inactive Request for {campaign.name}",
            to=[sponsor.email, influencer.email],
            body=html_content
        )
        
        # Also notify admin
        admin_emails = [user.email for user in User.query.filter_by(role='admin').all()]
        if admin_emails:
            send_email(
                subject=f"Admin Alert: Very Stale Ad Request (ID: {ad_request.id})",
                to=admin_emails,
                body=html_content
            )
        
        results.append(f"Very stale request notification sent for ad request {ad_request.id}")
    
    return "\n".join(results) if results else "No stale ad requests found"


@celery.task()
def export_user_data(admin_id):
    """Export user data to CSV for admin analysis"""
    admin = User.query.get(admin_id)
    if not admin or admin.role != 'admin':
        return {"success": False, "message": "Invalid admin user"}
    
    # Generate filename with timestamp
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f"user_export_{timestamp}.csv"
    
    # Ensure exports directory exists
    exports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'exports')
    os.makedirs(exports_dir, exist_ok=True)
    
    filepath = os.path.join(exports_dir, filename)
    
    try:
        # Query all non-admin users
        users = User.query.filter(User.role != 'admin').order_by(User.created_at).all()
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow([
                'ID', 'Username', 'Email', 'Role', 'Full Name', 'Created At',
                'Last Login', 'Is Active', 'Is Verified', 'Campaign Count',
                'Ad Request Count', 'Total Payments'
            ])
            
            # Write user data
            for user in users:
                # Count campaigns (for sponsors)
                campaign_count = 0
                if user.role == 'sponsor':
                    campaign_count = Campaign.query.filter_by(sponsor_id=user.id).count()
                
                # Count ad requests
                if user.role == 'sponsor':
                    ad_request_count = AdRequest.query.filter_by(sponsor_id=user.id).count()
                else:
                    ad_request_count = AdRequest.query.filter_by(influencer_id=user.id).count()
                
                # Get total payments
                total_payments = 0
                if user.role == 'sponsor':
                    payments = Payment.query.join(AdRequest).filter(AdRequest.sponsor_id == user.id).all()
                    total_payments = sum(payment.amount for payment in payments)
                
                # Write row
                writer.writerow([
                    user.id,
                    user.username,
                    user.email,
                    user.role,
                    getattr(user, 'full_name', 'N/A'),
                    user.created_at,
                    getattr(user, 'last_login', 'Never'),
                    'Yes' if getattr(user, 'is_active', False) else 'No',
                    'Yes' if getattr(user, 'is_verified', False) else 'No',
                    campaign_count,
                    ad_request_count,
                    total_payments
                ])
        
        # Send email to admin with the export attached
        html_content = render_template(
            'emails/user_export_notification.html',
            admin=admin,
            user_count=len(users),
            timestamp=timestamp
        )
        
        with open(filepath, 'rb') as f:
            file_data = f.read()
        
        attachments = [(filename, 'text/csv', file_data)]
        
        send_email(
            subject=f"Sponnect User Data Export - {timestamp}",
            to=admin.email,
            body=html_content,
            attachments=attachments
        )
        
        return {
            "success": True,
            "message": f"User data exported successfully. File: {filename}",
            "filename": filename,
            "filepath": filepath,
            "user_count": len(users)
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error exporting user data: {str(e)}"
        }


@celery.task()
def send_test_email(recipient):
    """Send a test email to verify email and Celery configuration"""
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
            .header { color: #4361ee; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #eee; }
            .content { line-height: 1.6; }
            .footer { margin-top: 30px; font-size: 12px; color: #777; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Sponnect Test Email</h2>
            </div>
            <div class="content">
                <p>Hello!</p>
                <p>This is a test email from Sponnect to verify that the Celery email task is working properly.</p>
                <p>If you're seeing this, it means:</p>
                <ul>
                    <li>Celery worker is running correctly</li>
                    <li>Tasks are being processed</li>
                    <li>Email system is configured properly</li>
                </ul>
                <p>Time sent: {{ time }}</p>
            </div>
            <div class="footer">
                <p>This is an automated message from Sponnect. Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    with flask_app.app_context():
        html_content = render_template_string(
            template,
            time=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        result = send_email(
            subject="Sponnect Celery Test Email",
            to=recipient,
            body=html_content
        )
    
    return f"Test email {'sent successfully' if result else 'failed to send'} to {recipient}" 