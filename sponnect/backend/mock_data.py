#!/usr/bin/env python3
"""
Mock Data Generator for Sponnect Application
This script populates the database with realistic mock data to test all features.
"""

import random
import string
import os
import sys
import json
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy import func
from app import app
from models import db, User, Campaign, AdRequest, NegotiationHistory, ProgressUpdate, Payment
from constants import INDUSTRIES, CATEGORIES, INFLUENCER_CATEGORIES, INDUSTRY_TO_CATEGORY, DEFAULT_CATEGORY

fake = Faker()

# Constants
NUM_ADMINS = 0  # Changed from 1 to 0 to prevent admin creation
NUM_SPONSORS = 10
NUM_INFLUENCERS = 20
NUM_CAMPAIGNS = 30
NUM_AD_REQUESTS = 50
NUM_PROGRESS_UPDATES = 40
NUM_PAYMENTS = 30
NUM_NEGOTIATIONS = 60

# Categories for campaigns - now imported from constants.py
# CATEGORIES = CATEGORIES

# Categories for influencers - now imported from constants.py
# INFLUENCER_CATEGORIES = INFLUENCER_CATEGORIES

NICHES = [
    "Product Reviews", "Tutorials", "Lifestyle", "How-to Guides", 
    "Unboxing", "Challenges", "Vlogs", "Interviews", "Live Events"
]

CAMPAIGN_NAMES = [
    "Summer Collection Launch", "Tech Gadget Review", "New Product Awareness",
    "Holiday Special Promotion", "Brand Ambassador Program", "Influencer Takeover",
    "Product Demo", "Customer Testimonial", "User Experience Showcase", 
    "Limited Edition Release", "Seasonal Campaign", "Wellness Challenge"
]

CAMPAIGN_DESCRIPTIONS = [
    "Promote our new summer collection with authentic content that resonates with your audience.",
    "Review our latest tech gadget and share your honest opinion with your followers.",
    "Help us spread awareness about our new product through creative content.",
    "Create engaging content for our holiday special promotion to drive sales.",
    "Become our brand ambassador and represent our brand values through your content.",
    "Take over our social media for a day and create content that aligns with our brand.",
    "Demonstrate our product features and benefits in an engaging way.",
    "Share your experience using our product or service through your content.",
    "Showcase the user experience of our product or service through your content.",
    "Promote our limited edition release and create exclusivity around it.",
    "Create seasonal content that aligns with our brand message and values.",
    "Participate in our wellness challenge and share your journey with your followers."
]

AD_REQUEST_MESSAGES = [
    "I'm interested in promoting your product to my audience.",
    "Your campaign caught my attention and I think I'd be a great fit.",
    "I believe my followers would love your product.",
    "I have previous experience with similar campaigns and achieved great results.",
    "I'd like to collaborate on this campaign and create engaging content.",
    "My audience demographics match perfectly with your target market.",
    "I have some creative ideas for showcasing your product.",
    "I'm passionate about your industry and would love to partner with you.",
    "My engagement rates are consistently high and would benefit your campaign.",
    "I can create authentic content that resonates with both our audiences."
]

NEGOTIATION_MESSAGES = [
    "Thank you for your offer. I'd like to propose a slightly higher rate due to my engagement metrics.",
    "I appreciate your interest. Let's discuss the deliverables in more detail.",
    "Your offer is reasonable. Can we also include exclusivity terms?",
    "I'm excited about this collaboration. Let's finalize the timeline.",
    "I can offer an additional post if we can adjust the compensation.",
    "The terms look good. I just need clarification on the content approval process.",
    "I'm interested in a longer-term partnership. Can we discuss future opportunities?",
    "Your proposal is close to what I'm looking for. Let's make a few adjustments.",
    "I'm flexible on the deliverables but would need a slightly higher budget.",
    "Let's add a story mention to increase visibility for the campaign."
]

PROGRESS_UPDATE_MESSAGES = [
    "Content creation is underway. Here's a sneak peek of what I'm working on.",
    "Draft content is ready for your review. Please provide feedback.",
    "Post has been scheduled for tomorrow at peak engagement time.",
    "Content is live! Early engagement metrics are looking promising.",
    "Weekly performance update: post has reached 10k impressions so far.",
    "Campaign is performing well with higher than average engagement rates.",
    "Just posted the second deliverable. The audience response is positive.",
    "Final metrics report: campaign exceeded expectations with 20% higher engagement.",
    "Bonus story was added as agreed. Seeing good click-through rates.",
    "All deliverables completed. Let me know if you need any adjustments."
]

def create_random_password():
    """Generate a random secure password."""
    return ''.join(random.choice(string.ascii_letters + string.digits + '!@#$%^&*()') for _ in range(12))

def clear_existing_data():
    """This function has been modified to NOT delete existing data."""
    print("Skipping data clearing - preserving existing database records")
    pass  # Do nothing, preserving existing data

def create_users():
    """Create sponsor and influencer users."""
    users = []
    
    # Admin user creation is skipped due to NUM_ADMINS = 0
    
    # Create sponsor users
    for i in range(NUM_SPONSORS):
        approved = random.choice([True, True, True, False])  # 75% approved
        industry = random.choice(INDUSTRIES)
        sponsor = User(
            username=f"sponsor{i+1}",
            email=f"sponsor{i+1}@example.com",
            role="sponsor",
            is_active=True,
            company_name=fake.company(),
            industry=industry,
            sponsor_approved=approved,
            is_flagged=random.random() < 0.1,  # 10% chance of being flagged
            created_at=datetime.utcnow() - timedelta(days=random.randint(7, 365))
        )
        sponsor.set_password("sponsor123")
        db.session.add(sponsor)
        users.append(sponsor)
    
    # Create influencer users
    for i in range(NUM_INFLUENCERS):
        approved = random.choice([True, True, True, False])  # 75% approved
        influencer = User(
            username=f"influencer{i+1}",
            email=f"influencer{i+1}@example.com",
            role="influencer",
            is_active=True,
            influencer_name=fake.name(),
            category=random.choice(INFLUENCER_CATEGORIES),
            niche=random.choice(NICHES),
            reach=random.randint(1000, 1000000),
            influencer_approved=approved,
            is_flagged=random.random() < 0.1,  # 10% chance of being flagged
            created_at=datetime.utcnow() - timedelta(days=random.randint(7, 365))
        )
        influencer.set_password("influencer123")
        db.session.add(influencer)
        users.append(influencer)
    
    db.session.commit()
    print(f"Created {NUM_SPONSORS} sponsors, and {NUM_INFLUENCERS} influencers")
    return users

def create_campaigns(sponsors):
    """Create campaigns for sponsors."""
    campaigns = []
    
    for i in range(NUM_CAMPAIGNS):
        sponsor = random.choice([s for s in sponsors if s.role == 'sponsor' and s.sponsor_approved])
        
        # Use current dates (2024) instead of future dates
        today = datetime.utcnow()
        # Ensure campaign start dates are in the past or very near future (max 7 days)
        start_date = today - timedelta(days=random.randint(1, 30))
        # End dates should be within 2024, not extending to 2025
        end_date = today + timedelta(days=random.randint(30, min(90, (datetime(today.year, 12, 31) - today).days)))
        
        # Use the industry_to_category mapping for consistency
        campaign_category = INDUSTRY_TO_CATEGORY.get(sponsor.industry, DEFAULT_CATEGORY)
        
        # Use valid campaign status values
        status_choices = ['draft', 'pending_approval', 'active', 'paused', 'completed', 'rejected']
        status = random.choice(status_choices)
        
        campaign = Campaign(
            sponsor_id=sponsor.id,
            name=random.choice(CAMPAIGN_NAMES) + f" {i+1}",
            description=random.choice(CAMPAIGN_DESCRIPTIONS),
            budget=random.randint(5000, 100000),
            goals=fake.paragraph(),
            visibility=random.choice(['public', 'public', 'private']),  # 2/3 public
            category=campaign_category,  # Add category from the sponsor's industry
            status=status,
            start_date=start_date,
            end_date=end_date,
            is_flagged=random.random() < 0.1,  # 10% chance of being flagged
            created_at=today - timedelta(days=random.randint(1, 60))
        )
        db.session.add(campaign)
        campaigns.append(campaign)
    
    db.session.commit()
    print(f"Created {NUM_CAMPAIGNS} campaigns")
    return campaigns

def create_ad_requests(campaigns, influencers):
    """Create ad requests between campaigns and influencers."""
    ad_requests = []
    
    # Get only approved influencers
    approved_influencers = [i for i in influencers if i.role == 'influencer' and i.influencer_approved]
    
    for i in range(NUM_AD_REQUESTS):
        campaign = random.choice(campaigns)
        influencer = random.choice(approved_influencers)
        
        # Randomly determine who initiated the request
        is_sponsor_initiated = random.choice([True, False])
        initiator_id = campaign.sponsor_id if is_sponsor_initiated else influencer.id
        
        # Set random status
        status = random.choice(['Pending', 'Negotiating', 'Accepted', 'Rejected'])
        
        # Set price based on campaign budget (5-15% of budget)
        payment_amount = int(campaign.budget * random.uniform(0.05, 0.15))
        
        # Set last offer by
        last_offer_by = 'sponsor' if is_sponsor_initiated else 'influencer'
        
        # Create an ad request with recent dates
        now = datetime.utcnow()
        created_at = now - timedelta(days=random.randint(1, 30))
        updated_at = created_at + timedelta(days=random.randint(1, min(7, (now - created_at).days)))
        
        ad_request = AdRequest(
            campaign_id=campaign.id,
            influencer_id=influencer.id,
            initiator_id=initiator_id,
            status=status,
            message=random.choice(AD_REQUEST_MESSAGES),
            payment_amount=payment_amount,
            requirements=fake.paragraph(3),
            last_offer_by=last_offer_by,
            is_flagged=random.random() < 0.05,  # 5% chance of being flagged
            created_at=created_at,
            updated_at=updated_at
        )
        db.session.add(ad_request)
        ad_requests.append(ad_request)
    
    db.session.commit()
    print(f"Created {NUM_AD_REQUESTS} ad requests")
    return ad_requests

def create_negotiations(ad_requests):
    """Create negotiation history for ad requests in negotiating status."""
    negotiating_requests = [ar for ar in ad_requests if ar.status in ['Negotiating', 'Accepted']]
    negotiations = []
    
    # For each eligible ad request, create 1-3 negotiation entries
    for ad_request in negotiating_requests:
        n_entries = random.randint(1, 3)
        
        for i in range(n_entries):
            # Alternate between sponsor and influencer
            if i % 2 == 0:
                user_id = ad_request.campaign.sponsor_id
                user_role = 'sponsor'
            else:
                user_id = ad_request.influencer_id
                user_role = 'influencer'
            
            # Select an action based on the scenario
            if i == 0:
                action = 'propose'
            elif i == n_entries - 1 and ad_request.status == 'Accepted':
                action = 'accept'
            else:
                action = random.choice(['counter', 'propose'])
            
            # Adjust payment amount for negotiations
            payment_adjustment = random.uniform(0.9, 1.1)
            payment_amount = ad_request.payment_amount * payment_adjustment
            
            # Create a negotiation history entry with recent dates
            created_at = ad_request.created_at + timedelta(hours=random.randint(1, 24) * (i + 1))
            
            negotiation = NegotiationHistory(
                ad_request_id=ad_request.id,
                user_id=user_id,
                user_role=user_role,
                action=action,
                message=random.choice(NEGOTIATION_MESSAGES),
                payment_amount=payment_amount,
                requirements=ad_request.requirements if random.random() < 0.8 else fake.paragraph(),
                created_at=created_at
            )
            db.session.add(negotiation)
            negotiations.append(negotiation)
    
    db.session.commit()
    print(f"Created {len(negotiations)} negotiation history entries")
    return negotiations

def create_progress_updates(ad_requests):
    """Create progress updates for accepted ad requests."""
    accepted_requests = [ar for ar in ad_requests if ar.status == 'Accepted']
    progress_updates = []
    
    # Create progress updates for each accepted ad request
    for _ in range(min(NUM_PROGRESS_UPDATES, len(accepted_requests))):
        ad_request = random.choice(accepted_requests)
        
        # Generate 1-3 updates per ad request
        n_updates = random.randint(1, 3)
        
        for i in range(n_updates):
            # Determine status based on sequence
            if i == n_updates - 1:
                status = random.choice(['Pending', 'Approved'])
            else:
                status = 'Approved'
            
            # Create sample metrics data
            metrics = {
                'views': random.randint(1000, 50000),
                'likes': random.randint(100, 5000),
                'comments': random.randint(10, 500),
                'shares': random.randint(5, 200),
                'clicks': random.randint(50, 2000)
            }
            
            # Sample media URLs
            media_count = random.randint(0, 3)
            media_urls = []
            for j in range(media_count):
                media_urls.append(f"https://example.com/media/{ad_request.id}/{j+1}.jpg")
            
            # Create a progress update with recent dates
            created_at = ad_request.updated_at + timedelta(days=random.randint(1, 7) * (i + 1))
            if created_at > datetime.utcnow():
                created_at = datetime.utcnow() - timedelta(hours=random.randint(1, 24))
                
            updated_at = created_at + timedelta(hours=random.randint(1, 24))
            if updated_at > datetime.utcnow():
                updated_at = datetime.utcnow()
            
            progress_update = ProgressUpdate(
                ad_request_id=ad_request.id,
                content=random.choice(PROGRESS_UPDATE_MESSAGES),
                media_urls=','.join(media_urls),
                metrics_data=json.dumps(metrics),
                status=status,
                feedback=fake.paragraph() if status == 'Revision Requested' else None,
                created_at=created_at,
                updated_at=updated_at
            )
            db.session.add(progress_update)
            progress_updates.append(progress_update)
    
    db.session.commit()
    print(f"Created {len(progress_updates)} progress updates")
    return progress_updates

def create_payments(ad_requests):
    """Create payments for accepted ad requests."""
    accepted_requests = [ar for ar in ad_requests if ar.status == 'Accepted']
    payments = []
    
    # Create payments for each accepted ad request
    for _ in range(min(NUM_PAYMENTS, len(accepted_requests))):
        ad_request = random.choice(accepted_requests)
        
        # Determine if full or partial payment
        is_full_payment = random.random() < 0.7  # 70% chance of full payment
        
        if is_full_payment:
            amount = ad_request.payment_amount
        else:
            amount = ad_request.payment_amount * random.uniform(0.3, 0.7)
        
        # Calculate platform fee (1% of payment)
        platform_fee = amount * 0.01
        influencer_amount = amount - platform_fee
        
        # Generate a transaction ID
        transaction_id = f"TXN_{ad_request.id}_{int(datetime.utcnow().timestamp())}"
        
        # Create a payment response
        payment_response = {
            'status': 'success',
            'message': 'Payment processed successfully',
            'transaction_id': transaction_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Create payment with recent dates
        created_at = ad_request.updated_at + timedelta(days=random.randint(1, 14))
        if created_at > datetime.utcnow():
            created_at = datetime.utcnow() - timedelta(hours=random.randint(1, 24))
            
        updated_at = created_at + timedelta(hours=random.randint(1, 24))
        if updated_at > datetime.utcnow():
            updated_at = datetime.utcnow()
        
        payment = Payment(
            ad_request_id=ad_request.id,
            amount=amount,
            platform_fee=platform_fee,
            influencer_amount=influencer_amount,
            status='Completed',
            payment_method=random.choice(['Direct', 'Credit Card', 'UPI', 'Bank Transfer']),
            transaction_id=transaction_id,
            payment_response=json.dumps(payment_response),
            created_at=created_at,
            updated_at=updated_at
        )
        db.session.add(payment)
        payments.append(payment)
    
    db.session.commit()
    print(f"Created {len(payments)} payments")
    return payments

def main():
    """Main function to generate mock data."""
    with app.app_context():
        print("Starting mock data generation...")
        
        # Check if data already exists
        user_count = db.session.query(func.count(User.id)).scalar()
        if user_count > 1:  # Account for admin
            print(f"Database already contains {user_count} users")
            response = input("Do you want to skip data generation? (y/n): ")
            if response.lower() == 'y':
                print("Skipping mock data generation")
                return
            
            response = input("Do you want to clear existing data before generating new data? (y/n): ")
            if response.lower() == 'y':
                print("Clearing existing data...")
                db.session.query(Payment).delete()
                db.session.query(ProgressUpdate).delete()
                db.session.query(NegotiationHistory).delete()
                db.session.query(AdRequest).delete()
                db.session.query(Campaign).delete()
                db.session.query(User).filter(User.role != 'admin').delete()
                db.session.commit()
                print("Existing data cleared")
            else:
                print("Will add data to existing records")
                clear_existing_data()
        
        # Create users
        users = create_users()
        
        # Filter out approved sponsors and influencers
        sponsors = [u for u in users if u.role == 'sponsor']
        influencers = [u for u in users if u.role == 'influencer']
        
        # Create campaigns
        campaigns = create_campaigns(sponsors)
        
        # Create ad requests
        ad_requests = create_ad_requests(campaigns, influencers)
        
        # Create negotiations
        create_negotiations(ad_requests)
        
        # Create progress updates
        create_progress_updates(ad_requests)
        
        # Create payments
        create_payments(ad_requests)
        
        print("Mock data generation complete!")

if __name__ == '__main__':
    main() 