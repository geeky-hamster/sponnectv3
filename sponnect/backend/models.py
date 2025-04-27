from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.orm import validates
from constants import INDUSTRIES, CATEGORIES, INFLUENCER_CATEGORIES, DEFAULT_CATEGORY

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='influencer', index=True) # 'influencer', 'sponsor', 'admin'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sponsor_approved = db.Column(db.Boolean, nullable=True, default=None) # For sponsors: True/False/None
    influencer_approved = db.Column(db.Boolean, nullable=True, default=None) # For influencers: True/False/None
    is_flagged = db.Column(db.Boolean, default=False, nullable=False) # For admin flagging
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Sponsor specific fields
    company_name = db.Column(db.String(100), nullable=True)
    industry = db.Column(db.String(100), nullable=True)
    # Sponsor budget field removed - Budget is per-campaign

    # Influencer specific fields
    influencer_name = db.Column(db.String(100), nullable=True) # Public Name
    category = db.Column(db.String(50), nullable=True)
    niche = db.Column(db.String(100), nullable=True)
    reach = db.Column(db.Integer, nullable=True, default=0)

    # Relationships
    campaigns = db.relationship('Campaign', back_populates='sponsor', lazy='dynamic',
                                foreign_keys='Campaign.sponsor_id')
    ad_requests_received = db.relationship('AdRequest', back_populates='target_influencer', lazy='dynamic',
                                           foreign_keys='AdRequest.influencer_id')
    ad_requests_initiated = db.relationship('AdRequest', back_populates='initiating_user', lazy='dynamic',
                                           foreign_keys='AdRequest.initiator_id')

    # Simple validation of role and industry values
    @validates('role')
    def validate_role(self, key, role):
        assert role in ['influencer', 'sponsor', 'admin']
        return role
        
    @validates('industry')
    def validate_industry(self, key, industry):
        if industry is not None and industry != '':
            assert industry in INDUSTRIES, f"Invalid industry: {industry}. Must be one of: {', '.join(INDUSTRIES)}"
        return industry
        
    @validates('category')
    def validate_category(self, key, category):
        if category is not None and category != '':
            if self.role == 'influencer':
                assert category in INFLUENCER_CATEGORIES, f"Invalid influencer category: {category}. Must be one of: {', '.join(INFLUENCER_CATEGORIES)}"
        return category

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

class Campaign(db.Model):
    __tablename__ = 'campaigns'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)
    budget = db.Column(db.Float, nullable=False)
    visibility = db.Column(db.String(10), nullable=False, default='private', index=True) # 'public', 'private'
    category = db.Column(db.String(50), nullable=True)  # Match category with sponsor's category
    goals = db.Column(db.Text, nullable=True)
    is_flagged = db.Column(db.Boolean, default=False, nullable=False) # For admin flagging
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # Relationships
    sponsor = db.relationship('User', back_populates='campaigns', foreign_keys=[sponsor_id])
    ad_requests = db.relationship('AdRequest', back_populates='campaign', lazy='dynamic',
                                  cascade="all, delete-orphan")

    @validates('category')
    def validate_category(self, key, category):
        if category is not None and category != '':
            assert category in CATEGORIES, f"Invalid campaign category: {category}. Must be one of: {', '.join(CATEGORIES)}"
        return category
        
    @validates('visibility')
    def validate_visibility(self, key, visibility):
        assert visibility in ['public', 'private']
        return visibility

    def __repr__(self):
        return f'<Campaign {self.name}>'

class AdRequest(db.Model):
    __tablename__ = 'ad_requests'
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False, index=True)
    influencer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True) # Target Influencer
    initiator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True) # User who created/last modified

    message = db.Column(db.Text, nullable=True) # Latest message/note in negotiation
    requirements = db.Column(db.Text, nullable=False)
    payment_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending', index=True) # 'Pending', 'Accepted', 'Rejected', 'Negotiating'
    last_offer_by = db.Column(db.String(20), nullable=True) # 'sponsor' or 'influencer' - tracks negotiation turn
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = db.relationship('Campaign', back_populates='ad_requests', foreign_keys=[campaign_id])
    target_influencer = db.relationship('User', back_populates='ad_requests_received', foreign_keys=[influencer_id])
    initiating_user = db.relationship('User', back_populates='ad_requests_initiated', foreign_keys=[initiator_id])

    def __repr__(self):
        return f'<AdRequest {self.id} Campaign:{self.campaign_id} Status:{self.status}>'

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    ad_request_id = db.Column(db.Integer, db.ForeignKey('ad_requests.id', ondelete='CASCADE'), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    platform_fee = db.Column(db.Float, nullable=False, default=0.0)  # Platform fee (1% of payment amount)
    influencer_amount = db.Column(db.Float, nullable=False, default=0.0)  # Amount after deducting platform fee
    status = db.Column(db.String(20), nullable=False, default='Pending')  # 'Pending', 'Completed', 'Failed'
    payment_method = db.Column(db.String(50), nullable=False, default='Razorpay')
    transaction_id = db.Column(db.String(100), nullable=True)
    payment_response = db.Column(db.Text, nullable=True)  # JSON storage for payment gateway response
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ad_request = db.relationship('AdRequest', backref=db.backref('payments', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Payment {self.id} for AdRequest {self.ad_request_id} Amount:{self.amount} Status:{self.status}>'

class NegotiationHistory(db.Model):
    __tablename__ = 'negotiation_history'
    id = db.Column(db.Integer, primary_key=True)
    ad_request_id = db.Column(db.Integer, db.ForeignKey('ad_requests.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user_role = db.Column(db.String(20), nullable=False)  # 'sponsor' or 'influencer'
    action = db.Column(db.String(20), nullable=False)  # 'propose', 'counter', 'accept', 'reject'
    message = db.Column(db.Text, nullable=True)
    payment_amount = db.Column(db.Float, nullable=True)
    requirements = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    ad_request = db.relationship('AdRequest', backref=db.backref('negotiation_history', lazy='dynamic', cascade='all, delete-orphan'))
    user = db.relationship('User')
    
    def __repr__(self):
        return f'<NegotiationHistory {self.id} AdRequest:{self.ad_request_id} Action:{self.action}>'

class ProgressUpdate(db.Model):
    __tablename__ = 'progress_updates'
    id = db.Column(db.Integer, primary_key=True)
    ad_request_id = db.Column(db.Integer, db.ForeignKey('ad_requests.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    media_urls = db.Column(db.Text, nullable=True)  # Comma-separated URLs of images, videos, etc.
    metrics_data = db.Column(db.Text, nullable=True)  # JSON string of metrics like views, engagement, etc.
    status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Revision Requested
    feedback = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ad_request = db.relationship('AdRequest', backref=db.backref('progress_updates', lazy='dynamic'))
    
    def __repr__(self):
        return f'<ProgressUpdate {self.id} for AdRequest {self.ad_request_id}>'

# Add Indexes
db.Index('idx_adrequest_campaign_influencer', AdRequest.campaign_id, AdRequest.influencer_id)
db.Index('idx_adrequest_status', AdRequest.status)
db.Index('idx_campaign_sponsor_visibility', Campaign.sponsor_id, Campaign.visibility)



