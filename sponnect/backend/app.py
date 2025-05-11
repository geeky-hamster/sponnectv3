# app.py
import os
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, get_jwt, verify_jwt_in_request
)
from functools import wraps
from datetime import datetime, timedelta, timezone
from sqlalchemy import func # For stats count
from math import ceil # For pagination calculation
import os
from sqlalchemy import extract, case, text, or_, and_
import json
import time

from config import Config
from models import db, User, Campaign, AdRequest, Payment, NegotiationHistory, ProgressUpdate
from constants import INDUSTRY_TO_CATEGORY, DEFAULT_CATEGORY, map_industry_to_category, CATEGORIES, INDUSTRIES, INFLUENCER_CATEGORIES

# --- App Initialization ---
app = Flask(__name__, static_folder='../frontend/dist', static_url_path='/')
# Fix CORS configuration to allow all required methods
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "PATCH"]}}, supports_credentials=True)
app.config.from_object(Config)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///sponnect.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'super-secret')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)  # Token expires in 24 hours
app.config['JWT_IDENTITY_CLAIM'] = 'sub'  # Use 'sub' claim to store identity

# --- Extension Initialization ---
db.init_app(app)  # Initialize the db instance from models.py
jwt = JWTManager(app)
with app.app_context(): # create tables if they don't exist
    db.create_all()

# Configure Flask-Mail
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'localhost')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 1025))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'False').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', None)
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', None)
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@sponnect.com')

# Configure Flask-Caching with Redis
app.config['CACHE_TYPE'] = 'redis'
app.config['CACHE_REDIS_URL'] = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 minutes default cache timeout

# Initialize extensions
from mailer import mail
from flask_caching import Cache
import workers
from workers import celery

mail.init_app(app)
cache = Cache(app)

# Configure Celery
celery.conf.update(
    broker_url=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/1'),
    result_backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_always_eager=False,
    broker_connection_retry_on_startup=True
)

# Set task base class which provides app context
celery.Task = workers.ContextTask

# Push app context
app.app_context().push()

# --- Error Handling ---
@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all unhandled exceptions."""
    # Log the error and stacktrace
    app.logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
    
    # Return a proper error response with CORS headers
    response = jsonify({"message": "Internal server error", "error": str(e)})
    response.status_code = 500
    return response

def serialize_pagination(pagination_obj):
    """Helper to generate pagination metadata."""
    return {
        'page': pagination_obj.page,
        'per_page': pagination_obj.per_page,
        'total_pages': pagination_obj.pages,
        'total_items': pagination_obj.total,
        'has_prev': pagination_obj.has_prev,
        'has_next': pagination_obj.has_next,
        'prev_num': pagination_obj.prev_num,
        'next_num': pagination_obj.next_num
    }

# --- Constants ---
# Indian Rupee symbol and IST timezone
CURRENCY_SYMBOL = '₹'
IST = timezone(timedelta(hours=5, minutes=30))  # IST is UTC+5:30

# --- Helper Functions for Currency and Time ---
def format_currency(amount):
    """Format amount as Indian Rupees"""
    if amount is None:
        return None
    return f"{CURRENCY_SYMBOL}{amount:,.2f}"

def utc_to_ist(utc_datetime):
    """Convert UTC datetime to IST timezone"""
    if utc_datetime is None:
        return None
    ist_datetime = utc_datetime.replace(tzinfo=timezone.utc).astimezone(IST)
    return ist_datetime

def format_datetime(utc_datetime, format_str="%d-%m-%Y %H:%M:%S"):
    """Convert UTC datetime to IST and format it"""
    if utc_datetime is None:
        return None
    ist_datetime = utc_to_ist(utc_datetime)
    return ist_datetime.strftime(format_str)

def format_date(utc_datetime, format_str="%d-%m-%Y"):
    """Convert UTC date to IST and format it"""
    if utc_datetime is None:
        return None
    ist_datetime = utc_to_ist(utc_datetime)
    return ist_datetime.strftime(format_str)

# --- Add Negotiation History ---
# The models are already imported at the top of the file, no need to reimport them

# Create tables if they don't exist (already done earlier)
# with app.app_context():
#    db.create_all()

# --- Decorators ---
def role_required(required_role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get('role')
            # Allow admin access to all role-restricted routes
            if user_role == 'admin':
                return fn(*args, **kwargs)
            if user_role != required_role:
                return jsonify(message=f"{required_role.capitalize()} access required"), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

admin_required = role_required('admin') # Note: Admin can access sponsor/influencer routes too
sponsor_required = role_required('sponsor')
influencer_required = role_required('influencer')

# --- Helper Functions ---
def serialize_user_basic(user):
    return {'id': user.id, 'username': user.username, 'role': user.role, 'is_flagged': user.is_flagged}

def serialize_user_profile(user):
    data = serialize_user_basic(user)
    data['email'] = user.email  # Add email field
    data['created_at'] = user.created_at.isoformat() if user.created_at else None
    data['is_active'] = user.is_active  # Include active status
    if user.role == 'sponsor':
        data.update({
            'company_name': user.company_name, 
            'industry': user.industry, 
            'sponsor_approved': user.sponsor_approved
        })
    elif user.role == 'influencer':
        data.update({
            'influencer_name': user.influencer_name, 
            'category': user.category, 
            'niche': user.niche, 
            'reach': user.reach,
            'influencer_approved': user.influencer_approved
        })
    return data

def serialize_campaign_basic(campaign):
     return {
        'id': campaign.id, 
        'name': campaign.name, 
        'budget': campaign.budget, 
        'budget_formatted': format_currency(campaign.budget),
        'visibility': campaign.visibility,
        'status': campaign.status, 
        'is_flagged': campaign.is_flagged
     }

def serialize_campaign_detail(campaign):
    data = serialize_campaign_basic(campaign)
    data.update({
        'description': campaign.description, 
        'goals': campaign.goals, 
        'sponsor_id': campaign.sponsor_id,
        'category': campaign.category,
        'start_date': format_date(campaign.start_date) if campaign.start_date else None,
        'end_date': format_date(campaign.end_date) if campaign.end_date else None,
        'created_at': format_datetime(campaign.created_at) if campaign.created_at else None,
        'start_date_iso': campaign.start_date.isoformat() if campaign.start_date else None,
        'end_date_iso': campaign.end_date.isoformat() if campaign.end_date else None,
        'created_at_iso': campaign.created_at.isoformat() if campaign.created_at else None,
        # Add sponsor details
        'sponsor_name': campaign.sponsor.username if campaign.sponsor else "Unknown",
        'sponsor_company': campaign.sponsor.company_name if campaign.sponsor else None,
    })
    return data

def serialize_ad_request_detail(ad_request):
    """Detailed ad request serialization with related objects"""
    try:
        # Get basic attributes
        result = {
            "id": ad_request.id,
            "status": ad_request.status,
            "payment_amount": ad_request.payment_amount,
            "requirements": ad_request.requirements,
            "message": ad_request.message,
            "last_offer_by": ad_request.last_offer_by,
            "payment_amount_formatted": format_currency(ad_request.payment_amount)
        }
        
        # Add dates with proper formatting - both ISO and human readable
        if ad_request.created_at:
            result["created_at"] = format_datetime(ad_request.created_at)
            result["created_at_iso"] = ad_request.created_at.isoformat()
        
        if ad_request.updated_at:
            result["updated_at"] = format_datetime(ad_request.updated_at)
            result["updated_at_iso"] = ad_request.updated_at.isoformat()
        
        # Include campaign details
        if ad_request.campaign:
            result["campaign"] = serialize_campaign_basic(ad_request.campaign)
            result["campaign_id"] = ad_request.campaign.id
            result["campaign_name"] = ad_request.campaign.name
        
        # Include influencer details
        if ad_request.target_influencer:
            result["influencer"] = serialize_user_basic(ad_request.target_influencer)
            result["influencer_id"] = ad_request.target_influencer.id
            result["influencer_name"] = ad_request.target_influencer.username
        
        # Include sponsor details through campaign if available
        if ad_request.campaign and ad_request.campaign.sponsor:
            result["sponsor"] = serialize_user_basic(ad_request.campaign.sponsor)
            result["sponsor_id"] = ad_request.campaign.sponsor.id
            result["sponsor_name"] = ad_request.campaign.sponsor.username
        
        return result
    except Exception as e:
        app.logger.error(f"Error serializing ad request {ad_request.id}: {str(e)}")
        # Return minimal information to avoid breaking the frontend
        return {
            "id": ad_request.id,
            "status": getattr(ad_request, "status", "Unknown"),
            "error": "Error processing this ad request"
        }

def serialize_negotiation_history(history_item):
    return {
        'id': history_item.id,
        'ad_request_id': history_item.ad_request_id,
        'user_id': history_item.user_id,
        'user_role': history_item.user_role,
        'action': history_item.action,
        'message': history_item.message,
        'payment_amount': history_item.payment_amount,
        'payment_amount_formatted': format_currency(history_item.payment_amount),
        'requirements': history_item.requirements,
        'created_at': format_datetime(history_item.created_at) if history_item.created_at else None,
        'created_at_iso': history_item.created_at.isoformat() if history_item.created_at else None,
        'username': history_item.user.username if history_item.user else None,
    }

# --- CLI Command for Admin Creation ---
@app.cli.command("create-admin")
def create_admin_command():
    """Creates the admin user from .env variables."""
    admin_email = Config.ADMIN_EMAIL
    admin_password = Config.ADMIN_PASSWORD
    if not admin_email or not admin_password:
        print("Error: ADMIN_EMAIL and ADMIN_PASSWORD missing in .env")
        return

    with app.app_context():  # Important: establish app context
        if User.query.filter_by(email=admin_email, role='admin').first():
            print(f"Admin '{admin_email}' already exists.")
            return

        admin_user = User(
            username=Config.ADMIN_USERNAME,  # Use ADMIN_USERNAME from config
            email=Config.ADMIN_EMAIL,
            role='admin',
            is_active=True,
            sponsor_approved=True
        )
        admin_user.set_password(admin_password)
        db.session.add(admin_user)
        try:
            db.session.commit()
            print(f"Admin user '{admin_email}' created.")
        except Exception as e:  # Handle potential database errors
            print(f"Error creating admin user: {e}")
            db.session.rollback()  # Rollback changes in case of error


# --- Routes ---

# == Authentication ==
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['username', 'email', 'password', 'role']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400
    
    # Check if username or email already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 400
    
    # Validate role
    if data['role'] not in ['sponsor', 'influencer']:
        return jsonify({'message': 'Invalid role'}), 400
    
    # Create new user
    new_user = User(
        username=data['username'],
        email=data['email'],
        role=data['role']
    )
    new_user.set_password(data['password'])
    
    # Additional fields for sponsor
    if data['role'] == 'sponsor':
        if 'company_name' not in data:
            return jsonify({'message': 'Company name is required for sponsors'}), 400
        
        new_user.company_name = data['company_name']
        
        # Optional fields
        new_user.industry = data.get('industry', '')
        
        # Start as pending approval
        new_user.sponsor_approved = None
    
    # Additional fields for influencer
    elif data['role'] == 'influencer':
        if 'influencer_name' not in data:
            return jsonify({'message': 'Influencer name is required'}), 400
        
        new_user.influencer_name = data['influencer_name']
        
        # Optional fields with defaults
        new_user.category = data.get('category', 'Other')
        new_user.niche = data.get('niche', '')
        new_user.bio = data.get('bio', '')
        new_user.reach = int(data.get('reach', 0))
        
        # Start as pending approval
        new_user.influencer_approved = None
    
    try:
        db.session.add(new_user)
        db.session.commit()
        
        # Send registration pending notification
        from user_notifications import send_registration_pending_notification
        send_registration_pending_notification.delay(new_user.id)
        
        return jsonify({
            'message': 'User registered successfully. Account is pending approval.',
            'user_id': new_user.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error creating user: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data:
        return jsonify({"message": "Missing JSON in request"}), 400
        
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not password:
        return jsonify({"message": "Password is required"}), 400
        
    if not username and not email:
        return jsonify({"message": "Username or email is required"}), 400
        
    # Check if login is with username or email
    if username:
        user = User.query.filter_by(username=username).first()
    else:
        user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        return jsonify({"message": "Invalid login credentials"}), 401
        
    # Check if user is active
    if not getattr(user, 'is_active', True):
        return jsonify({"message": "Account is disabled. Please contact support."}), 403
    
    # Check if user is flagged
    if user.is_flagged:
        return jsonify({
            "message": "Your account has been flagged due to policy violations. Please contact support for assistance.",
            "error": "ACCOUNT_FLAGGED"
        }), 403
    
    # Check role-specific approval requirements
    if user.role == 'sponsor' and user.sponsor_approved is False:
        return jsonify({"message": "Your sponsor account has been rejected. Please contact support."}), 403
    
    if user.role == 'influencer' and user.influencer_approved is False:
        return jsonify({"message": "Your influencer account has been rejected. Please contact support."}), 403
    
    if (user.role == 'sponsor' and user.sponsor_approved is None) or \
       (user.role == 'influencer' and user.influencer_approved is None):
        return jsonify({"message": "Your account is pending approval"}), 403
    
    # Create access token with role in additional_claims
    expires = datetime.utcnow() + timedelta(days=1)
    # Add 'role' to the token's claims to match what the decorator expects
    additional_claims = {"role": user.role}
    access_token = create_access_token(
        identity=user.id, 
        expires_delta=expires - datetime.utcnow(),
        additional_claims=additional_claims
    )
    
    # Update last login time
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Send login stats to the user's email
    from user_notifications import send_login_stats
    send_login_stats.delay(user.id)
    
    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user_role": user.role,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    }), 200



# == Profile Management ==
@app.route('/api/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user: return jsonify({"message": "User not found"}), 404
    return jsonify(serialize_user_profile(user)), 200

@app.route('/api/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user: return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    # Update fields based on role - prevent users from changing role/approval status
    if user.role == 'sponsor':
        # Check if industry is being changed
        industry_changed = 'industry' in data and data['industry'] != user.industry
        old_industry = user.industry
        
        # Update sponsor fields
        user.company_name = data.get('company_name', user.company_name)
        user.industry = data.get('industry', user.industry)
        
        # If industry changed, update all campaign categories
        if industry_changed and user.industry:
            # Get all campaigns for this sponsor
            campaigns = Campaign.query.filter_by(sponsor_id=user_id).all()
            
            # Update all campaigns with the new category based on industry
            new_category = map_industry_to_category(user.industry)
            for campaign in campaigns:
                # Only update campaigns that haven't been explicitly categorized
                # or have the old category derived from the old industry
                old_category = map_industry_to_category(old_industry)
                if not campaign.category or campaign.category == old_category:
                    campaign.category = new_category
    
    elif user.role == 'influencer':
        user.influencer_name = data.get('influencer_name', user.influencer_name)
        user.category = data.get('category', user.category)
        user.niche = data.get('niche', user.niche)
        if 'reach' in data: # Allow updating reach, maybe validate later
             try: user.reach = int(data['reach'])
             except (ValueError, TypeError): pass

    db.session.commit()
    return jsonify({"message": "Profile updated successfully", "profile": serialize_user_profile(user)}), 200

@app.route('/api/influencers/<int:influencer_id>/profile', methods=['GET'])
@jwt_required() # Any logged-in user can view public profile
def get_public_influencer_profile(influencer_id):
    user = User.query.filter_by(id=influencer_id, role='influencer', is_active=True).first()
    if not user: return jsonify({"message": "Active influencer not found"}), 404
    # Return only public-safe info
    return jsonify({'id': user.id, 'influencer_name': user.influencer_name, 'category': user.category,
                    'niche': user.niche, 'reach': user.reach }), 200

# == Admin Actions ==
@app.route('/api/admin/stats', methods=['GET'])
@jwt_required()
@admin_required
def get_admin_stats():
    # Basic counts - can be expanded with date ranges, etc.
    total_users = db.session.query(func.count(User.id)).scalar()
    active_sponsors = User.query.filter_by(role='sponsor', is_active=True, sponsor_approved=True).count()
    pending_sponsors = User.query.filter_by(role='sponsor', sponsor_approved=False).count()
    active_influencers = User.query.filter_by(role='influencer', is_active=True, influencer_approved=True).count()
    pending_influencers = User.query.filter_by(role='influencer', influencer_approved=False).count()
    public_campaigns = Campaign.query.filter_by(visibility='public').count()
    private_campaigns = Campaign.query.filter_by(visibility='private').count()
    flagged_users = User.query.filter_by(is_flagged=True).count()
    flagged_campaigns = Campaign.query.filter_by(is_flagged=True).count()
    ad_request_stats = db.session.query(AdRequest.status, func.count(AdRequest.id)).group_by(AdRequest.status).all()
    
    # Payment and fees stats
    total_payments = db.session.query(func.sum(Payment.amount)).filter(Payment.status == 'Completed').scalar() or 0
    total_platform_fees = db.session.query(func.sum(Payment.platform_fee)).filter(Payment.status == 'Completed').scalar() or 0
    total_payment_count = db.session.query(func.count(Payment.id)).filter(Payment.status == 'Completed').scalar() or 0
    
    # Get recent fees (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_fees = db.session.query(func.sum(Payment.platform_fee)).filter(
        Payment.status == 'Completed',
        Payment.created_at >= thirty_days_ago
    ).scalar() or 0

    return jsonify({
        'total_users': total_users, 
        'active_sponsors': active_sponsors, 
        'pending_sponsors': pending_sponsors,
        'active_influencers': active_influencers, 
        'pending_influencers': pending_influencers,
        'public_campaigns': public_campaigns, 
        'private_campaigns': private_campaigns,
        'flagged_users': flagged_users, 
        'flagged_campaigns': flagged_campaigns,
        'ad_requests_by_status': dict(ad_request_stats),
        'payment_stats': {
            'total_payments': round(total_payments, 2),
            'total_payments_formatted': format_currency(total_payments),
            'total_platform_fees': round(total_platform_fees, 2),
            'total_platform_fees_formatted': format_currency(total_platform_fees),
            'total_payment_count': total_payment_count,
            'recent_fees': round(recent_fees, 2),
            'recent_fees_formatted': format_currency(recent_fees),
            'currency_symbol': CURRENCY_SYMBOL
        }
    }), 200

@app.route('/api/admin/pending_sponsors', methods=['GET'])
@jwt_required()
@admin_required
def admin_get_pending_sponsors():
    pending = User.query.filter_by(role='sponsor', sponsor_approved=False, is_active=True).all()
    return jsonify([serialize_user_profile(user) for user in pending]), 200

@app.route('/api/admin/pending_influencers', methods=['GET'])
@jwt_required()
@admin_required
def admin_get_pending_influencers():
    pending = User.query.filter_by(role='influencer', influencer_approved=False, is_active=True).all()
    return jsonify([serialize_user_profile(user) for user in pending]), 200

@app.route('/api/admin/pending_users', methods=['GET'])
@jwt_required()
@admin_required
def admin_get_pending_users():
    """Get all pending users (both sponsors and influencers)"""
    pending_sponsors = User.query.filter_by(role='sponsor', sponsor_approved=False, is_active=True).all()
    pending_influencers = User.query.filter_by(role='influencer', influencer_approved=False, is_active=True).all()
    
    all_pending = pending_sponsors + pending_influencers
    return jsonify([serialize_user_profile(user) for user in all_pending]), 200

@app.route('/api/admin/sponsors/<int:sponsor_id>/approve', methods=['PATCH'])
@jwt_required()
@admin_required
def admin_approve_sponsor(sponsor_id):
    sponsor = User.query.filter_by(id=sponsor_id, role='sponsor').first()
    
    if not sponsor:
        return jsonify({"message": "Sponsor not found"}), 404
        
    sponsor.sponsor_approved = True
    sponsor.is_active = True  # Also activate the account
    
    db.session.commit()
    
    # Send account approval notification
    from user_notifications import send_account_approval_notification
    send_account_approval_notification.delay(sponsor.id)
    
    return jsonify({"message": "Sponsor approved successfully"}), 200

@app.route('/api/admin/influencers/<int:influencer_id>/approve', methods=['PATCH'])
@jwt_required()
@admin_required
def admin_approve_influencer(influencer_id):
    influencer = User.query.filter_by(id=influencer_id, role='influencer').first()
    
    if not influencer:
        return jsonify({"message": "Influencer not found"}), 404
        
    influencer.influencer_approved = True
    influencer.is_active = True  # Also activate the account
    
    db.session.commit()
    
    # Send account approval notification
    from user_notifications import send_account_approval_notification
    send_account_approval_notification.delay(influencer.id)
    
    return jsonify({"message": "Influencer approved successfully"}), 200

@app.route('/api/admin/sponsors/<int:sponsor_id>/reject', methods=['PATCH'])
@jwt_required()
@admin_required
def admin_reject_sponsor(sponsor_id):
    sponsor = db.session.get(User, sponsor_id)
    if not sponsor or sponsor.role != 'sponsor': return jsonify({"message": "Sponsor not found"}), 404
    if sponsor.sponsor_approved is not False: return jsonify({"message": "Can only reject pending sponsors"}), 400
    sponsor.is_active = False # Deactivate rejected sponsors
    sponsor.sponsor_approved = None # Reset approval status, maybe? Or keep False. Keep False.
    db.session.commit()
    return jsonify({"message": "Sponsor rejected and deactivated"}), 200

@app.route('/api/admin/influencers/<int:influencer_id>/reject', methods=['PATCH'])
@jwt_required()
@admin_required
def admin_reject_influencer(influencer_id):
    influencer = db.session.get(User, influencer_id)
    if not influencer or influencer.role != 'influencer': return jsonify({"message": "Influencer not found"}), 404
    if influencer.influencer_approved is not False: return jsonify({"message": "Can only reject pending influencers"}), 400
    influencer.is_active = False # Deactivate rejected influencers
    influencer.influencer_approved = None # Reset approval status
    db.session.commit()
    return jsonify({"message": "Influencer rejected and deactivated"}), 200

@app.route('/api/admin/users/<int:user_id>/flag', methods=['PATCH'])
@jwt_required()
@admin_required
def admin_flag_user(user_id):
    user = db.session.get(User, user_id)
    if not user or user.role == 'admin': return jsonify({"message": "User not found or cannot flag admin"}), 404
    
    # Flag the user
    user.is_flagged = True
    
    # Cascade flag to related content
    if user.role == 'sponsor':
        # Flag all campaigns by this sponsor
        campaigns = Campaign.query.filter_by(sponsor_id=user_id).all()
        for campaign in campaigns:
            campaign.is_flagged = True
        
        # Flag all ad requests associated with these campaigns
        for campaign in campaigns:
            ad_requests = AdRequest.query.filter_by(campaign_id=campaign.id).all()
            for ad_request in ad_requests:
                ad_request.is_flagged = True
    
    elif user.role == 'influencer':
        # Flag all ad requests where this user is the influencer
        ad_requests = AdRequest.query.filter_by(influencer_id=user_id).all()
        for ad_request in ad_requests:
            ad_request.is_flagged = True
    
    db.session.commit()
    
    # Count affected items for the response
    flagged_campaigns = 0
    flagged_ad_requests = 0
    
    if user.role == 'sponsor':
        flagged_campaigns = Campaign.query.filter_by(sponsor_id=user_id, is_flagged=True).count()
        flagged_ad_requests = AdRequest.query.join(Campaign).filter(Campaign.sponsor_id == user_id, AdRequest.is_flagged == True).count()
    elif user.role == 'influencer':
        flagged_ad_requests = AdRequest.query.filter_by(influencer_id=user_id, is_flagged=True).count()
    
    return jsonify({
        "message": "User flagged successfully",
        "flagged_items": {
            "user": user.username,
            "role": user.role,
            "campaigns": flagged_campaigns,
            "ad_requests": flagged_ad_requests
        }
    }), 200

@app.route('/api/admin/users/<int:user_id>/unflag', methods=['PATCH'])
@jwt_required()
@admin_required
def admin_unflag_user(user_id):
    user = db.session.get(User, user_id)
    if not user: return jsonify({"message": "User not found"}), 404
    
    # Unflag the user
    user.is_flagged = False
    
    # Check if we should cascade unflag
    cascade = request.args.get('cascade', 'false').lower() == 'true'
    
    if cascade:
        # Cascade unflag to related content
        if user.role == 'sponsor':
            # Unflag all campaigns by this sponsor
            campaigns = Campaign.query.filter_by(sponsor_id=user_id).all()
            for campaign in campaigns:
                campaign.is_flagged = False
            
            # Unflag all ad requests associated with these campaigns
            for campaign in campaigns:
                ad_requests = AdRequest.query.filter_by(campaign_id=campaign.id).all()
                for ad_request in ad_requests:
                    ad_request.is_flagged = False
        
        elif user.role == 'influencer':
            # Unflag all ad requests where this user is the influencer
            ad_requests = AdRequest.query.filter_by(influencer_id=user_id).all()
            for ad_request in ad_requests:
                ad_request.is_flagged = False
                
        unflagged_campaigns = 0
        unflagged_ad_requests = 0
        
        if user.role == 'sponsor':
            unflagged_campaigns = Campaign.query.filter_by(sponsor_id=user_id).count()
            unflagged_ad_requests = AdRequest.query.join(Campaign).filter(Campaign.sponsor_id == user_id).count()
        elif user.role == 'influencer':
            unflagged_ad_requests = AdRequest.query.filter_by(influencer_id=user_id).count()
            
        message = "User unflagged with cascade"
        response_data = {
            "unflagged_items": {
                "user": user.username,
                "role": user.role,
                "campaigns": unflagged_campaigns,
                "ad_requests": unflagged_ad_requests
            }
        }
    else:
        message = "User unflagged"
        response_data = {}
    
    db.session.commit()
    
    return jsonify({"message": message, **response_data}), 200

@app.route('/api/admin/campaigns/<int:campaign_id>/flag', methods=['PATCH'])
@jwt_required()
@admin_required
def admin_flag_campaign(campaign_id):
    campaign = db.session.get(Campaign, campaign_id)
    if not campaign: return jsonify({"message": "Campaign not found"}), 404
    campaign.is_flagged = True
    db.session.commit()
    return jsonify({"message": "Campaign flagged"}), 200

@app.route('/api/admin/campaigns', methods=['GET'])
@jwt_required()
@admin_required
def admin_list_campaigns():
    """Get list of campaigns with pagination and filtering options"""
    # Parse query parameters
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)  # Cap at 100 items
    
    # Filtering options
    name = request.args.get('name', '')
    flagged = request.args.get('flagged', '').lower() == 'true'
    status = request.args.get('status', '')
    sponsor_id = request.args.get('sponsor_id')
    budget_min = request.args.get('budget_min', type=float)
    budget_max = request.args.get('budget_max', type=float)
    
    # Sorting options
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    # Build query
    query = Campaign.query
    
    # Apply filters
    if name:
        query = query.filter(Campaign.name.ilike(f'%{name}%'))
    if flagged:
        query = query.filter(Campaign.is_flagged == True)
    if status:
        query = query.filter(Campaign.status == status)
    if sponsor_id:
        try:
            sponsor_id = int(sponsor_id)
            query = query.filter(Campaign.sponsor_id == sponsor_id)
        except (ValueError, TypeError):
            pass  # Invalid sponsor_id, ignore filter
    
    # Apply budget filters
    if budget_min is not None:
        query = query.filter(Campaign.budget >= budget_min)
    if budget_max is not None:
        query = query.filter(Campaign.budget <= budget_max)
    
    # Apply sorting
    if sort_by:
        if hasattr(Campaign, sort_by):
            sort_attr = getattr(Campaign, sort_by)
            if sort_order.lower() == 'asc':
                query = query.order_by(sort_attr.asc())
            else:
                query = query.order_by(sort_attr.desc())
        else:
            # Default sort if invalid sort_by
            query = query.order_by(Campaign.created_at.desc())
    else:
        # Default sort
        query = query.order_by(Campaign.created_at.desc())
    
    # Paginate
    campaigns = query.paginate(page=page, per_page=per_page)
    
    # Return response
    return jsonify({
        'campaigns': [serialize_campaign_detail(c) for c in campaigns.items],
        'pagination': serialize_pagination(campaigns)
    }), 200

# == Sponsor: Campaign Management ==
@app.route('/api/sponsor/campaigns', methods=['POST'])
@jwt_required()
@sponsor_required
def sponsor_create_campaign():
    data = request.get_json(); sponsor_id = get_jwt_identity()
    required = ['name', 'budget', 'start_date', 'visibility']
    if not all(f in data for f in required): return jsonify({"message": "Missing fields"}), 400
    try:
        start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00')) if data.get('end_date') else None
        budget = float(data['budget'])
        if data['visibility'] not in ['public', 'private']: raise ValueError("Invalid visibility")
    except (ValueError, TypeError): return jsonify({"message": "Invalid date, budget, or visibility"}), 400

    # Get sponsor to inherit category based on industry
    sponsor = db.session.get(User, sponsor_id)
    
    # Use provided category if available, otherwise map from industry
    category = data.get('category')
    if not category and sponsor and sponsor.industry:
        category = map_industry_to_category(sponsor.industry)

    campaign = Campaign(sponsor_id=sponsor_id, name=data['name'], budget=budget, start_date=start_date,
                        end_date=end_date, visibility=data['visibility'], category=category,
                        description=data.get('description'), goals=data.get('goals'))
    db.session.add(campaign); db.session.commit()
    return jsonify({"message": "Campaign created", "campaign": serialize_campaign_detail(campaign)}), 201

@app.route('/api/sponsor/campaigns', methods=['GET'])
@jwt_required()
@sponsor_required
def sponsor_get_campaigns():
    sponsor_id = get_jwt_identity()
    campaigns = Campaign.query.filter_by(sponsor_id=sponsor_id).order_by(Campaign.created_at.desc()).all()
    return jsonify([serialize_campaign_detail(c) for c in campaigns]), 200

@app.route('/api/sponsor/campaigns/<int:campaign_id>', methods=['GET'])
@jwt_required()
@sponsor_required
def sponsor_get_campaign(campaign_id):
    sponsor_id = get_jwt_identity()
    campaign = Campaign.query.filter_by(id=campaign_id, sponsor_id=sponsor_id).first()
    if not campaign: return jsonify({"message": "Campaign not found or access denied"}), 404
    return jsonify(serialize_campaign_detail(campaign)), 200

@app.route('/api/sponsor/campaigns/<int:campaign_id>', methods=['PUT'])
@jwt_required()
@sponsor_required
def sponsor_update_campaign(campaign_id):
    sponsor_id = get_jwt_identity(); data = request.get_json()
    campaign = Campaign.query.filter_by(id=campaign_id, sponsor_id=sponsor_id).first()
    if not campaign: return jsonify({"message": "Campaign not found/denied"}), 404

    # Selective update
    if 'name' in data: campaign.name = data['name']
    if 'description' in data: campaign.description = data['description']
    if 'goals' in data: campaign.goals = data['goals']
    if 'visibility' in data and data['visibility'] in ['public', 'private']: campaign.visibility = data['visibility']
    
    # Update category if provided, otherwise keep existing or inherit from sponsor if null
    if 'category' in data:
        if data['category']:
            campaign.category = data['category']
        elif data['category'] is None:
            # Inherit from sponsor if explicitly setting to null
            sponsor = db.session.get(User, sponsor_id)
            if sponsor and sponsor.industry:
                campaign.category = map_industry_to_category(sponsor.industry)
            else:
                campaign.category = DEFAULT_CATEGORY
            
    if 'budget' in data:
        try: campaign.budget = float(data['budget'])
        except (ValueError, TypeError): pass # ignore invalid budget on update
    for date_field in ['start_date', 'end_date']:
         if date_field in data:
              try:
                  date_val = datetime.fromisoformat(data[date_field].replace('Z', '+00:00')) if data[date_field] else None
                  setattr(campaign, date_field, date_val)
              except (ValueError, TypeError): pass

    db.session.commit()
    return jsonify({"message": "Campaign updated", "campaign": serialize_campaign_detail(campaign)}), 200

@app.route('/api/sponsor/campaigns/<int:campaign_id>', methods=['DELETE'])
@jwt_required()
@sponsor_required
def sponsor_delete_campaign(campaign_id):
    sponsor_id = get_jwt_identity()
    campaign = Campaign.query.filter_by(id=campaign_id, sponsor_id=sponsor_id).first()
    if not campaign: return jsonify({"message": "Campaign not found/denied"}), 404
    db.session.delete(campaign); db.session.commit() # Cascade deletes AdRequests
    return jsonify({"message": "Campaign deleted"}), 200

# == Sponsor: Ad Request Management ==
@app.route('/api/sponsor/campaigns/<int:campaign_id>/ad_requests', methods=['POST'])
@jwt_required()
@sponsor_required
def sponsor_create_ad_request(campaign_id):
    sponsor_id = get_jwt_identity()
    campaign = Campaign.query.filter_by(id=campaign_id, sponsor_id=sponsor_id).first()
    if not campaign: return jsonify({"message": "Campaign not found/denied"}), 404

    data = request.get_json()
    required = ['influencer_id', 'requirements', 'payment_amount']
    if not all(f in data for f in required): return jsonify({"message": "Missing fields"}), 400
    influencer = User.query.filter_by(id=data['influencer_id'], role='influencer', is_active=True).first()
    if not influencer: return jsonify({"message": "Active influencer not found"}), 404
    try: payment = float(data['payment_amount'])
    except (ValueError, TypeError): return jsonify({"message": "Invalid payment amount"}), 400

    # Check if any request already exists for this influencer on this campaign (regardless of status)
    existing_request = AdRequest.query.filter_by(
        campaign_id=campaign.id,
        influencer_id=influencer.id
    ).first()
    if existing_request:
        status_msg = f"An ad request already exists for this influencer on this campaign (status: {existing_request.status})"
        return jsonify({"message": status_msg, "ad_request_id": existing_request.id}), 409

    ad_request = AdRequest(
        campaign_id=campaign.id, influencer_id=influencer.id, initiator_id=sponsor_id, last_offer_by='sponsor',
        message=data.get('message'), requirements=data['requirements'], payment_amount=payment, status='Pending'
    )
    db.session.add(ad_request)
    db.session.flush()  # Get the ad_request ID before committing
    
    # Create initial history record
    history = NegotiationHistory(
        ad_request_id=ad_request.id,
        user_id=sponsor_id,
        user_role='sponsor',
        action='propose',
        message=data.get('message'),
        payment_amount=payment,
        requirements=data['requirements']
    )
    db.session.add(history)
    
    db.session.commit()
    
    # Schedule notification email task for new ad request
    from task import send_test_email
    send_test_email.delay(influencer.email)
    
    return jsonify({
        "message": "Ad request created successfully",
        "ad_request": serialize_ad_request_detail(ad_request)
    }), 201

@app.route('/api/sponsor/ad_requests', methods=['GET']) # Get all ad requests initiated by sponsor
@jwt_required()
@sponsor_required
def sponsor_get_all_ad_requests():
    sponsor_id = get_jwt_identity()
    status_filter = request.args.get('status')
    campaign_id_filter = request.args.get('campaign_id')

    query = AdRequest.query.join(Campaign).filter(Campaign.sponsor_id == sponsor_id) # Filter by sponsor via campaign

    if status_filter: query = query.filter(AdRequest.status == status_filter)
    if campaign_id_filter:
         try: query = query.filter(AdRequest.campaign_id == int(campaign_id_filter))
         except ValueError: pass

    requests = query.order_by(AdRequest.updated_at.desc()).all()
    
    # Safe serialization with error handling
    ad_requests_data = []
    for ar in requests:
        try:
            data = {
                "id": ar.id,
                "campaign_id": ar.campaign_id,
                "campaign_name": ar.campaign.name if ar.campaign else "Unknown",
                "influencer_id": ar.influencer_id,
                "influencer_name": ar.target_influencer.username if ar.target_influencer else "Unknown",
                "status": ar.status,
                "payment_amount": ar.payment_amount,
                "payment_amount_formatted": format_currency(ar.payment_amount),
                "last_offer_by": ar.last_offer_by,
                "requirements": ar.requirements,
                "created_at": format_datetime(ar.created_at) if ar.created_at else None,
                "updated_at": format_datetime(ar.updated_at) if ar.updated_at else None,
                "created_at_iso": ar.created_at.isoformat() if ar.created_at else None,
                "updated_at_iso": ar.updated_at.isoformat() if ar.updated_at else None
            }
            ad_requests_data.append(data)
        except Exception as e:
            app.logger.error(f"Error serializing ad request {ar.id}: {str(e)}")
            # Continue with next item instead of failing completely
            
    return jsonify({
        "ad_requests": ad_requests_data,
        "currency_symbol": CURRENCY_SYMBOL
    }), 200

@app.route('/api/sponsor/ad_requests/<int:ad_request_id>', methods=['GET'])
@jwt_required()
@sponsor_required
def sponsor_get_ad_request(ad_request_id):
    sponsor_id = get_jwt_identity()
    
    try:
        ad_request = db.session.get(AdRequest, ad_request_id)
        
        if not ad_request:
            return jsonify({"message": "Ad Request not found"}), 404
        
        # Check ownership via campaign
        if not ad_request.campaign or ad_request.campaign.sponsor_id != sponsor_id:
            return jsonify({"message": "Access denied"}), 403
        
        # Get negotiation history
        negotiations = NegotiationHistory.query.filter_by(ad_request_id=ad_request_id).order_by(NegotiationHistory.created_at).all()
        negotiation_history = [
            {
                "id": neg.id,
                "action": neg.action,
                "message": neg.message,
                "payment_amount": neg.payment_amount,
                "payment_amount_formatted": format_currency(neg.payment_amount),
                "requirements": neg.requirements,
                "actor": neg.user_role,
                "actor_name": neg.user.username if neg.user else "Unknown User",
                "created_at": format_datetime(neg.created_at) if neg.created_at else None,
                "created_at_iso": neg.created_at.isoformat() if neg.created_at else None
            } for neg in negotiations
        ]
        
        # Safe access to related objects
        campaign_name = ad_request.campaign.name if ad_request.campaign else "Unknown Campaign"
        influencer_name = ad_request.target_influencer.username if ad_request.target_influencer else "Unknown Influencer"
        
        # Get influencer details for more context
        influencer_details = None
        if ad_request.target_influencer:
            influencer = ad_request.target_influencer
            influencer_details = {
                "id": influencer.id,
                "username": influencer.username,
                "influencer_name": influencer.influencer_name,
                "category": influencer.category,
                "niche": influencer.niche,
                "reach": influencer.reach
            }
        
        ad_request_data = {
            "id": ad_request.id,
            "campaign_id": ad_request.campaign_id,
            "campaign_name": campaign_name,
            "influencer_id": ad_request.influencer_id,
            "influencer_name": influencer_name,
            "influencer_details": influencer_details,
            "status": ad_request.status,
            "payment_amount": ad_request.payment_amount,
            "payment_amount_formatted": format_currency(ad_request.payment_amount),
            "last_offer_by": ad_request.last_offer_by,
            "requirements": ad_request.requirements,
            "message": ad_request.message,
            "created_at": format_datetime(ad_request.created_at) if ad_request.created_at else None,
            "updated_at": format_datetime(ad_request.updated_at) if ad_request.updated_at else None,
            "created_at_iso": ad_request.created_at.isoformat() if ad_request.created_at else None,
            "updated_at_iso": ad_request.updated_at.isoformat() if ad_request.updated_at else None,
            "negotiation_history": negotiation_history,
            # Add clear negotiation status flags for UI
            "can_respond": ad_request.status == 'Negotiating' and ad_request.last_offer_by == 'influencer',
            "is_active": ad_request.status in ['Pending', 'Negotiating'],
            "is_completed": ad_request.status == 'Accepted',
            "is_rejected": ad_request.status == 'Rejected',
            "currency_symbol": CURRENCY_SYMBOL
        }
        
        return jsonify(ad_request_data), 200
        
    except Exception as e:
        app.logger.error(f"Error in sponsor_get_ad_request: {str(e)}")
        return jsonify({"message": f"An error occurred while fetching the ad request: {str(e)}"}), 500

@app.route('/api/sponsor/ad_requests/<int:ad_request_id>', methods=['PUT']) # Sponsor responds to negotiation
@jwt_required()
@sponsor_required
def sponsor_negotiate_ad_request(ad_request_id):
    sponsor_id = get_jwt_identity()
    ad_request = db.session.get(AdRequest, ad_request_id)
    if not ad_request: return jsonify({"message": "Ad Request not found"}), 404
    if ad_request.campaign.sponsor_id != sponsor_id: return jsonify({"message": "Access denied"}), 403

    # Allow sponsor action if status is 'Pending' OR ('Negotiating' and last offer was by influencer)
    if not ((ad_request.status == 'Pending') or 
            (ad_request.status == 'Negotiating' and ad_request.last_offer_by == 'influencer')):
         return jsonify({"message": "Cannot modify request now or not sponsor's turn"}), 400

    data = request.get_json()
    action = data.get('action') # 'accept' (accept influencer's offer), 'reject', 'negotiate' (counter-offer)

    # Create history record
    history = NegotiationHistory(
        ad_request_id=ad_request.id,
        user_id=sponsor_id,
        user_role='sponsor',
        action='respond' if ad_request.status == 'Pending' else action,
        message=data.get('message'),
        payment_amount=data.get('payment_amount', ad_request.payment_amount),
        requirements=data.get('requirements')
    )
    db.session.add(history)

    if action == 'accept':
        ad_request.status = 'Accepted'
        message = "Offer accepted"
    elif action == 'reject':
        ad_request.status = 'Rejected'
        message = "Offer rejected"
    elif action == 'negotiate':
        # Sponsor makes counter-offer
        new_payment = data.get('payment_amount')
        new_message = data.get('message')
        new_requirements = data.get('requirements') # Allow changing requirements?

        if new_payment is None: return jsonify({"message": "Payment amount required for counter-offer"}), 400
        try: ad_request.payment_amount = float(new_payment)
        except (ValueError, TypeError): return jsonify({"message": "Invalid payment amount"}), 400

        if new_message: ad_request.message = new_message
        if new_requirements: ad_request.requirements = new_requirements # Be careful allowing this

        ad_request.status = 'Negotiating' # Remains negotiating
        ad_request.last_offer_by = 'sponsor'
        message = "Counter-offer sent to influencer"
    else:
        return jsonify({"message": "Invalid action. Use 'accept', 'reject', or 'negotiate'."}), 400

    ad_request.updated_at = datetime.utcnow()
    db.session.commit()
    # Add notification logic later
    return jsonify({"message": message, "ad_request": serialize_ad_request_detail(ad_request)}), 200


@app.route('/api/sponsor/ad_requests/<int:ad_request_id>', methods=['DELETE'])
@jwt_required()
@sponsor_required
def sponsor_delete_ad_request(ad_request_id):
    sponsor_id = get_jwt_identity()
    ad_request = db.session.get(AdRequest, ad_request_id)
    if not ad_request: return jsonify({"message": "Ad Request not found"}), 404
    # Check ownership via campaign
    if ad_request.campaign.sponsor_id != sponsor_id: return jsonify({"message": "Access denied"}), 403
    if ad_request.status not in ['Pending', 'Rejected']: return jsonify({"message": "Cannot delete active request"}), 400

    db.session.delete(ad_request); db.session.commit()
    return jsonify({"message": "Ad Request deleted"}), 200

# == Influencer: Ad Request Management ==
@app.route('/api/influencer/ad_requests', methods=['GET'])
@jwt_required()
@influencer_required
def influencer_get_ad_requests():
    influencer_id = get_jwt_identity()
    status_filter = request.args.get('status')
    query = AdRequest.query.filter_by(influencer_id=influencer_id)
    if status_filter:
        query = query.filter(AdRequest.status == status_filter)
    
    # Join with Campaign and User (sponsor) to get all needed information
    ad_requests = query.join(Campaign, AdRequest.campaign_id == Campaign.id)\
                      .join(User, Campaign.sponsor_id == User.id)\
                      .order_by(AdRequest.updated_at.desc())\
                      .all()
    
    # Process results
    serialized_requests = []
    for req in ad_requests:
        data = serialize_ad_request_detail(req)
        
        # Ensure campaign name is directly accessible
        if 'campaign' in data and data['campaign'].get('name'):
            data['campaign_name'] = data['campaign']['name']
        elif req.campaign:
            data['campaign_name'] = req.campaign.name or 'Unnamed Campaign'
        else:
            data['campaign_name'] = 'Unnamed Campaign'
        
        # Ensure influencer name is directly accessible
        if 'influencer' in data and data['influencer'].get('influencer_name'):
            data['influencer_name'] = data['influencer']['influencer_name']
        elif req.target_influencer:
            data['influencer_name'] = req.target_influencer.influencer_name or req.target_influencer.username
        else:
            data['influencer_name'] = 'Unknown Influencer'
        
        # Ensure dates are available in both formatted and ISO format
        for date_field in ['created_at', 'updated_at']:
            if req.__dict__.get(date_field):
                date_obj = getattr(req, date_field)
                data[f'{date_field}_iso'] = date_obj.isoformat()
                data[date_field] = format_datetime(date_obj)
        
        serialized_requests.append(data)
    
    return jsonify(serialized_requests), 200

@app.route('/api/influencer/ad_requests/<int:ad_request_id>', methods=['PATCH'])
@jwt_required()
@influencer_required
def influencer_action_ad_request(ad_request_id):
    try:
        influencer_id = get_jwt_identity()
        data = request.get_json()
        
        app.logger.info(f"Influencer {influencer_id} attempting action on ad_request {ad_request_id}")
        app.logger.info(f"Received payload: {data}")
        
        # Validate payload
        if not data:
            return jsonify({"message": "No data provided"}), 400
            
        action = data.get('action')
        if not action:
            return jsonify({"message": "Action is required"}), 400
        
        if action not in ['accept', 'reject', 'negotiate']:
            return jsonify({"message": f"Invalid action '{action}'. Use 'accept', 'reject', or 'negotiate'."}), 400
            
        # Find ad request
        ad_request = AdRequest.query.filter_by(id=ad_request_id, influencer_id=influencer_id).first()
        if not ad_request: 
            return jsonify({"message": "Ad Request not found/denied"}), 404
            
        app.logger.info(f"Current ad_request status: {ad_request.status}, last_offer_by: {ad_request.last_offer_by}")
        
        # Check allowed states for action
        allowed_states = ['Pending']
        if ad_request.status == 'Negotiating' and ad_request.last_offer_by == 'sponsor':
            allowed_states.append('Negotiating') # Allow response if sponsor made last offer

        if ad_request.status not in allowed_states:
            return jsonify({
                "message": f"Cannot action request in status '{ad_request.status}' or not influencer's turn",
                "status": ad_request.status,
                "last_offer_by": ad_request.last_offer_by
            }), 400

        # Handle based on action
        if action == 'accept':
            ad_request.status = 'Accepted'
            message = "Ad Request accepted"
        elif action == 'reject':
            ad_request.status = 'Rejected'
            message = "Ad Request rejected"
        elif action == 'negotiate':
            # Influencer makes counter-offer
            new_payment = data.get('payment_amount')
            new_message = data.get('message')
            
            if new_payment is None: 
                return jsonify({"message": "Payment amount required to negotiate"}), 400
                
            try: 
                payment_amount = float(new_payment)
                ad_request.payment_amount = payment_amount
            except (ValueError, TypeError): 
                return jsonify({"message": f"Invalid payment amount: {new_payment}"}), 400

            if new_message: 
                ad_request.message = new_message
                
            ad_request.status = 'Negotiating' # Set/Keep status
            ad_request.last_offer_by = 'influencer'
            message = "Negotiation offer sent to sponsor"

        # Create history record
        history = NegotiationHistory(
            ad_request_id=ad_request.id,
            user_id=influencer_id,
            user_role='influencer',
            action=action,
            message=data.get('message'),
            payment_amount=data.get('payment_amount', ad_request.payment_amount),
            requirements=None  # Influencers don't typically modify requirements
        )
        db.session.add(history)

        ad_request.updated_at = datetime.utcnow()
        db.session.commit()
        
        app.logger.info(f"Action '{action}' successful for ad_request {ad_request_id}")
        
        return jsonify({
            "message": message, 
            "ad_request": serialize_ad_request_detail(ad_request)
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error in influencer_action_ad_request: {str(e)}")
        db.session.rollback()
        return jsonify({"message": f"Server error: {str(e)}"}), 500

# == Influencer: Apply to Public Campaigns ==
@app.route('/api/influencer/campaigns/<int:campaign_id>/apply', methods=['POST'])
@jwt_required()
@influencer_required
def influencer_apply_campaign(campaign_id):
    influencer_id = get_jwt_identity()
    campaign = Campaign.query.filter_by(id=campaign_id, visibility='public').first()
    if not campaign: return jsonify({"message": "Public campaign not found"}), 404

    data = request.get_json()
    requirements = data.get('requirements', "Influencer proposal based on campaign goals.") # Default or require input?
    payment_amount = data.get('payment_amount')
    message = data.get('message', "Interested in collaborating on this campaign.")

    if payment_amount is None: return jsonify({"message": "Proposed payment amount required"}), 400
    try: payment = float(payment_amount)
    except (ValueError, TypeError): return jsonify({"message": "Invalid payment amount"}), 400

    # Check if any request already exists between this influencer and campaign
    existing_request = AdRequest.query.filter_by(
        campaign_id=campaign.id, influencer_id=influencer_id
    ).first()
    if existing_request:
        status_msg = f"You already have an ad request for this campaign (status: {existing_request.status})"
        return jsonify({"message": status_msg, "ad_request_id": existing_request.id}), 409

    ad_request = AdRequest(
        campaign_id=campaign.id, influencer_id=influencer_id, initiator_id=influencer_id, # Influencer initiated
        last_offer_by='influencer', message=message, requirements=requirements,
        payment_amount=payment, status='Pending' # Sponsor needs to accept/reject this application
    )
    db.session.add(ad_request)
    db.session.flush()  # Get the ad_request ID before committing
    
    # Create initial history record
    history = NegotiationHistory(
        ad_request_id=ad_request.id,
        user_id=influencer_id,
        user_role='influencer',
        action='propose',
        message=message,
        payment_amount=payment,
        requirements=requirements
    )
    db.session.add(history)
    
    db.session.commit()
    # Add notification to sponsor later
    return jsonify({"message": "Application submitted successfully", "ad_request": serialize_ad_request_detail(ad_request)}), 201


# == Search Routes ==
@app.route('/api/search/influencers', methods=['GET'])
@jwt_required() # Any logged-in user can search
def search_influencers():
    query = User.query.filter_by(role='influencer', is_active=True, is_flagged=False) # Exclude flagged
    
    # Text search
    if search_query := request.args.get('query'):
        query = query.filter(
            or_(
                User.username.ilike(f'%{search_query}%'),
                User.influencer_name.ilike(f'%{search_query}%'),
                User.category.ilike(f'%{search_query}%'),
                User.niche.ilike(f'%{search_query}%')
            )
        )
    
    # Specific ID search - useful for direct lookup
    if user_id := request.args.get('id'):
        try:
            user_id = int(user_id)
            query = query.filter(User.id == user_id)
        except (ValueError, TypeError):
            pass
    
    # Filters
    if niche := request.args.get('niche'): 
        query = query.filter(User.niche.ilike(f'%{niche}%'))
        
    if category := request.args.get('category'): 
        # Validate the category is in our allowed list
        if category in INFLUENCER_CATEGORIES:
            query = query.filter(User.category == category)
    
    # Reach filters
    if reach_min_str := request.args.get('min_reach'):
        try: 
            query = query.filter(User.reach >= int(reach_min_str))
        except (ValueError, TypeError): 
            pass
            
    if reach_max_str := request.args.get('max_reach'):
        try: 
            query = query.filter(User.reach <= int(reach_max_str))
        except (ValueError, TypeError): 
            pass
    
    # Get limit parameter (default 20, max 50)
    try:
        limit = min(int(request.args.get('limit', 20)), 50)
    except (ValueError, TypeError):
        limit = 20
    
    # Sorting
    sort_by = request.args.get('sort', 'reach')
    if sort_by == 'popularity':
        # Sort by reach (as a popularity proxy) - highest first
        query = query.order_by(User.reach.desc())
    elif sort_by == 'name':
        query = query.order_by(User.influencer_name)
    elif sort_by == 'newest':
        query = query.order_by(User.created_at.desc())
    else:
        # Default sorting by reach
        query = query.order_by(User.reach.desc())
    
    # Execute query with limit
    influencers = query.limit(limit).all()
    
    # Return serialized influencers
    return jsonify([serialize_user_profile(i) for i in influencers]), 200

@app.route('/api/search/campaigns', methods=['GET'])
@jwt_required() # Any logged-in user can search public campaigns
def search_campaigns():
    # Join with User to get sponsor information
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)  # Limit max items
    category = request.args.get('category')
    query = request.args.get('query', '')
    min_budget = request.args.get('min_budget', 0, type=float)
    max_budget = request.args.get('max_budget')
    
    # Build base query - join with User to get sponsor details
    base_q = db.session.query(Campaign, User).join(User, Campaign.sponsor_id == User.id)
    
    # Filter basic requirements:
    # 1. Campaign visibility must be public (unless user is viewing their own campaigns)
    # 2. Campaign should not be flagged (unless user is admin)
    # 3. Sponsor must be approved
    # 4. Sponsor user must be active
    # 5. Campaign dates should make sense (start date <= today)
    
    # Start with basic criteria
    criteria = [
        User.sponsor_approved == True,
        User.is_active == True,
        Campaign.start_date <= datetime.utcnow()
    ]
    
    # Non-admin users shouldn't see flagged campaigns
    if user.role != 'admin':
        criteria.append(Campaign.is_flagged == False)
    
    # Apply visibility filter (sponsors can see their own private campaigns)
    if user.role == 'sponsor':
        # Sponsors see public campaigns OR their own campaigns (including private)
        visibility_filter = or_(Campaign.visibility == 'public', 
                               and_(Campaign.visibility == 'private', Campaign.sponsor_id == user_id))
        criteria.append(visibility_filter)
    else:
        # Regular users only see public campaigns
        criteria.append(Campaign.visibility == 'public')
    
    # Apply additional filters from query params
    if category:
        criteria.append(Campaign.category == category)
    if query:
        criteria.append(or_(
            Campaign.name.ilike(f'%{query}%'),
            Campaign.description.ilike(f'%{query}%')
        ))
    if min_budget:
        criteria.append(Campaign.budget >= min_budget)
    if max_budget:
        criteria.append(Campaign.budget <= float(max_budget))
    
    # Complete the query
    search_query = base_q.filter(and_(*criteria))
    
    # Order and paginate
    search_query = search_query.order_by(Campaign.created_at.desc())
    campaigns_page = search_query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Process results
    campaigns_data = []
    for campaign, sponsor in campaigns_page.items:
        # Use detailed serialization instead of basic to include more fields
        campaign_dict = serialize_campaign_detail(campaign)
        
        # Ensure all required fields are present with fallbacks
        campaign_dict['name'] = campaign_dict.get('name') or campaign.name or 'Unnamed Campaign'
        campaign_dict['description'] = campaign_dict.get('description') or campaign.description or ''
        campaign_dict['budget'] = campaign_dict.get('budget') or campaign.budget or 0
        campaign_dict['sponsor_name'] = sponsor.company_name or sponsor.username or 'Unknown Sponsor'
        campaign_dict['sponsor_id'] = sponsor.id
        
        # Ensure date fields are properly formatted for frontend
        if campaign.start_date:
            campaign_dict['start_date'] = format_date(campaign.start_date)
            campaign_dict['start_date_iso'] = campaign.start_date.isoformat()
        
        if campaign.end_date:
            campaign_dict['end_date'] = format_date(campaign.end_date)
            campaign_dict['end_date_iso'] = campaign.end_date.isoformat()
        
        if campaign.created_at:
            campaign_dict['created_at'] = format_datetime(campaign.created_at)
            campaign_dict['created_at_iso'] = campaign.created_at.isoformat()
        
        campaigns_data.append(campaign_dict)
    
    return jsonify({
        'campaigns': campaigns_data,
        'pagination': serialize_pagination(campaigns_page)
    }), 200

# == ChartJS Data Endpoints ==
@app.route('/api/charts/user-growth', methods=['GET'])
@jwt_required()
@admin_required
def chart_user_growth():
    """Returns time-series data of user registrations for ChartJS"""
    # Get time period from query params (default: last 6 months)
    months = int(request.args.get('months', 6))
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30 * months)
    
    # Query users by role and registration date
    influencers_by_month = db.session.query(
        func.strftime('%Y-%m', User.created_at).label('month'),
        func.count().label('count')
    ).filter(
        User.role == 'influencer',
        User.created_at >= start_date,
        User.created_at <= end_date
    ).group_by('month').order_by('month').all()
    
    sponsors_by_month = db.session.query(
        func.strftime('%Y-%m', User.created_at).label('month'),
        func.count().label('count')
    ).filter(
        User.role == 'sponsor',
        User.created_at >= start_date,
        User.created_at <= end_date
    ).group_by('month').order_by('month').all()
    
    # Generate all months in range (for complete labels even if no data)
    all_months = []
    current = start_date.replace(day=1)
    while current <= end_date:
        all_months.append(current.strftime('%Y-%m'))
        # Move to next month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
    
    # Convert query results to dict for easier lookup
    inf_data = {m: c for m, c in influencers_by_month}
    spo_data = {m: c for m, c in sponsors_by_month}
    
    # Format data for ChartJS
    chart_data = {
        'labels': all_months,
        'datasets': [
            {
                'label': 'Influencers',
                'data': [inf_data.get(m, 0) for m in all_months],
                'borderColor': 'rgba(75, 192, 192, 1)',
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
            },
            {
                'label': 'Sponsors',
                'data': [spo_data.get(m, 0) for m in all_months],
                'borderColor': 'rgba(153, 102, 255, 1)',
                'backgroundColor': 'rgba(153, 102, 255, 0.2)',
            }
        ]
    }
    
    return jsonify(chart_data), 200

@app.route('/api/charts/ad-request-status', methods=['GET'])
@jwt_required()
@admin_required
def chart_ad_request_status():
    """Returns distribution of ad request statuses for ChartJS"""
    # Get counts by status
    status_counts = db.session.query(
        AdRequest.status,
        func.count().label('count')
    ).group_by(AdRequest.status).all()
    
    # Convert to lists for ChartJS
    statuses = [status for status, _ in status_counts]
    counts = [count for _, count in status_counts]
    
    # Prepare data for ChartJS
    chart_data = {
        'labels': statuses,
        'datasets': [{
            'label': 'Ad Requests by Status',
            'data': counts,
            'backgroundColor': [
                'rgba(54, 162, 235, 0.6)',  # Pending - Blue
                'rgba(75, 192, 192, 0.6)',  # Accepted - Green
                'rgba(255, 99, 132, 0.6)',  # Rejected - Red
                'rgba(255, 206, 86, 0.6)',  # Negotiating - Yellow
            ],
            'borderColor': [
                'rgba(54, 162, 235, 1)',
                'rgba(75, 192, 192, 1)',
                'rgba(255, 99, 132, 1)',
                'rgba(255, 206, 86, 1)',
            ],
            'borderWidth': 1
        }]
    }
    
    return jsonify(chart_data), 200

@app.route('/api/charts/campaign-activity', methods=['GET'])
@jwt_required()
@admin_required
def chart_campaign_activity():
    """Returns time-series data of campaign creation and ad requests for ChartJS"""
    # Get time period from query params (default: last 6 months)
    months = int(request.args.get('months', 6))
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30 * months)
    
    # Query campaigns by creation date
    campaigns_by_month = db.session.query(
        func.strftime('%Y-%m', Campaign.created_at).label('month'),
        func.count().label('count')
    ).filter(
        Campaign.created_at >= start_date,
        Campaign.created_at <= end_date
    ).group_by('month').order_by('month').all()
    
    # Query ad requests by creation date
    requests_by_month = db.session.query(
        func.strftime('%Y-%m', AdRequest.created_at).label('month'),
        func.count().label('count')
    ).filter(
        AdRequest.created_at >= start_date,
        AdRequest.created_at <= end_date
    ).group_by('month').order_by('month').all()
    
    # Generate all months in range
    all_months = []
    current = start_date.replace(day=1)
    while current <= end_date:
        all_months.append(current.strftime('%Y-%m'))
        # Move to next month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
    
    # Convert query results to dict for easier lookup
    camp_data = {m: c for m, c in campaigns_by_month}
    req_data = {m: c for m, c in requests_by_month}
    
    # Format data for ChartJS
    chart_data = {
        'labels': all_months,
        'datasets': [
            {
                'label': 'New Campaigns',
                'data': [camp_data.get(m, 0) for m in all_months],
                'borderColor': 'rgba(255, 99, 132, 1)',
                'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                'type': 'line'
            },
            {
                'label': 'Ad Requests',
                'data': [req_data.get(m, 0) for m in all_months],
                'borderColor': 'rgba(54, 162, 235, 1)',
                'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                'type': 'bar'
            }
        ]
    }
    
    return jsonify(chart_data), 200

@app.route('/api/charts/conversion-rates', methods=['GET'])
@jwt_required()
@admin_required
def chart_conversion_rates():
    """Returns conversion rates from ad requests to accepted partnerships"""
    # Get time period from query params (default: last 6 months)
    months = int(request.args.get('months', 6))
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30 * months)
    
    # Group by month and count total requests
    total_by_month = db.session.query(
        func.strftime('%Y-%m', AdRequest.created_at).label('month'),
        func.count().label('count')
    ).filter(
        AdRequest.created_at >= start_date,
        AdRequest.created_at <= end_date
    ).group_by('month').order_by('month').all()
    
    # Group by month and count accepted requests
    accepted_by_month = db.session.query(
        func.strftime('%Y-%m', AdRequest.created_at).label('month'),
        func.count().label('count')
    ).filter(
        AdRequest.created_at >= start_date,
        AdRequest.created_at <= end_date,
        AdRequest.status == 'Accepted'
    ).group_by('month').order_by('month').all()
    
    # Generate all months in range
    all_months = []
    current = start_date.replace(day=1)
    while current <= end_date:
        all_months.append(current.strftime('%Y-%m'))
        # Move to next month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
    
    # Convert query results to dict for easier lookup
    total_data = {m: c for m, c in total_by_month}
    accepted_data = {m: c for m, c in accepted_by_month}
    
    # Calculate conversion rates (as percentage)
    conversion_rates = []
    for month in all_months:
        total = total_data.get(month, 0)
        accepted = accepted_data.get(month, 0)
        rate = (accepted / total * 100) if total > 0 else 0
        conversion_rates.append(round(rate, 1))
    
    # Format data for ChartJS
    chart_data = {
        'labels': all_months,
        'datasets': [{
            'label': 'Conversion Rate (%)',
            'data': conversion_rates,
            'borderColor': 'rgba(75, 192, 192, 1)',
            'backgroundColor': 'rgba(75, 192, 192, 0.2)',
            'borderWidth': 2,
            'fill': False,
            'tension': 0.1
        }]
    }
    
    return jsonify(chart_data), 200

@app.route('/api/charts/dashboard-summary', methods=['GET'])
@jwt_required()
@admin_required
def chart_dashboard_summary():
    """Returns summarized data for dashboard charts"""
    # Get stats for different user types
    total_influencers = User.query.filter_by(role='influencer').count()
    active_influencers = User.query.filter_by(role='influencer', is_active=True).count()
    
    total_sponsors = User.query.filter_by(role='sponsor').count()
    approved_sponsors = User.query.filter_by(role='sponsor', sponsor_approved=True).count()
    
    # Get campaign stats
    public_campaigns = Campaign.query.filter_by(visibility='public').count()
    private_campaigns = Campaign.query.filter_by(visibility='private').count()
    
    # Get ad request stats
    total_requests = AdRequest.query.count()
    accepted_requests = AdRequest.query.filter_by(status='Accepted').count()
    pending_requests = AdRequest.query.filter_by(status='Pending').count()
    rejected_requests = AdRequest.query.filter_by(status='Rejected').count()
    negotiating_requests = AdRequest.query.filter_by(status='Negotiating').count()
    
    # Prepare data for multiple chart types
    chart_data = {
        'userSummary': {
            'labels': ['Active Influencers', 'Inactive Influencers', 'Approved Sponsors', 'Pending Sponsors'],
            'datasets': [{
                'data': [
                    active_influencers,
                    total_influencers - active_influencers,
                    approved_sponsors,
                    total_sponsors - approved_sponsors
                ],
                'backgroundColor': [
                    'rgba(75, 192, 192, 0.6)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(153, 102, 255, 0.6)',
                    'rgba(153, 102, 255, 0.2)'
                ]
            }]
        },
        'campaignVisibility': {
            'labels': ['Public', 'Private'],
            'datasets': [{
                'data': [public_campaigns, private_campaigns],
                'backgroundColor': ['rgba(54, 162, 235, 0.6)', 'rgba(255, 99, 132, 0.6)']
            }]
        },
        'adRequestStatus': {
            'labels': ['Accepted', 'Pending', 'Rejected', 'Negotiating'],
            'datasets': [{
                'data': [accepted_requests, pending_requests, rejected_requests, negotiating_requests],
                'backgroundColor': [
                    'rgba(75, 192, 192, 0.6)',
                    'rgba(54, 162, 235, 0.6)',
                    'rgba(255, 99, 132, 0.6)',
                    'rgba(255, 206, 86, 0.6)'
                ]
            }]
        },
        'conversionRate': {
            'value': 0,  # Default value
            'label': 'Acceptance Rate'
        },
        'currencySymbol': CURRENCY_SYMBOL,
        'timezoneName': 'IST (UTC+5:30)'
    }
    
    # Calculate conversion rate only if there are requests
    if total_requests > 0:
        chart_data['conversionRate']['value'] = round((accepted_requests / total_requests) * 100, 1)
    
    return jsonify(chart_data), 200

# == Negotiation History Endpoints ==
@app.route('/api/ad_requests/<int:ad_request_id>/history', methods=['GET'])
@jwt_required()
def get_negotiation_history(ad_request_id):
    """Get negotiation history for an ad request (available to both parties involved)"""
    user_id = get_jwt_identity()
    user_role = get_jwt().get('role')
    
    # Find the ad request
    ad_request = db.session.get(AdRequest, ad_request_id)
    if not ad_request:
        return jsonify({"message": "Ad request not found"}), 404
    
    # Check if user is authorized to view this history (either the sponsor or the influencer)
    is_sponsor = user_role == 'sponsor' and ad_request.campaign.sponsor_id == user_id
    is_influencer = user_role == 'influencer' and ad_request.influencer_id == user_id
    is_admin = user_role == 'admin'
    
    if not (is_sponsor or is_influencer or is_admin):
        return jsonify({"message": "You are not authorized to view this negotiation history"}), 403
    
    # Get history sorted by creation date
    history = NegotiationHistory.query.filter_by(ad_request_id=ad_request_id).order_by(NegotiationHistory.created_at).all()
    
    # Include ad request details for context
    result = {
        'ad_request': serialize_ad_request_detail(ad_request),
        'history': [serialize_negotiation_history(item) for item in history]
    }
    
    return jsonify(result), 200

@app.route('/api/sponsor/campaigns/<int:campaign_id>/negotiation_summary', methods=['GET'])
@jwt_required()
@sponsor_required
def sponsor_campaign_negotiation_summary(campaign_id):
    """Get summary of negotiations for a sponsor's campaign"""
    sponsor_id = get_jwt_identity()
    
    # Check campaign ownership
    campaign = Campaign.query.filter_by(id=campaign_id, sponsor_id=sponsor_id).first()
    if not campaign:
        return jsonify({"message": "Campaign not found or access denied"}), 404
    
    # Get all ad requests for this campaign
    ad_requests = AdRequest.query.filter_by(campaign_id=campaign_id).all()
    
    # For each ad request, get the latest negotiation history
    results = []
    for ad_request in ad_requests:
        latest_history = NegotiationHistory.query.filter_by(ad_request_id=ad_request.id).order_by(NegotiationHistory.created_at.desc()).first()
        
        if latest_history:
            results.append({
                'ad_request': serialize_ad_request_detail(ad_request),
                'latest_action': {
                    'user_role': latest_history.user_role,
                    'action': latest_history.action,
                    'payment_amount': latest_history.payment_amount,
                    'created_at': latest_history.created_at.isoformat() if latest_history.created_at else None,
                }
            })
    
    return jsonify(results), 200

@app.route('/api/influencer/negotiations', methods=['GET'])
@jwt_required()
@influencer_required
def influencer_negotiations():
    """Get all negotiations the influencer is involved in"""
    influencer_id = get_jwt_identity()
    
    # Get all ad requests where this user is the influencer
    ad_requests = AdRequest.query.filter_by(influencer_id=influencer_id).all()
    
    # For each ad request, get the latest negotiation
    results = []
    for ad_request in ad_requests:
        latest_history = NegotiationHistory.query.filter_by(ad_request_id=ad_request.id).order_by(NegotiationHistory.created_at.desc()).first()
        
        if latest_history:
            results.append({
                'ad_request': serialize_ad_request_detail(ad_request),
                'latest_action': {
                    'user_role': latest_history.user_role,
                    'action': latest_history.action,
                    'payment_amount': latest_history.payment_amount,
                    'created_at': latest_history.created_at.isoformat() if latest_history.created_at else None,
                }
            })
    
    return jsonify(results), 200

# Simple Health Check
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "OK"}), 200


# == Admin Actions (Additions/Modifications) ==

@app.route('/api/admin/users', methods=['GET'])
@jwt_required()
@admin_required
def admin_list_users():
    """List and search users with filters and pagination."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search_term = request.args.get('search', None, type=str)
        role_filter = request.args.get('role', None, type=str)
        flagged_filter = request.args.get('flagged', None, type=str) # 'true' or 'false'
        status_filter = request.args.get('status', None, type=str) # 'active', 'inactive', 'pending_approval', 'approved'

        query = User.query.filter(User.role != 'admin') # Exclude admin itself

        # Apply Filters
        if role_filter and role_filter in ['sponsor', 'influencer']:
            query = query.filter(User.role == role_filter)

        if flagged_filter is not None:
            query = query.filter(User.is_flagged == (flagged_filter.lower() == 'true'))

        if status_filter:
            if status_filter == 'active':
                query = query.filter(User.is_active == True)
            elif status_filter == 'inactive':
                query = query.filter(User.is_active == False)
            elif status_filter == 'pending_approval':
                query = query.filter(User.role == 'sponsor', User.sponsor_approved == False, User.is_active == True)
            elif status_filter == 'approved':
                 query = query.filter(User.role == 'sponsor', User.sponsor_approved == True, User.is_active == True)

        # Apply Search (simple search on username, sponsor/influencer name)
        if search_term:
            search_like = f"%{search_term}%"
            query = query.filter(
                or_(
                    User.username.ilike(search_like),
                    User.company_name.ilike(search_like),
                    User.influencer_name.ilike(search_like)
                )
            )

        # Apply Sorting (optional, e.g., by creation date or username)
        query = query.order_by(User.created_at.desc())

        # Apply Pagination
        pagination = query.paginate(page=page, per_page=per_page, error_out=False) # error_out=False avoids 404 on invalid page [2, 8]

        return jsonify({
            'users': [serialize_user_profile(user) for user in pagination.items],
            'pagination': serialize_pagination(pagination)
        }), 200

    except Exception as e:
        # Log the exception e
        return jsonify({"message": "An error occurred while fetching users."}), 500


@app.route('/api/admin/users/<int:user_id>/deactivate', methods=['PATCH'])
@jwt_required()
@admin_required
def admin_deactivate_user(user_id):
    user = db.session.get(User, user_id)
    if not user or user.role == 'admin':
        return jsonify({"message": "User not found or cannot deactivate admin"}), 404
    if not user.is_active:
         return jsonify({"message": "User already inactive"}), 400

    user.is_active = False
    db.session.commit()
    return jsonify({"message": "User deactivated successfully"}), 200

@app.route('/api/admin/users/<int:user_id>/activate', methods=['PATCH'])
@jwt_required()
@admin_required
def admin_activate_user(user_id):
    user = db.session.get(User, user_id)
    if not user or user.role == 'admin':
        return jsonify({"message": "User not found"}), 404
    if user.is_active:
         return jsonify({"message": "User already active"}), 400

    # Special check for sponsors: only activate if they are approved
    if user.role == 'sponsor' and not user.sponsor_approved:
         return jsonify({"message": "Cannot activate a sponsor whose registration is not approved"}), 400

    user.is_active = True
    db.session.commit()
    return jsonify({"message": "User activated successfully"}), 200


# Keep existing flag/unflag endpoints as they are functionally correct [1]
# @app.route('/api/admin/users/<int:user_id>/flag', methods=['PATCH']) ...
# @app.route('/api/admin/users/<int:user_id>/unflag', methods=['PATCH']) ...


# == Sponsor: Handling Influencer Applications ==

@app.route('/api/sponsor/campaigns/<int:campaign_id>/applications', methods=['GET'])
@jwt_required()
@sponsor_required
def sponsor_get_campaign_applications(campaign_id):
    """Get AdRequests initiated by influencers for a specific campaign."""
    sponsor_id = get_jwt_identity()

    # Verify campaign exists and belongs to the sponsor
    campaign = Campaign.query.filter_by(id=campaign_id, sponsor_id=sponsor_id).first()
    if not campaign:
        return jsonify({"message": "Campaign not found or access denied"}), 404

    # Get filters and pagination params
    status_filter = request.args.get('status', 'Pending') # Default to pending applications
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Query AdRequests for this campaign initiated by influencers
    query = AdRequest.query.filter(
        AdRequest.campaign_id == campaign_id,
        AdRequest.initiator_id == AdRequest.influencer_id # Ensure influencer started it
    )

    if status_filter:
        query = query.filter(AdRequest.status == status_filter)

    query = query.order_by(AdRequest.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'applications': [serialize_ad_request_detail(req) for req in pagination.items],
        'pagination': serialize_pagination(pagination)
    }), 200

@app.route('/api/sponsor/applications/<int:ad_request_id>/accept', methods=['PATCH'])
@jwt_required()
@sponsor_required
def sponsor_accept_application(ad_request_id):
    """Sponsor accepts an influencer's application (AdRequest)."""
    sponsor_id = get_jwt_identity()
    ad_request = db.session.get(AdRequest, ad_request_id)

    if not ad_request:
        return jsonify({"message": "Application (Ad Request) not found"}), 404
    # Verify ownership via campaign
    if ad_request.campaign.sponsor_id != sponsor_id:
        return jsonify({"message": "Access denied"}), 403
    # Verify it's a pending application initiated by the influencer
    if not (ad_request.status == 'Pending' and ad_request.initiator_id == ad_request.influencer_id):
        return jsonify({"message": "Application is not pending or was not initiated by the influencer"}), 400

    ad_request.status = 'Accepted' # Now it's an active agreement
    ad_request.updated_at = datetime.utcnow()

    # Log this action in history
    history = NegotiationHistory(
        ad_request_id=ad_request.id,
        user_id=sponsor_id,
        user_role='sponsor',
        action='accept_application', # Distinguish from accepting a negotiation counter-offer
        message="Sponsor accepted influencer's initial application.",
        payment_amount=ad_request.payment_amount,
        requirements=ad_request.requirements
    )
    db.session.add(history)
    db.session.commit()

    # Add notification logic here if implemented

    return jsonify({
        "message": "Influencer application accepted",
        "ad_request": serialize_ad_request_detail(ad_request)
    }), 200

@app.route('/api/sponsor/applications/<int:ad_request_id>/reject', methods=['PATCH'])
@jwt_required()
@sponsor_required
def sponsor_reject_application(ad_request_id):
    """Sponsor rejects an influencer's application (AdRequest)."""
    sponsor_id = get_jwt_identity()
    ad_request = db.session.get(AdRequest, ad_request_id)

    if not ad_request:
        return jsonify({"message": "Application (Ad Request) not found"}), 404
    # Verify ownership via campaign
    if ad_request.campaign.sponsor_id != sponsor_id:
        return jsonify({"message": "Access denied"}), 403
    # Verify it's a pending application initiated by the influencer
    if not (ad_request.status == 'Pending' and ad_request.initiator_id == ad_request.influencer_id):
        return jsonify({"message": "Application is not pending or was not initiated by the influencer"}), 400

    ad_request.status = 'Rejected'
    ad_request.updated_at = datetime.utcnow()

    # Log this action in history
    history = NegotiationHistory(
        ad_request_id=ad_request.id,
        user_id=sponsor_id,
        user_role='sponsor',
        action='reject_application',
        message="Sponsor rejected influencer's initial application.",
        payment_amount=ad_request.payment_amount,
        requirements=ad_request.requirements
    )
    db.session.add(history)
    db.session.commit()

    # Add notification logic here if implemented

    return jsonify({"message": "Influencer application rejected"}), 200


def serialize_progress_update(update):
    """Serialize a progress update object for API responses"""
    return {
        'id': update.id,
        'ad_request_id': update.ad_request_id,
        'content': update.content,
        'media_urls': update.media_urls.split(',') if update.media_urls else [],
        'metrics_data': update.metrics_data,  # Front-end will parse this JSON
        'status': update.status,
        'feedback': update.feedback,
        'created_at': format_datetime(update.created_at) if update.created_at else None,
        'updated_at': format_datetime(update.updated_at) if update.updated_at else None,
        'created_at_iso': update.created_at.isoformat() if update.created_at else None,
        'updated_at_iso': update.updated_at.isoformat() if update.updated_at else None
    }

def serialize_payment(payment):
    """Serialize a payment object for API responses"""
    return {
        'id': payment.id,
        'ad_request_id': payment.ad_request_id,
        'amount': payment.amount,
        'amount_formatted': format_currency(payment.amount),
        'platform_fee': payment.platform_fee,
        'platform_fee_formatted': format_currency(payment.platform_fee),
        'influencer_amount': payment.influencer_amount,
        'influencer_amount_formatted': format_currency(payment.influencer_amount),
        'status': payment.status,
        'payment_method': payment.payment_method,
        'transaction_id': payment.transaction_id,
        'created_at': format_datetime(payment.created_at) if payment.created_at else None,
        'updated_at': format_datetime(payment.updated_at) if payment.updated_at else None,
        'created_at_iso': payment.created_at.isoformat() if payment.created_at else None,
        'updated_at_iso': payment.updated_at.isoformat() if payment.updated_at else None
    }

# == Influencer: Progress Updates ==
@app.route('/api/influencer/ad_requests/<int:ad_request_id>/progress', methods=['GET'])
@jwt_required()
@influencer_required
def influencer_get_progress_updates(ad_request_id):
    influencer_id = get_jwt_identity()
    ad_request = AdRequest.query.filter_by(id=ad_request_id, influencer_id=influencer_id).first()
    if not ad_request: return jsonify({"message": "Ad Request not found/denied"}), 404
    
    updates = ProgressUpdate.query.filter_by(ad_request_id=ad_request_id).order_by(ProgressUpdate.created_at.desc()).all()
    return jsonify([serialize_progress_update(update) for update in updates]), 200

@app.route('/api/influencer/ad_requests/<int:ad_request_id>/progress', methods=['POST'])
@jwt_required()
@influencer_required
def influencer_add_progress_update(ad_request_id):
    influencer_id = get_jwt_identity()
    app.logger.info(f"Influencer {influencer_id} creating progress update for ad_request {ad_request_id}")
    
    try:
        ad_request = AdRequest.query.filter_by(id=ad_request_id, influencer_id=influencer_id).first()
        if not ad_request: 
            app.logger.warning(f"Ad request not found for influencer {influencer_id}, ad_request {ad_request_id}")
            return jsonify({"message": "Ad Request not found/denied"}), 404
        
        if ad_request.status != 'Accepted': 
            app.logger.warning(f"Cannot add progress update - ad request status is {ad_request.status}, not Accepted")
            return jsonify({"message": "Can only add progress updates for accepted requests"}), 400
        
        data = request.get_json()
        app.logger.info(f"Progress update payload: {data}")
        
        if not data:
            return jsonify({"message": "No data provided"}), 400
            
        if not data.get('content'): 
            return jsonify({"message": "Content is required"}), 400
        
        # Create new progress update
        progress_update = ProgressUpdate(
            ad_request_id=ad_request_id,
            content=data.get('content'),
            media_urls=','.join(data.get('media_urls', [])) if isinstance(data.get('media_urls'), list) else None,
            metrics_data=data.get('metrics_data'),
            status='Pending'  # Explicitly set initial status
        )
        
        db.session.add(progress_update)
        db.session.commit()
        
        app.logger.info(f"Successfully created progress update {progress_update.id} for ad_request {ad_request_id}")
        
        return jsonify({
            "message": "Progress update added successfully",
            "progress_update": serialize_progress_update(progress_update)
        }), 201
        
    except Exception as e:
        app.logger.error(f"Error in influencer_add_progress_update: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

# Add API endpoint for testing Celery integration
@app.route('/api/admin/test/celery', methods=['POST'])
@jwt_required()
@admin_required
def test_celery():
    """Endpoint for testing Celery integration"""
    data = request.get_json()
    email = data.get('email', get_jwt_identity())
    
    # Validate email
    if not email or '@' not in email:
        return jsonify({"error": "Valid email address is required"}), 400
    
    # Send a test email using Celery
    from task import send_test_email
    task = send_test_email.delay(email)
    
    return jsonify({
        "message": "Test task dispatched successfully",
        "task_id": task.id
    }), 202

@app.route('/api/admin/test/reminder', methods=['POST'])
@jwt_required()
@admin_required
def test_minute_reminder():
    """Endpoint for testing the minute reminder Celery task"""
    # Trigger the minute reminder task immediately
    from task import send_minute_test_reminder
    task = send_minute_test_reminder.delay()
    
    return jsonify({
        "message": "Minute reminder test task dispatched successfully",
        "task_id": task.id,
        "note": "Check Mailhog for the test email. The task is also scheduled to run every minute with Celery Beat."
    }), 202

# Add API endpoint for exporting user data
@app.route('/api/admin/export/users', methods=['POST'])
@jwt_required()
@admin_required
def export_users():
    """Trigger a background task to export all users data"""
    admin_id = get_jwt_identity()
    
    # Import and trigger export task
    from task import export_user_data
    task = export_user_data.delay(admin_id)
    
    return jsonify({
        "message": "User export started in background",
        "task_id": task.id,
        "status": "Processing"
    }), 200

# Add API endpoint for checking Celery task status
@app.route('/api/admin/tasks/<task_id>', methods=['GET'])
@jwt_required()
@admin_required
def check_task_status(task_id):
    """Check the status of a background task"""
    from workers import celery
    task = celery.AsyncResult(task_id)
    
    response = {
        "task_id": task_id,
        "status": task.state
    }
    
    if task.state == 'SUCCESS':
        response["result"] = task.result
    elif task.state == 'FAILURE':
        response["error"] = str(task.result)
    
    return jsonify(response), 200

@app.route('/api/admin/test/activity-update', methods=['POST'])
@jwt_required()
@admin_required
def test_activity_update():
    """Endpoint for testing the minute activity update Celery task"""
    # Trigger the minute activity update task immediately
    from user_notifications import send_minute_activity_update
    task = send_minute_activity_update.delay()
    
    return jsonify({
        "message": "Activity update test task dispatched successfully",
        "task_id": task.id,
        "note": "Check Mailhog for the test emails. The task is also scheduled to run every minute with Celery Beat."
    }), 202

@app.route('/api/sponsor/ad_requests/<int:ad_request_id>/payments', methods=['GET'])
@jwt_required()
@sponsor_required
def get_payments(ad_request_id):
    """Get payments for an ad request"""
    sponsor_id = get_jwt_identity()
    
    # Check ad request exists and belongs to the sponsor
    ad_request = db.session.get(AdRequest, ad_request_id)
    if not ad_request:
        return jsonify({"message": "Ad Request not found"}), 404
    
    # Verify ownership via campaign
    if ad_request.campaign.sponsor_id != sponsor_id:
        return jsonify({"message": "Access denied"}), 403
    
    # Get all payments for this ad request
    payments = Payment.query.filter_by(ad_request_id=ad_request_id).order_by(Payment.created_at.desc()).all()
    
    # Serialize payments
    payments_data = [serialize_payment(payment) for payment in payments]
    
    return jsonify(payments_data), 200

@app.route('/api/sponsor/ad_requests/<int:ad_request_id>/payments', methods=['POST'])
@jwt_required()
@sponsor_required
def create_payment(ad_request_id):
    """Create a new payment for an ad request"""
    sponsor_id = get_jwt_identity()
    
    # Check ad request exists and belongs to the sponsor
    ad_request = db.session.get(AdRequest, ad_request_id)
    if not ad_request:
        return jsonify({"message": "Ad Request not found"}), 404
    
    # Verify ownership via campaign
    if ad_request.campaign.sponsor_id != sponsor_id:
        return jsonify({"message": "Access denied"}), 403
    
    # Check if ad request is accepted (only can pay for accepted requests)
    if ad_request.status != 'Accepted':
        return jsonify({"message": "Cannot make payment for non-accepted ad requests"}), 400
    
    # Get payment data
    data = request.get_json()
    if not data:
        return jsonify({"message": "No payment data provided"}), 400
    
    # Validate required fields
    if 'amount' not in data:
        return jsonify({"message": "Payment amount is required"}), 400
        
    if 'payment_type' not in data:
        return jsonify({"message": "Payment type is required"}), 400
        
    # Get amount from data or use full payment amount
    amount = None
    if data['payment_type'] == 'full':
        amount = float(ad_request.payment_amount)
    else:  # partial payment
        try:
            amount = float(data['amount'])
            if amount <= 0:
                return jsonify({"message": "Payment amount must be positive"}), 400
            if amount > ad_request.payment_amount:
                return jsonify({"message": "Partial payment cannot exceed the agreed amount"}), 400
        except (ValueError, TypeError):
            return jsonify({"message": "Invalid payment amount"}), 400
    
    # Calculate platform fees (1% of payment amount)
    platform_fee = amount * 0.01  # 1% fee
    influencer_amount = amount - platform_fee
    
    # Generate simple transaction ID
    transaction_id = f"TXN_{ad_request_id}_{int(time.time())}"
    
    # Create payment record
    payment = Payment(
        ad_request_id=ad_request_id,
        amount=amount,
        platform_fee=platform_fee,
        influencer_amount=influencer_amount,
        status='Completed',
        payment_method='Direct',
        transaction_id=transaction_id,
        payment_response=json.dumps({
            "message": data.get('message', ''),
            "payment_type": data['payment_type']
        })
    )
    
    db.session.add(payment)
    db.session.commit()
    
    # Send email notification to the influencer
    try:
        influencer = User.query.get(ad_request.influencer_id)
        sponsor = User.query.get(sponsor_id)
        
        if influencer and influencer.email:
            email_body = f"""
            Hello {influencer.username},
            
            You have received a payment of {format_currency(amount)} for the campaign "{ad_request.campaign.name}".
            
            Payment Details:
            - Amount: {format_currency(amount)}
            - Platform Fee (1%): {format_currency(platform_fee)}
            - Net Amount: {format_currency(influencer_amount)}
            - Transaction ID: {transaction_id}
            - Date: {format_datetime(datetime.utcnow())}
            
            Message from sponsor: {data.get('message', 'No message provided')}
            
            Thank you for using our platform!
            
            Regards,
            Sponnect Team
            """
            
            # In production, send the actual email
            # send_email(influencer.email, "Payment Received", email_body)
            
            # For now, log it
            app.logger.info(f"Email notification would be sent to {influencer.email}")
    except Exception as e:
        app.logger.error(f"Failed to send email notification: {str(e)}")
    
    return jsonify({
        "payment": serialize_payment(payment),
        "receipt_url": f"/api/sponsor/payments/{payment.id}/receipt"
    }), 201

@app.route('/api/sponsor/payments/<int:payment_id>/receipt', methods=['GET'])
@jwt_required()
def get_payment_receipt(payment_id):
    """Get payment receipt"""
    try:
        user_id = get_jwt_identity()
        
        # Get payment
        payment = db.session.get(Payment, payment_id)
        if not payment:
            return jsonify({"message": "Payment not found", "error": True}), 404
        
        # Get ad request
        ad_request = payment.ad_request
        
        # Check permissions (either the sponsor or influencer can view the receipt)
        if not (ad_request.campaign.sponsor_id == user_id or ad_request.influencer_id == user_id):
            return jsonify({"message": "Access denied", "error": True}), 403
        
        # Get user details
        sponsor = User.query.get(ad_request.campaign.sponsor_id)
        influencer = User.query.get(ad_request.influencer_id)
        
        # Create receipt data
        receipt = {
            "receipt_id": f"RCPT-{payment.id}",
            "transaction_id": payment.transaction_id,
            "date": format_datetime(payment.created_at),
            "campaign_name": ad_request.campaign.name,
            "sponsor_name": sponsor.username if sponsor else "Unknown",
            "influencer_name": influencer.username if influencer else "Unknown",
            "amount": payment.amount,
            "amount_formatted": format_currency(payment.amount),
            "platform_fee": payment.platform_fee,
            "platform_fee_formatted": format_currency(payment.platform_fee),
            "influencer_amount": payment.influencer_amount,
            "influencer_amount_formatted": format_currency(payment.influencer_amount),
            "payment_method": payment.payment_method,
            "status": payment.status
        }
        
        return jsonify(receipt), 200
    except Exception as e:
        app.logger.error(f"Error generating receipt: {str(e)}", exc_info=True)
        return jsonify({"message": f"Error generating receipt: {str(e)}", "error": True}), 500

@app.route('/api/influencer/ad_requests/<int:ad_request_id>/payments', methods=['GET'])
@jwt_required()
@influencer_required
def influencer_get_payments(ad_request_id):
    """Get payments for an ad request (influencer view)"""
    influencer_id = get_jwt_identity()
    
    # Check ad request exists and belongs to the influencer
    ad_request = db.session.get(AdRequest, ad_request_id)
    if not ad_request:
        return jsonify({"message": "Ad Request not found"}), 404
    
    # Verify ownership
    if ad_request.influencer_id != influencer_id:
        return jsonify({"message": "Access denied"}), 403
    
    # Get all payments for this ad request
    payments = Payment.query.filter_by(ad_request_id=ad_request_id).order_by(Payment.created_at.desc()).all()
    
    # Serialize payments
    payments_data = [serialize_payment(payment) for payment in payments]
    
    return jsonify(payments_data), 200

@app.route('/api/sponsor/ad_requests/<int:ad_request_id>/progress', methods=['GET'])
@jwt_required()
@sponsor_required
def sponsor_get_progress_updates(ad_request_id):
    """Get progress updates for an ad request (sponsor view)"""
    sponsor_id = get_jwt_identity()
    
    # Check ad request exists and belongs to the sponsor
    ad_request = db.session.get(AdRequest, ad_request_id)
    if not ad_request:
        return jsonify({"message": "Ad Request not found"}), 404
    
    # Verify ownership via campaign
    if ad_request.campaign.sponsor_id != sponsor_id:
        return jsonify({"message": "Access denied"}), 403
    
    # Get all progress updates for this ad request
    from models import ProgressUpdate
    progress_updates = ProgressUpdate.query.filter_by(ad_request_id=ad_request_id).order_by(ProgressUpdate.created_at.desc()).all()
    
    # Serialize progress updates
    progress_data = [serialize_progress_update(update) for update in progress_updates]
    
    return jsonify(progress_data), 200

@app.route('/api/sponsor/ad_requests/<int:ad_request_id>/progress/<int:update_id>', methods=['PATCH'])
@jwt_required()
@sponsor_required
def sponsor_review_progress_update(ad_request_id, update_id):
    """Review a progress update (sponsor only)"""
    sponsor_id = get_jwt_identity()
    
    # Check ad request exists and belongs to the sponsor
    ad_request = db.session.get(AdRequest, ad_request_id)
    if not ad_request:
        return jsonify({"message": "Ad Request not found"}), 404
    
    # Verify ownership via campaign
    if ad_request.campaign.sponsor_id != sponsor_id:
        return jsonify({"message": "Access denied"}), 403
    
    # Find the progress update
    from models import ProgressUpdate
    update = ProgressUpdate.query.filter_by(id=update_id, ad_request_id=ad_request_id).first()
    if not update:
        return jsonify({"message": "Progress update not found"}), 404
    
    # Check if update is pending (can only review pending updates)
    if update.status != 'Pending':
        return jsonify({"message": "Cannot review non-pending updates"}), 400
    
    # Get action from request data
    data = request.get_json()
    if not data or 'action' not in data:
        return jsonify({"message": "Action is required"}), 400
    
    action = data['action']
    
    # Handle different actions
    if action == 'approve':
        update.status = 'Approved'
    elif action == 'request_revision':
        if 'feedback' not in data or not data['feedback']:
            return jsonify({"message": "Feedback is required for revision requests"}), 400
        
        update.status = 'Revision Requested'
        update.feedback = data['feedback']
    else:
        return jsonify({"message": "Invalid action. Use 'approve' or 'request_revision'"}), 400
    
    update.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        "message": f"Progress update {action}d successfully",
        "update": serialize_progress_update(update)
    }), 200

@app.route('/api/admin/ad_requests/<int:ad_request_id>/flag', methods=['PATCH'])
@jwt_required()
@admin_required
def admin_flag_ad_request(ad_request_id):
    ad_request = db.session.get(AdRequest, ad_request_id)
    if not ad_request: return jsonify({"message": "Ad request not found"}), 404
    ad_request.is_flagged = True
    db.session.commit()
    return jsonify({"message": "Ad request flagged"}), 200

@app.route('/api/admin/ad_requests/<int:ad_request_id>/unflag', methods=['PATCH'])
@jwt_required()
@admin_required
def admin_unflag_ad_request(ad_request_id):
    ad_request = db.session.get(AdRequest, ad_request_id)
    if not ad_request: return jsonify({"message": "Ad request not found"}), 404
    ad_request.is_flagged = False
    db.session.commit()
    return jsonify({"message": "Ad request unflagged"}), 200

@app.route('/api/admin/ad_requests', methods=['GET'])
@jwt_required()
@admin_required
def admin_list_ad_requests():
    """Get list of ad requests with pagination and filtering options"""
    # Parse query parameters
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)  # Cap at 100 items
    
    # Filtering options
    status = request.args.get('status', '')
    flagged = request.args.get('flagged', '').lower() == 'true'
    campaign_id = request.args.get('campaign_id', type=int)
    influencer_id = request.args.get('influencer_id', type=int)
    
    # Build query
    query = AdRequest.query
    
    # Apply filters
    if status:
        query = query.filter(AdRequest.status == status)
    if flagged:
        query = query.filter(AdRequest.is_flagged == True)
    if campaign_id:
        query = query.filter(AdRequest.campaign_id == campaign_id)
    if influencer_id:
        query = query.filter(AdRequest.influencer_id == influencer_id)
    
    # Order by most recent first
    query = query.order_by(AdRequest.created_at.desc())
    
    # Paginate
    ad_requests = query.paginate(page=page, per_page=per_page)
    
    # Return response
    return jsonify({
        'ad_requests': [serialize_ad_request_detail(ar) for ar in ad_requests.items],
        'pagination': serialize_pagination(ad_requests)
    }), 200

@app.route('/api/admin/ad_requests/<int:ad_request_id>', methods=['GET'])
@jwt_required()
@admin_required
def admin_get_ad_request(ad_request_id):
    """Get a specific ad request by ID"""
    ad_request = db.session.get(AdRequest, ad_request_id)
    if not ad_request:
        return jsonify({"message": "Ad request not found"}), 404
    
    return jsonify(serialize_ad_request_detail(ad_request)), 200

@app.route('/api/sponsor/campaigns/<int:campaign_id>/complete', methods=['PATCH'])
@jwt_required()
@sponsor_required
def sponsor_complete_campaign(campaign_id):
    """Mark a campaign as completed by the sponsor."""
    sponsor_id = get_jwt_identity()
    
    # Find the campaign and verify ownership
    campaign = Campaign.query.filter_by(id=campaign_id, sponsor_id=sponsor_id).first()
    if not campaign:
        return jsonify({"message": "Campaign not found or access denied"}), 404
    
    # Only active campaigns can be marked as completed
    if campaign.status != 'active':
        return jsonify({"message": f"Only active campaigns can be marked as completed. Current status: {campaign.status}"}), 400
    
    # Mark as completed
    campaign.status = 'completed'
    db.session.commit()
    
    return jsonify({
        "message": "Campaign marked as completed successfully",
        "campaign": serialize_campaign_detail(campaign)
    }), 200

# Add this function to app.py
def check_and_update_expired_campaigns():
    """Background task to mark campaigns as completed when their end date has passed."""
    now = datetime.utcnow()
    
    # Find active campaigns with end_date in the past
    expired_campaigns = Campaign.query.filter(
        Campaign.status == 'active',
        Campaign.end_date.isnot(None),
        Campaign.end_date < now
    ).all()
    
    completed_count = 0
    for campaign in expired_campaigns:
        campaign.status = 'completed'
        completed_count += 1
    
    if completed_count > 0:
        db.session.commit()
        app.logger.info(f"Auto-completed {completed_count} expired campaigns")
    
    return completed_count

# Import this in task.py and register it as a periodic task
from celery import shared_task

@shared_task
def update_expired_campaigns():
    """Celery task to update expired campaigns to completed status."""
    from app import check_and_update_expired_campaigns
    return check_and_update_expired_campaigns()

@app.route('/api/charts/campaign-distribution', methods=['GET'])
@jwt_required()
@admin_required
def chart_campaign_distribution():
    """Returns distribution of campaigns by category for charts"""
    
    # Query to count campaigns by category
    category_counts = db.session.query(
        Campaign.category, 
        func.count(Campaign.id).label('count')
    ).group_by(Campaign.category).all()
    
    # Create labels and data arrays
    labels = []
    data = []
    background_colors = [
        'rgba(255, 99, 132, 0.6)',
        'rgba(54, 162, 235, 0.6)',
        'rgba(255, 206, 86, 0.6)',
        'rgba(75, 192, 192, 0.6)',
        'rgba(153, 102, 255, 0.6)',
        'rgba(255, 159, 64, 0.6)',
        'rgba(199, 199, 199, 0.6)',
        'rgba(83, 102, 255, 0.6)',
        'rgba(40, 159, 64, 0.6)',
        'rgba(210, 199, 199, 0.6)',
        'rgba(78, 52, 199, 0.6)',
        'rgba(225, 99, 132, 0.6)',
        'rgba(24, 162, 235, 0.6)',
        'rgba(215, 206, 86, 0.6)'
    ]
    
    for category, count in category_counts:
        labels.append(category or 'Uncategorized')
        data.append(count)
    
    # If there are more categories than colors, cycle through colors
    while len(background_colors) < len(labels):
        background_colors.extend(background_colors)
    
    # Limit colors to the number of categories
    background_colors = background_colors[:len(labels)]
    
    # Format data for ChartJS
    chart_data = {
        'labels': labels,
        'datasets': [{
            'label': 'Campaigns by Category',
            'data': data,
            'backgroundColor': background_colors,
            'borderWidth': 1
        }]
    }
    
    return jsonify(chart_data), 200
