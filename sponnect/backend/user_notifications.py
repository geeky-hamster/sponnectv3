"""
User notification tasks for the Sponnect application.
This module contains Celery tasks for sending notifications to users.
"""

from workers import celery
from models import db, User, Campaign, AdRequest, NegotiationHistory, ProgressUpdate, Payment
from mailer import send_email, send_template_email
from datetime import datetime, timedelta
from flask import render_template
import os
from sqlalchemy import func, and_, or_


@celery.task()
def send_minute_activity_update():
    """
    Send activity updates to relevant users (admins, sponsors, influencers)
    This is meant to be run by a scheduled task (e.g., Celery)
    """
    try:
        # Common stats
        total_users = User.query.count()
        total_campaigns = Campaign.query.count()
        total_ad_requests = AdRequest.query.count()
        
        # Recent activity (past day)
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        new_users = User.query.filter(User.created_at >= one_day_ago).count()
        new_campaigns = Campaign.query.filter(Campaign.created_at >= one_day_ago).count()
        new_ad_requests = AdRequest.query.filter(AdRequest.created_at >= one_day_ago).count()
        
        print(f"Activity Update - Stats: Users={total_users}, Campaigns={total_campaigns}, New Users={new_users}")
        
        # SEND TO ADMINS - Admins get platform-wide updates
        send_admin_activity_updates(total_users, total_campaigns, total_ad_requests,
                                   new_users, new_campaigns, new_ad_requests)
        
        # SEND TO SPONSORS - Only relevant sponsor-specific information
        send_sponsor_activity_updates(new_campaigns)
        
        # SEND TO INFLUENCERS - Only relevant influencer-specific information
        send_influencer_activity_updates(new_campaigns)
        
        return "Activity updates sent successfully"
        
    except Exception as e:
        error_message = f"Error in send_minute_activity_update: {str(e)}"
        print(error_message)
        return error_message


def send_admin_activity_updates(total_users, total_campaigns, total_ad_requests, 
                              new_users, new_campaigns, new_ad_requests):
    """Helper function to send activity updates to admins"""
    admins = User.query.filter_by(role='admin').all()
    print(f"Activity Update - Found {len(admins)} admins to notify")
    
    admin_sent_count = 0
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    
    for admin in admins:
        try:
            subject = "Sponnect Platform Daily Activity Update"
            
            # Render the template with admin-specific context
            body = render_template('emails/activity_update.html',
                user=admin,
                role='admin',
                total_users=total_users,
                total_campaigns=total_campaigns,
                total_ad_requests=total_ad_requests,
                new_users=new_users,
                new_campaigns=new_campaigns,
                new_ad_requests=new_ad_requests,
                frontend_url=frontend_url
            )
            
            if admin.email:
                send_email(subject, admin.email, body)
                admin_sent_count += 1
                print(f"Sent activity update to admin: {admin.email}")
            else:
                print(f"Admin {admin.username} has no email address")
        except Exception as e:
            print(f"Error sending to admin {admin.username}: {str(e)}")
    
    return admin_sent_count


def send_sponsor_activity_updates(new_campaigns):
    """Helper function to send activity updates to sponsors"""
    sponsors = User.query.filter_by(role='sponsor', is_active=True).all()
    print(f"Activity Update - Found {len(sponsors)} active sponsors to notify")
    
    sponsor_sent_count = 0
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    
    for sponsor in sponsors:
        try:
            # Get sponsor-specific stats
            sponsor_campaigns = Campaign.query.filter_by(sponsor_id=sponsor.id).count()
            pending_requests = AdRequest.query.join(Campaign).filter(
                Campaign.sponsor_id == sponsor.id,
                AdRequest.status == 'Pending'
            ).count()
            
            # Only send if they have pending requests or campaigns
            if pending_requests > 0 or sponsor_campaigns > 0:
                subject = "Sponnect: Campaign Activity Update"
                
                # Render the template with sponsor-specific context
                body = render_template('emails/sponsor_stats.html',
                    sponsor=sponsor,
                    active_campaigns=Campaign.query.filter(
                        Campaign.sponsor_id == sponsor.id,
                        Campaign.end_date >= datetime.utcnow()
                    ).count(),
                    total_campaigns=sponsor_campaigns,
                    pending_requests=pending_requests,
                    active_negotiations=AdRequest.query.join(Campaign).filter(
                        Campaign.sponsor_id == sponsor.id,
                        AdRequest.status == 'Negotiating'
                    ).count(),
                    accepted_partnerships=AdRequest.query.join(Campaign).filter(
                        Campaign.sponsor_id == sponsor.id,
                        AdRequest.status == 'Accepted'
                    ).count(),
                    pending_progress_updates=ProgressUpdate.query.join(AdRequest).join(Campaign).filter(
                        Campaign.sponsor_id == sponsor.id,
                        ProgressUpdate.status == 'Pending'
                    ).count(),
                    recent_requests=get_recent_requests_for_sponsor(sponsor.id),
                    frontend_url=frontend_url
                )
                
                if sponsor.email:
                    send_email(subject, sponsor.email, body)
                    sponsor_sent_count += 1
                    print(f"Sent activity update to sponsor: {sponsor.email}")
                else:
                    print(f"Sponsor {sponsor.username} has no email address")
        except Exception as e:
            print(f"Error sending to sponsor {sponsor.username}: {str(e)}")
    
    return sponsor_sent_count


def send_influencer_activity_updates(new_campaigns):
    """Helper function to send activity updates to influencers"""
    influencers = User.query.filter_by(role='influencer', is_active=True).all()
    print(f"Activity Update - Found {len(influencers)} active influencers to notify")
    
    influencer_sent_count = 0
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    
    for influencer in influencers:
        try:
            # Get matching campaigns for this influencer
            matching_campaigns = Campaign.query.filter(
                Campaign.visibility == 'public',
                Campaign.end_date >= datetime.utcnow(),
                (Campaign.category == influencer.category) | (Campaign.category == 'any')
            ).count()
            
            # Get pending applications for this influencer
            pending_apps = AdRequest.query.filter_by(
                influencer_id=influencer.id,
                status='Pending'
            ).count()
            
            # Only send if they have matching campaigns or pending applications
            if matching_campaigns > 0 or pending_apps > 0:
                subject = "Sponnect: Campaign Opportunities Update"
                
                # Get recent matching campaigns for this influencer
                recent_matching_campaigns = Campaign.query.filter(
                    Campaign.visibility == 'public',
                    Campaign.end_date >= datetime.utcnow(),
                    (Campaign.category == influencer.category) | (Campaign.category == 'any')
                ).order_by(Campaign.created_at.desc()).limit(3).all()
                
                # Render the template with influencer-specific context
                body = render_template('emails/influencer_stats.html',
                    influencer=influencer,
                    pending_applications=pending_apps,
                    active_negotiations=AdRequest.query.filter_by(
                        influencer_id=influencer.id,
                        status='Negotiating'
                    ).count(),
                    active_partnerships=AdRequest.query.filter_by(
                        influencer_id=influencer.id,
                        status='Accepted'
                    ).count(),
                    pending_content_reviews=ProgressUpdate.query.join(AdRequest).filter(
                        AdRequest.influencer_id == influencer.id,
                        ProgressUpdate.status == 'Pending'
                    ).count(),
                    matching_campaigns=matching_campaigns,
                    recent_matching_campaigns=recent_matching_campaigns,
                    frontend_url=frontend_url
                )
                
                if influencer.email:
                    send_email(subject, influencer.email, body)
                    influencer_sent_count += 1
                    print(f"Sent activity update to influencer: {influencer.email}")
                else:
                    print(f"Influencer {influencer.username} has no email address")
        except Exception as e:
            print(f"Error sending to influencer {influencer.username}: {str(e)}")
    
    return influencer_sent_count


def get_recent_requests_for_sponsor(sponsor_id):
    """Helper function to get formatted recent requests for a sponsor"""
    recent_requests = AdRequest.query.join(Campaign).filter(
        Campaign.sponsor_id == sponsor_id
    ).order_by(AdRequest.created_at.desc()).limit(5).all()
    
    # Format recent requests data
    recent_requests_data = []
    for request in recent_requests:
        influencer = User.query.get(request.influencer_id)
        campaign = Campaign.query.get(request.campaign_id)
        if influencer and campaign:
            recent_requests_data.append({
                'influencer_username': influencer.username,
                'campaign_name': campaign.name,
                'created_at': request.created_at.strftime('%Y-%m-%d')
            })
    
    return recent_requests_data


@celery.task()
def send_registration_pending_notification(user_id):
    """
    Send notification to user when they register and are waiting for admin approval
    """
    user = User.query.get(user_id)
    if not user:
        return "User not found"
    
    subject = "Your Sponnect Registration is Pending Approval"
    
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    
    # Render the template with context
    body = render_template('emails/registration_pending.html',
        user=user,
        frontend_url=frontend_url
    )
    
    # Send the email
    send_email(subject, user.email, body)
    
    # Also notify admins
    notify_admin_pending_approvals()
    
    return f"Registration pending notification sent to {user.email}"


@celery.task()
def send_account_approval_notification(user_id):
    """
    Send notification to user when their account is approved
    """
    user = User.query.get(user_id)
    if not user:
        return "User not found"
    
    subject = "Your Sponnect Account Has Been Approved"
    
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    
    # Render the template with context
    body = render_template('emails/account_approval.html',
        user=user,
        frontend_url=frontend_url
    )
    
    # Send the email
    send_email(subject, user.email, body)
    
    return f"Account approval notification sent to {user.email}"


@celery.task()
def send_login_stats(user_id):
    """
    Send login stats notification to user
    Called when a user logs in to display pending items and account status
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return "User not found"
        
        subject = f"Welcome back to Sponnect, {user.username}!"
        
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
        context = {
            'user': user,
            'frontend_url': frontend_url
        }
        
        if user.role == 'admin':
            # Get stats for admin
            pending_users = User.query.filter(
                ((User.role == 'sponsor') & (User.sponsor_approved.is_(None))) |
                ((User.role == 'influencer') & (User.influencer_approved.is_(None)))
            ).count()
            
            total_users = User.query.count()
            total_campaigns = Campaign.query.count()
            total_ad_requests = AdRequest.query.count()
            
            context.update({
                'pending_users': pending_users,
                'total_users': total_users,
                'total_campaigns': total_campaigns,
                'total_ad_requests': total_ad_requests
            })
        
        elif user.role == 'sponsor':
            # Get stats for sponsor
            total_campaigns = Campaign.query.filter_by(sponsor_id=user.id).count()
            pending_requests = AdRequest.query.join(Campaign).filter(
                Campaign.sponsor_id == user.id,
                AdRequest.status == 'pending'
            ).count()
            approved_requests = AdRequest.query.join(Campaign).filter(
                Campaign.sponsor_id == user.id,
                AdRequest.status == 'approved'
            ).count()
            
            context.update({
                'total_campaigns': total_campaigns,
                'pending_requests': pending_requests,
                'approved_requests': approved_requests
            })
        
        elif user.role == 'influencer':
            # Get stats for influencer
            pending_requests = AdRequest.query.filter_by(
                influencer_id=user.id,
                status='pending'
            ).count()
            approved_requests = AdRequest.query.filter_by(
                influencer_id=user.id,
                status='approved'
            ).count()
            
            # Get recently added campaigns that match influencer's niche/category
            matching_campaigns = Campaign.query.filter(
                Campaign.visibility == 'public',
                (Campaign.category == user.category) | (Campaign.category == 'any')
            ).order_by(Campaign.created_at.desc()).limit(3).all()
            
            context.update({
                'pending_requests': pending_requests,
                'approved_requests': approved_requests,
                'matching_campaigns': matching_campaigns if matching_campaigns else []
            })
        
        # Render the template with context
        body = render_template('emails/login_stats.html', **context)
        
        # Send the email
        send_email(subject, user.email, body)
        print(f"Login stats sent to {user.email}")
        return f"Login stats sent to {user.email}"
    except Exception as e:
        error_message = f"Error in send_login_stats: {str(e)}"
        print(error_message)
        return error_message


@celery.task()
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
    
    # Get most recent 5 pending users
    pending_details = User.query.filter(
        ((User.role == 'sponsor') & (User.sponsor_approved.is_(None))) |
        ((User.role == 'influencer') & (User.influencer_approved.is_(None)))
    ).order_by(User.created_at.desc()).limit(5).all()
    
    # Send to all admins
    for admin in admins:
        # Render the template with context
        body = render_template('emails/pending_approval_admin.html',
            admin=admin,
            pending_sponsors=pending_sponsors,
            pending_influencers=pending_influencers,
            pending_details=pending_details,
            frontend_url=frontend_url
        )
        
        send_email(subject, admin.email, body)
    
    return f"Pending approvals notification sent to {len(admins)} admins"


@celery.task()
def send_sponsor_stats_update():
    """
    Send detailed stats to sponsors
    Includes: pending ad requests, negotiations, campaigns, etc.
    """
    try:
        sponsors = User.query.filter_by(role='sponsor', is_active=True, sponsor_approved=True).all()
        print(f"Sponsor Stats Update - Found {len(sponsors)} approved sponsors to notify")
        
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
        
        sent_count = 0
        for sponsor in sponsors:
            try:
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
                
                # Get recent ad requests
                recent_requests_data = get_recent_requests_for_sponsor(sponsor.id)
                
                # Generate stats summary email using template
                subject = f"Sponnect Sponsor Status Update - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
                
                # Render the template with context
                body = render_template('emails/sponsor_stats.html',
                    sponsor=sponsor,
                    active_campaigns=active_campaigns,
                    total_campaigns=total_campaigns,
                    pending_requests=pending_requests,
                    active_negotiations=active_negotiations,
                    accepted_partnerships=accepted_partnerships,
                    pending_progress_updates=pending_progress_updates,
                    recent_requests=recent_requests_data,
                    frontend_url=frontend_url
                )
                
                if sponsor.email:
                    send_email(subject, sponsor.email, body)
                    sent_count += 1
                    print(f"Sent stats update to sponsor: {sponsor.email}")
                else:
                    print(f"Sponsor {sponsor.username} has no email address")
                    
            except Exception as e:
                print(f"Error sending to sponsor {sponsor.username}: {str(e)}")
        
        return f"Sponsor stats update sent to {sent_count} sponsors"
    except Exception as e:
        error_message = f"Error in send_sponsor_stats_update: {str(e)}"
        print(error_message)
        return error_message


@celery.task()
def send_influencer_stats_update():
    """
    Send detailed stats to influencers
    Includes: campaigns, ad requests, progress updates, etc.
    """
    try:
        influencers = User.query.filter_by(role='influencer', is_active=True, influencer_approved=True).all()
        print(f"Influencer Stats Update - Found {len(influencers)} approved influencers to notify")
        
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
        
        sent_count = 0
        for influencer in influencers:
            try:
                # Get ad request stats
                pending_applications = AdRequest.query.filter_by(
                    influencer_id=influencer.id,
                    status='Pending'
                ).count()
                
                # Get negotiation stats
                active_negotiations = AdRequest.query.filter_by(
                    influencer_id=influencer.id,
                    status='Negotiating'
                ).count()
                
                # Get active partnerships
                active_partnerships = AdRequest.query.filter_by(
                    influencer_id=influencer.id,
                    status='Accepted'
                ).count()
                
                # Get pending content reviews
                pending_content_reviews = ProgressUpdate.query.join(AdRequest).filter(
                    AdRequest.influencer_id == influencer.id,
                    ProgressUpdate.status == 'Pending'
                ).count()
                
                # Get matching campaigns
                matching_campaigns = Campaign.query.filter(
                    Campaign.visibility == 'public',
                    Campaign.end_date >= datetime.utcnow(),
                    (Campaign.category == influencer.category) | (Campaign.category == 'any')
                ).count()
                
                # Get recent matching campaigns
                recent_matching_campaigns = Campaign.query.filter(
                    Campaign.visibility == 'public',
                    Campaign.end_date >= datetime.utcnow(),
                    (Campaign.category == influencer.category) | (Campaign.category == 'any')
                ).order_by(Campaign.created_at.desc()).limit(3).all()
                
                # Generate stats summary email using template
                subject = f"Sponnect Influencer Status Update - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
                
                # Render the template with context
                body = render_template('emails/influencer_stats.html',
                    influencer=influencer,
                    pending_applications=pending_applications,
                    active_negotiations=active_negotiations,
                    active_partnerships=active_partnerships,
                    pending_content_reviews=pending_content_reviews,
                    matching_campaigns=matching_campaigns,
                    recent_matching_campaigns=recent_matching_campaigns,
                    frontend_url=frontend_url
                )
                
                if influencer.email:
                    send_email(subject, influencer.email, body)
                    sent_count += 1
                    print(f"Sent stats update to influencer: {influencer.email}")
                else:
                    print(f"Influencer {influencer.username} has no email address")
                    
            except Exception as e:
                print(f"Error sending to influencer {influencer.username}: {str(e)}")
        
        return f"Influencer stats update sent to {sent_count} influencers"
    except Exception as e:
        error_message = f"Error in send_influencer_stats_update: {str(e)}"
        print(error_message)
        return error_message


@celery.task()
def send_admin_daily_report():
    """
    Send daily summary report to admins
    Includes: user stats, campaign stats, ad request stats, system health, etc.
    """
    try:
        admins = User.query.filter_by(role='admin').all()
        if not admins:
            return "No admin users found"
        
        print(f"Admin Daily Report - Preparing report for {len(admins)} admins")
        
        # Get general platform stats
        total_users = User.query.count()
        active_campaigns = Campaign.query.filter(Campaign.end_date >= datetime.utcnow()).count()
        total_ad_requests = AdRequest.query.count()
        completed_partnerships = AdRequest.query.filter(AdRequest.status == 'Completed').count()
        
        # Get pending approvals
        pending_sponsors = User.query.filter(
            (User.role == 'sponsor') & (User.sponsor_approved.is_(None))
        ).count()
        
        pending_influencers = User.query.filter(
            (User.role == 'influencer') & (User.influencer_approved.is_(None))
        ).count()
        
        pending_approvals = pending_sponsors + pending_influencers
        
        # Get daily activity
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        
        new_users = User.query.filter(User.created_at >= one_day_ago).count()
        new_campaigns = Campaign.query.filter(Campaign.created_at >= one_day_ago).count()
        new_ad_requests = AdRequest.query.filter(AdRequest.created_at >= one_day_ago).count()
        new_payments = Payment.query.filter(Payment.created_at >= one_day_ago).count()
        
        # Get mock data for system status (in a real system, these would come from monitoring)
        db_size = "24.5 MB"
        storage_usage = "678.2 MB (34%)"
        api_health = "Good"
        
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
        
        sent_count = 0
        for admin in admins:
            try:
                # Generate daily report email using template
                subject = f"Sponnect Admin Daily Report - {datetime.utcnow().strftime('%Y-%m-%d')}"
                
                # Render the template with context
                body = render_template('emails/admin_daily_report.html',
                    admin=admin,
                    pending_approvals=pending_approvals,
                    pending_sponsors=pending_sponsors,
                    pending_influencers=pending_influencers,
                    total_users=total_users,
                    active_campaigns=active_campaigns,
                    total_ad_requests=total_ad_requests,
                    completed_partnerships=completed_partnerships,
                    new_users=new_users,
                    new_campaigns=new_campaigns,
                    new_ad_requests=new_ad_requests,
                    new_payments=new_payments,
                    reports=[],  # Mock data for content reports
                    disputes=[],  # Mock data for payment disputes
                    db_size=db_size,
                    storage_usage=storage_usage,
                    api_health=api_health,
                    frontend_url=frontend_url
                )
                
                if admin.email:
                    send_email(subject, admin.email, body)
                    sent_count += 1
                    print(f"Sent daily report to admin: {admin.email}")
                else:
                    print(f"Admin {admin.username} has no email address")
                    
            except Exception as e:
                print(f"Error sending to admin {admin.username}: {str(e)}")
        
        return f"Admin daily report sent to {sent_count} admins"
    except Exception as e:
        error_message = f"Error in send_admin_daily_report: {str(e)}"
        print(error_message)
        return error_message 