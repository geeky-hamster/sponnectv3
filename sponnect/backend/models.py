from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

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
    goals = db.Column(db.Text, nullable=True)
    is_flagged = db.Column(db.Boolean, default=False, nullable=False) # For admin flagging
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # Relationships
    sponsor = db.relationship('User', back_populates='campaigns', foreign_keys=[sponsor_id])
    ad_requests = db.relationship('AdRequest', back_populates='campaign', lazy='dynamic',
                                  cascade="all, delete-orphan")

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

# Add Indexes
db.Index('idx_adrequest_campaign_influencer', AdRequest.campaign_id, AdRequest.influencer_id)
db.Index('idx_adrequest_status', AdRequest.status)
db.Index('idx_campaign_sponsor_visibility', Campaign.sponsor_id, Campaign.visibility)



