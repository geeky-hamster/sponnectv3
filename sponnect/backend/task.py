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
            # Get top campaigns by ad requests
            top_campaigns = sorted(campaign_stats, key=lambda x: x['all_requests'], reverse=True)[:3]
            top_campaigns = [cs['campaign'] for cs in top_campaigns]
            
            # Get recent ad requests
            recent_ad_requests = AdRequest.query.join(Campaign).filter(
                Campaign.sponsor_id == sponsor.id,
                AdRequest.created_at >= one_week_ago
            ).order_by(AdRequest.created_at.desc()).limit(5).all()
            
            # Generate recommendations based on campaign performance
            recommendations = []
            if not new_ad_requests and total_ad_requests > 0:
                recommendations.append("Consider updating your campaign descriptions to attract more influencers.")
            if accepted_requests > 0 and completed_updates == 0:
                recommendations.append("Follow up with influencers who have accepted but haven't submitted progress.")
                
            html_content = render_template(
                'emails/weekly_sponsor_summary.html',
                sponsor=sponsor,
                period_start=one_week_ago,
                period_end=now,
                active_campaigns=len(campaigns),
                new_requests=new_ad_requests,
                accepted_requests=accepted_requests,
                completed_collaborations=completed_updates,
                top_campaigns=top_campaigns,
                recent_ad_requests=recent_ad_requests,
                recommendations=recommendations,
                dashboard_url="https://sponnect.com/sponsor/dashboard",
                year=now.year
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
    active_sponsors = User.query.filter_by(role='sponsor', is_active=True).count()
    influencers_count = User.query.filter_by(role='influencer').count()
    active_influencers = User.query.filter_by(role='influencer', is_active=True).count()
    
    # Growth calculations
    user_growth = ((new_users_this_month - new_users_prev_month) / max(new_users_prev_month, 1)) * 100
    
    # Get previous month counts for growth calculations
    prev_month_sponsors = User.query.filter(
        User.role == 'sponsor',
        User.created_at < first_day_of_month
    ).count()
    prev_month_influencers = User.query.filter(
        User.role == 'influencer',
        User.created_at < first_day_of_month
    ).count()
    
    sponsor_growth = ((active_sponsors - prev_month_sponsors) / max(prev_month_sponsors, 1)) * 100
    influencer_growth = ((active_influencers - prev_month_influencers) / max(prev_month_influencers, 1)) * 100
    
    # Campaign stats
    total_campaigns = Campaign.query.count()
    new_campaigns_this_month = Campaign.query.filter(
        Campaign.created_at >= first_day_of_month,
        Campaign.created_at < now
    ).count()
    active_campaigns = Campaign.query.filter_by(visibility='public').count()
    
    # Get previous month campaign count
    prev_month_campaigns = Campaign.query.filter(
        Campaign.created_at < first_day_of_month
    ).count()
    campaign_growth = ((total_campaigns - prev_month_campaigns) / max(prev_month_campaigns, 1)) * 100
    
    # Campaign categories
    campaign_categories = []
    categories_data = db.session.query(
        Campaign.category, func.count(Campaign.id)
    ).group_by(Campaign.category).all()
    
    for category, count in categories_data:
        if not category:
            category = "Uncategorized"
        percentage = (count / max(total_campaigns, 1)) * 100
        campaign_categories.append({
            "name": category,
            "count": count,
            "percentage": round(percentage, 1)
        })
    
    # Ad request stats
    total_ad_requests = AdRequest.query.count()
    new_ad_requests_this_month = AdRequest.query.filter(
        AdRequest.created_at >= first_day_of_month,
        AdRequest.created_at < now
    ).count()
    
    # Get previous month ad request count
    prev_month_ad_requests = AdRequest.query.filter(
        AdRequest.created_at < first_day_of_month
    ).count()
    ad_request_growth = ((total_ad_requests - prev_month_ad_requests) / max(prev_month_ad_requests, 1)) * 100
    
    # Ad request statuses
    ad_request_statuses = []
    for status in ['pending', 'negotiating', 'accepted', 'rejected', 'completed']:
        count = AdRequest.query.filter_by(status=status).count()
        percentage = (count / max(total_ad_requests, 1)) * 100
        ad_request_statuses.append({
            "name": status.capitalize(),
            "count": count,
            "percentage": round(percentage, 1)
        })
    
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
    
    # Get previous month payment data
    prev_month_payments = db.session.query(func.sum(Payment.amount)).filter(
        Payment.created_at >= first_day_of_prev_month,
        Payment.created_at < first_day_of_month
    ).scalar() or 0
    
    payment_growth = ((payments_this_month - prev_month_payments) / max(prev_month_payments, 1)) * 100
    platform_fee_percentage = (total_platform_fees / max(total_payments, 1)) * 100
    
    # Payment types
    payment_types = [
        {
            "name": "Standard Campaigns", 
            "amount": total_payments * 0.7,  # Placeholder - replace with actual query
            "percentage": 70
        },
        {
            "name": "Premium Campaigns",
            "amount": total_payments * 0.3,  # Placeholder - replace with actual query
            "percentage": 30
        }
    ]
    
    # Prepare stats object for template
    stats = {
        'total_users': total_users,
        'new_users': new_users_this_month,
        'user_growth': round(user_growth, 1),
        'active_sponsors': active_sponsors,
        'sponsor_growth': round(sponsor_growth, 1),
        'active_influencers': active_influencers,
        'influencer_growth': round(influencer_growth, 1),
        'total_campaigns': total_campaigns,
        'new_campaigns': new_campaigns_this_month,
        'campaign_growth': round(campaign_growth, 1),
        'campaign_categories': campaign_categories,
        'total_ad_requests': total_ad_requests,
        'new_ad_requests': new_ad_requests_this_month,
        'ad_request_growth': round(ad_request_growth, 1),
        'ad_request_statuses': ad_request_statuses,
        'total_payments': total_payments,
        'platform_fees': total_platform_fees,
        'payment_growth': round(payment_growth, 1),
        'platform_fee_percentage': round(platform_fee_percentage, 1),
        'payment_types': payment_types
    }
    
    results = []
    
    # Send to each admin
    for admin in admins:
        html_content = render_template(
            'emails/monthly_admin_report.html',
            admin=admin,
            stats=stats,
            month_name=first_day_of_month.strftime('%B'),
            year=first_day_of_month.year,
            generation_date=now.strftime('%Y-%m-%d %H:%M:%S')
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
        json.dump(stats, f, indent=2, default=str)
    
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


@celery.task()
def send_minute_test_reminder():
    """
    Send practical reminder emails every minute to sponsors and influencers.
    Different content is sent to each user type based on their role.
    This serves as both a test for Celery Beat and a useful notification system.
    """
    from datetime import datetime
    current_time = datetime.utcnow()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Get active sponsors and influencers
    sponsors = User.query.filter_by(role='sponsor', is_active=True, is_flagged=False).all()
    influencers = User.query.filter_by(role='influencer', is_active=True, is_flagged=False).all()
    
    # Count recently created campaigns (in the last 24 hours)
    one_day_ago = current_time - timedelta(days=1)
    new_campaigns = Campaign.query.filter(
        Campaign.created_at >= one_day_ago,
        Campaign.visibility == 'public'
    ).count()
    
    results = []
    
    # Send to sponsors - focus on new influencers and pending requests
    for sponsor in sponsors:
        # Get pending ad requests for this sponsor
        pending_requests = AdRequest.query.filter_by(
            sponsor_id=sponsor.id,
            status='pending'
        ).count()
        
        # Get new influencers in the last week
        one_week_ago = current_time - timedelta(days=7)
        new_influencers = User.query.filter(
            User.role == 'influencer',
            User.is_active == True,
            User.created_at >= one_week_ago
        ).count()
        
        # Email content for sponsors
        sponsor_html = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 5px;">
                <h2 style="color: #4a6ee0;">Sponnect Activity Update</h2>
                <p>Hello {sponsor.username},</p>
                <p>Here's a quick update on your Sponnect activity:</p>
                <ul>
                    <li><strong>{pending_requests}</strong> pending ad requests require your attention</li>
                    <li><strong>{new_influencers}</strong> new influencers joined in the last week</li>
                    <li><strong>{new_campaigns}</strong> new campaigns were posted in the last 24 hours</li>
                </ul>
                <p>Don't miss out on potential collaborations!</p>
                <div style="margin-top: 20px; text-align: center;">
                    <a href="https://sponnect.com/sponsor/dashboard" 
                       style="background-color: #4a6ee0; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">
                       Visit Dashboard
                    </a>
                </div>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #666; font-size: 12px; text-align: center;">
                    This is a test notification from the Sponnect minute reminder service.
                    Current time: {formatted_time}
                </p>
            </div>
        </body>
        </html>
        """
        
        send_email(
            subject="Sponnect Activity Update",
            to=sponsor.email,
            body=sponsor_html
        )
        
        results.append(f"Sponsor update sent to {sponsor.email}")
    
    # Send to influencers - focus on new campaigns and application opportunities
    for influencer in influencers:
        # Get pending applications for this influencer
        pending_applications = AdRequest.query.filter_by(
            influencer_id=influencer.id,
            status='pending'
        ).count()
        
        # Get campaigns that match influencer's category
        matching_campaigns = Campaign.query.filter_by(
            visibility='public',
            category=influencer.category if hasattr(influencer, 'category') else None
        ).count()
        
        # Email content for influencers
        influencer_html = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 5px;">
                <h2 style="color: #4a6ee0;">Sponnect Opportunities Update</h2>
                <p>Hello {influencer.username},</p>
                <p>Here's a quick update on potential opportunities:</p>
                <ul>
                    <li><strong>{pending_applications}</strong> of your applications are pending</li>
                    <li><strong>{matching_campaigns}</strong> campaigns match your category</li>
                    <li><strong>{new_campaigns}</strong> new campaigns were posted in the last 24 hours</li>
                </ul>
                <p>Don't miss out on these collaboration opportunities!</p>
                <div style="margin-top: 20px; text-align: center;">
                    <a href="https://sponnect.com/influencer/campaigns/browse" 
                       style="background-color: #4a6ee0; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">
                       Browse Campaigns
                    </a>
                </div>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #666; font-size: 12px; text-align: center;">
                    This is a test notification from the Sponnect minute reminder service.
                    Current time: {formatted_time}
                </p>
            </div>
        </body>
        </html>
        """
        
        send_email(
            subject="Sponnect Opportunities Update",
            to=influencer.email,
            body=influencer_html
        )
        
        results.append(f"Influencer update sent to {influencer.email}")
    
    # Also send to admin emails for monitoring
    admin_emails = [user.email for user in User.query.filter_by(role='admin', is_active=True).all()]
    if admin_emails:
        admin_html = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 5px;">
                <h2 style="color: #4a6ee0;">Sponnect Minute Reminder Test</h2>
                <p>This is a test email from the Sponnect Celery Beat scheduler.</p>
                <p>Notification summary:</p>
                <ul>
                    <li>Sent updates to {len(sponsors)} sponsors</li>
                    <li>Sent updates to {len(influencers)} influencers</li>
                </ul>
                <p>Current time: <strong>{formatted_time}</strong></p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #666; font-size: 12px;">
                    This email was automatically generated to test the Celery Beat scheduler with a 1-minute interval.
                </p>
            </div>
        </body>
        </html>
        """
        
        for admin_email in admin_emails:
            send_email(
                subject=f"Sponnect Minute Reminder Test - {formatted_time}",
                to=admin_email,
                body=admin_html
            )
        
        results.append(f"Admin summary sent to {', '.join(admin_emails)}")
    
    return f"Activity updates sent at {formatted_time} to {len(sponsors)} sponsors and {len(influencers)} influencers"


@celery.task()
def send_registration_pending_notification(user_id):
    """
    Send a notification to a newly registered user who is waiting for admin approval.
    
    Args:
        user_id (int): ID of the newly registered user
    """
    user = User.query.get(user_id)
    if not user:
        return f"User with ID {user_id} not found"
    
    # Skip if user is already approved or active
    if hasattr(user, 'is_active') and user.is_active:
        return f"User {user.username} is already active"
    
    # Determine if sponsor or influencer for custom content
    approval_type = ""
    if user.role == 'sponsor':
        approval_type = "sponsor"
        approval_status = user.sponsor_approved
    elif user.role == 'influencer':
        approval_type = "influencer"
        approval_status = user.influencer_approved
    else:
        # Skip for admin users or other roles
        return f"User {user.username} has role {user.role} which doesn't require approval"
    
    # Skip if already approved
    if approval_status is True:
        return f"User {user.username} is already approved"
    
    # Generate HTML content for the notification email
    html_content = f"""
    <html>
    <body>
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 5px;">
            <h2 style="color: #4a6ee0;">Welcome to Sponnect!</h2>
            <p>Hello {user.username},</p>
            <p>Thank you for registering as a {approval_type} on Sponnect. Your account has been created and is currently awaiting admin approval.</p>
            <h3>What happens next?</h3>
            <ol>
                <li>Our admin team will review your details</li>
                <li>Once approved, you'll receive a confirmation email</li>
                <li>You can then log in and start using all Sponnect features</li>
            </ol>
            <p>This process typically takes 1-2 business days. You'll be notified as soon as your account is approved.</p>
            <div style="margin: 30px 0; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #4a6ee0;">
                <p style="margin: 0;"><strong>Account Status:</strong> Pending Approval</p>
            </div>
            <p>If you have any questions or need assistance, please contact our support team at support@sponnect.com.</p>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #666; font-size: 12px; text-align: center;">
                This is an automated message from Sponnect. Please do not reply to this email.
            </p>
        </div>
    </body>
    </html>
    """
    
    # Send the email
    result = send_email(
        subject="Welcome to Sponnect - Account Pending Approval",
        to=user.email,
        body=html_content
    )
    
    return f"Registration pending notification {'sent successfully' if result else 'failed to send'} to {user.email}"


@celery.task()
def send_account_approval_notification(user_id):
    """
    Send a notification to a user when their account has been approved by an admin.
    
    Args:
        user_id (int): ID of the approved user
    """
    user = User.query.get(user_id)
    if not user:
        return f"User with ID {user_id} not found"
    
    # Determine if sponsor or influencer for custom content
    if user.role == 'sponsor':
        role_title = "Sponsor"
        dashboard_url = "https://sponnect.com/sponsor/dashboard"
        features = [
            "Create advertising campaigns",
            "Search for suitable influencers",
            "Send ad requests to influencers",
            "Manage your marketing budget",
            "Track campaign performance"
        ]
    elif user.role == 'influencer':
        role_title = "Influencer"
        dashboard_url = "https://sponnect.com/influencer/dashboard"
        features = [
            "Browse available campaigns",
            "Apply to campaigns that match your niche",
            "Negotiate with sponsors",
            "Track your earnings",
            "Build your sponsorship portfolio"
        ]
    else:
        # Skip for admin users or other roles
        return f"User {user.username} has role {user.role} which doesn't need approval notification"
    
    # Generate HTML content for the notification email
    html_content = f"""
    <html>
    <body>
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 5px;">
            <h2 style="color: #4a6ee0;">Your Sponnect Account is Approved!</h2>
            <p>Hello {user.username},</p>
            <p>Great news! Your {role_title.lower()} account has been approved and is now fully active. You can start using all Sponnect features immediately.</p>
            
            <div style="margin: 20px 0; padding: 15px; background-color: #f0f7ff; border-radius: 5px;">
                <p style="margin: 0; text-align: center; font-weight: bold; color: #4a6ee0;">
                    <span style="font-size: 16px;">✓</span> ACCOUNT ACTIVE
                </p>
            </div>
            
            <h3>What you can do now:</h3>
            <ul>
                {' '.join(f'<li>{feature}</li>' for feature in features)}
            </ul>
            
            <div style="margin-top: 30px; text-align: center;">
                <a href="{dashboard_url}" 
                   style="background-color: #4a6ee0; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; font-weight: bold;">
                   GO TO DASHBOARD
                </a>
            </div>
            
            <p style="margin-top: 30px;">If you have any questions or need assistance, our support team is always here to help at support@sponnect.com.</p>
            
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #666; font-size: 12px; text-align: center;">
                This is an automated message from Sponnect. Please do not reply to this email.
            </p>
        </div>
    </body>
    </html>
    """
    
    # Send the email
    result = send_email(
        subject="Your Sponnect Account Has Been Approved!",
        to=user.email,
        body=html_content
    )
    
    return f"Account approval notification {'sent successfully' if result else 'failed to send'} to {user.email}"


@celery.task()
def send_login_stats(user_id):
    """
    Send stats about pending requests and other activities when a user logs in
    
    Args:
        user_id (int): ID of the user who just logged in
    """
    user = User.query.get(user_id)
    if not user:
        return f"User with ID {user_id} not found"
    
    current_time = datetime.utcnow()
    
    # Different stats based on user role
    if user.role == 'sponsor':
        # Get pending ad requests
        pending_requests = AdRequest.query.filter_by(
            sponsor_id=user.id,
            status='pending'
        ).count()
        
        # Get negotiating ad requests
        negotiating_requests = AdRequest.query.filter_by(
            sponsor_id=user.id,
            status='negotiating'
        ).count()
        
        # Get accepted requests without progress updates recently
        accepted_requests = AdRequest.query.filter_by(
            sponsor_id=user.id,
            status='accepted'
        ).count()
        
        # Get campaign count
        campaigns = Campaign.query.filter_by(sponsor_id=user.id).count()
        
        # Get recent applications (last 3 days)
        three_days_ago = current_time - timedelta(days=3)
        recent_applications = AdRequest.query.filter(
            AdRequest.sponsor_id == user.id,
            AdRequest.created_at >= three_days_ago
        ).count()
        
        # Generate HTML content for sponsor
        html_content = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 5px;">
                <h2 style="color: #4a6ee0;">Welcome Back to Sponnect!</h2>
                <p>Hello {user.username},</p>
                <p>Here's a summary of your current Sponnect activity:</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="background-color: #f8f9fa;">
                        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Activity</th>
                        <th style="padding: 10px; text-align: center; border: 1px solid #ddd;">Count</th>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">Active Campaigns</td>
                        <td style="padding: 10px; text-align: center; border: 1px solid #ddd;">{campaigns}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">Pending Ad Requests</td>
                        <td style="padding: 10px; text-align: center; border: 1px solid #ddd;">{pending_requests}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">Ongoing Negotiations</td>
                        <td style="padding: 10px; text-align: center; border: 1px solid #ddd;">{negotiating_requests}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">Accepted Partnerships</td>
                        <td style="padding: 10px; text-align: center; border: 1px solid #ddd;">{accepted_requests}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">New Applications (Last 3 Days)</td>
                        <td style="padding: 10px; text-align: center; border: 1px solid #ddd;">{recent_applications}</td>
                    </tr>
                </table>
                
                <div style="margin-top: 20px; text-align: center;">
                    <a href="https://sponnect.com/sponsor/dashboard" 
                       style="background-color: #4a6ee0; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">
                       Go to Dashboard
                    </a>
                </div>
                
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #666; font-size: 12px; text-align: center;">
                    This is an automated login statistics email from Sponnect.
                </p>
            </div>
        </body>
        </html>
        """
        
    elif user.role == 'influencer':
        # Get pending applications
        pending_applications = AdRequest.query.filter_by(
            influencer_id=user.id,
            status='pending'
        ).count()
        
        # Get negotiations in progress
        negotiations = AdRequest.query.filter_by(
            influencer_id=user.id,
            status='negotiating'
        ).count()
        
        # Get accepted partnerships
        accepted_partnerships = AdRequest.query.filter_by(
            influencer_id=user.id,
            status='accepted'
        ).count()
        
        # Get available campaigns that match the influencer's category
        matching_campaigns = Campaign.query.filter_by(
            visibility='public',
            category=user.category if hasattr(user, 'category') else None
        ).count()
        
        # Get new campaigns in the last week
        one_week_ago = current_time - timedelta(days=7)
        new_campaigns = Campaign.query.filter(
            Campaign.created_at >= one_week_ago,
            Campaign.visibility == 'public'
        ).count()
        
        # Generate HTML content for influencer
        html_content = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 5px;">
                <h2 style="color: #4a6ee0;">Welcome Back to Sponnect!</h2>
                <p>Hello {user.username},</p>
                <p>Here's a summary of your current Sponnect opportunities and activity:</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="background-color: #f8f9fa;">
                        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Activity</th>
                        <th style="padding: 10px; text-align: center; border: 1px solid #ddd;">Count</th>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">Pending Applications</td>
                        <td style="padding: 10px; text-align: center; border: 1px solid #ddd;">{pending_applications}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">Ongoing Negotiations</td>
                        <td style="padding: 10px; text-align: center; border: 1px solid #ddd;">{negotiations}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">Active Partnerships</td>
                        <td style="padding: 10px; text-align: center; border: 1px solid #ddd;">{accepted_partnerships}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">Campaigns Matching Your Category</td>
                        <td style="padding: 10px; text-align: center; border: 1px solid #ddd;">{matching_campaigns}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">New Campaigns (Last 7 Days)</td>
                        <td style="padding: 10px; text-align: center; border: 1px solid #ddd;">{new_campaigns}</td>
                    </tr>
                </table>
                
                <div style="margin-top: 20px; text-align: center;">
                    <a href="https://sponnect.com/influencer/dashboard" 
                       style="background-color: #4a6ee0; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">
                       Go to Dashboard
                    </a>
                </div>
                
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #666; font-size: 12px; text-align: center;">
                    This is an automated login statistics email from Sponnect.
                </p>
            </div>
        </body>
        </html>
        """
    else:
        # Admin or other role - no stats needed
        return f"No login stats needed for user {user.username} with role {user.role}"
    
    # Send the email
    result = send_email(
        subject="Your Sponnect Activity Summary",
        to=user.email,
        body=html_content
    )
    
    return f"Login stats {'sent successfully' if result else 'failed to send'} to {user.email}"


@celery.task()
def notify_admin_pending_approvals():
    """Notify admins about pending user approvals that need attention"""
    # Get all admin users
    admins = User.query.filter_by(role='admin', is_active=True).all()
    if not admins:
        return "No active admin users found"
    
    # Count pending sponsors
    pending_sponsors = User.query.filter_by(
        role='sponsor',
        sponsor_approved=None
    ).all()
    
    # Count pending influencers
    pending_influencers = User.query.filter_by(
        role='influencer',
        influencer_approved=None
    ).all()
    
    # If no pending approvals, no need to send email
    if not pending_sponsors and not pending_influencers:
        return "No pending approvals to notify admins about"
    
    # Generate HTML content
    html_content = f"""
    <html>
    <body>
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 5px;">
            <h2 style="color: #4a6ee0;">Pending Approvals Require Attention</h2>
            <p>Hello Admin,</p>
            <p>There are user registrations waiting for your approval:</p>
            
            <div style="margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-radius: 5px;">
                <p><strong>Pending Sponsors:</strong> {len(pending_sponsors)}</p>
                <p><strong>Pending Influencers:</strong> {len(pending_influencers)}</p>
            </div>
            
            {generate_pending_users_table(pending_sponsors, 'Sponsors') if pending_sponsors else ''}
            {generate_pending_users_table(pending_influencers, 'Influencers') if pending_influencers else ''}
            
            <div style="margin-top: 30px; text-align: center;">
                <a href="https://sponnect.com/admin/pending" 
                style="background-color: #4a6ee0; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">
                Review Pending Users
                </a>
            </div>
            
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #666; font-size: 12px; text-align: center;">
                This is an automated notification from the Sponnect system.
            </p>
        </div>
    </body>
    </html>
    """
    
    results = []
    # Send to each admin
    for admin in admins:
        result = send_email(
            subject=f"Sponnect: {len(pending_sponsors) + len(pending_influencers)} Users Awaiting Approval",
            to=admin.email,
            body=html_content
        )
        results.append(f"Admin notification {'sent' if result else 'failed'} to {admin.email}")
    
    return "\n".join(results)


def generate_pending_users_table(users, user_type):
    """Helper function to generate HTML table of pending users"""
    if not users:
        return ""
    
    rows = ""
    for user in users:
        created_date = user.created_at.strftime("%Y-%m-%d") if user.created_at else "Unknown"
        if user_type == "Sponsors":
            detail = user.company_name if hasattr(user, 'company_name') else ""
            extra = user.industry if hasattr(user, 'industry') else ""
        else:  # Influencers
            detail = user.influencer_name if hasattr(user, 'influencer_name') else ""
            extra = f"{user.category} - {user.niche}" if hasattr(user, 'category') and hasattr(user, 'niche') else ""
        
        rows += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">{user.username}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{user.email}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{detail}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{extra}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{created_date}</td>
        </tr>
        """
    
    return f"""
    <h3 style="margin-top: 20px;">Pending {user_type}</h3>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
        <tr style="background-color: #f0f7ff;">
            <th style="padding: 8px; border: 1px solid #ddd;">Username</th>
            <th style="padding: 8px; border: 1px solid #ddd;">Email</th>
            <th style="padding: 8px; border: 1px solid #ddd;">Name</th>
            <th style="padding: 8px; border: 1px solid #ddd;">Details</th>
            <th style="padding: 8px; border: 1px solid #ddd;">Registered</th>
        </tr>
        {rows}
    </table>
    """ 