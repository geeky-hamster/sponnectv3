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

# Industries for sponsors
CATEGORIES = [
    "Technology", "Fashion", "Cosmetics", "Food & Beverage", "Travel", 
    "Gaming", "Health & Fitness", "Automotive", "Finance", "Art", 
    "Entertainment", "Education", "Home & Decor", "Sports", "Media", "Retail"
]

# Categories for influencers
INFLUENCER_CATEGORIES = [
    "Fashion", "Beauty", "Fitness", "Travel", "Food", "Technology", 
    "Gaming", "Lifestyle", "Business", "Education", "Entertainment", 
    "Health", "Sports", "Parenting", "Other"
]

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
        sponsor = User(
            username=f"sponsor{i+1}",
            email=f"sponsor{i+1}@example.com",
            role="sponsor",
            is_active=True,
            company_name=fake.company(),
            industry=random.choice(CATEGORIES),
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
        
        start_date = datetime.utcnow() + timedelta(days=random.randint(7, 30))
        end_date = start_date + timedelta(days=random.randint(30, 90))
        
        campaign = Campaign(
            sponsor_id=sponsor.id,
            name=random.choice(CAMPAIGN_NAMES) + f" {i+1}",
            description=random.choice(CAMPAIGN_DESCRIPTIONS),
            budget=random.randint(5000, 100000),
            goals=fake.paragraph(),
            visibility=random.choice(['public', 'public', 'private']),  # 2/3 public
            start_date=start_date,
            end_date=end_date,
            is_flagged=random.random() < 0.1,  # 10% chance of being flagged
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 60))
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
        
        ad_request = AdRequest(
            campaign_id=campaign.id,
            influencer_id=influencer.id,
            initiator_id=initiator_id,
            status=status,
            message=random.choice(AD_REQUEST_MESSAGES),
            payment_amount=payment_amount,
            requirements=fake.paragraph(3),
            last_offer_by=last_offer_by,
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
            updated_at=datetime.utcnow() - timedelta(days=random.randint(0, 7))
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
            user_role = 'sponsor' if i % 2 == 0 else 'influencer'
            user_id = ad_request.campaign.sponsor_id if user_role == 'sponsor' else ad_request.influencer_id
            
            # Adjust price slightly
            price_adjustment = random.uniform(0.9, 1.1)
            payment_amount = int(ad_request.payment_amount * price_adjustment)
            
            # Determine action type
            action = random.choice(['propose', 'counter']) if i < n_entries - 1 else 'accept'
            
            negotiation = NegotiationHistory(
                ad_request_id=ad_request.id,
                user_id=user_id,
                user_role=user_role,
                action=action,
                message=random.choice(NEGOTIATION_MESSAGES),
                payment_amount=payment_amount,
                requirements=fake.paragraph(2) if random.random() > 0.5 else None,
                created_at=ad_request.created_at + timedelta(days=i+1)
            )
            db.session.add(negotiation)
            negotiations.append(negotiation)
            
            # Update ad request with the latest proposed price
            if i == n_entries - 1:
                ad_request.payment_amount = payment_amount
                ad_request.last_offer_by = user_role
    
    db.session.commit()
    print(f"Created {len(negotiations)} negotiation history entries")
    return negotiations

def create_progress_updates(ad_requests):
    """Create progress updates for accepted ad requests."""
    eligible_requests = [ar for ar in ad_requests if ar.status == 'Accepted']
    progress_updates = []
    
    for _ in range(NUM_PROGRESS_UPDATES):
        if not eligible_requests:
            break
            
        ad_request = random.choice(eligible_requests)
        
        # Generate 1-3 fake image URLs
        num_images = random.randint(0, 3)
        media_urls = ','.join([fake.image_url() for _ in range(num_images)]) if num_images > 0 else None
        
        # Generate fake metrics as JSON
        metrics = {
            'views': random.randint(1000, 100000),
            'likes': random.randint(100, 10000),
            'comments': random.randint(10, 1000),
            'shares': random.randint(5, 500),
            'clicks': random.randint(50, 5000)
        }
        
        progress_update = ProgressUpdate(
            ad_request_id=ad_request.id,
            content=random.choice(PROGRESS_UPDATE_MESSAGES),
            media_urls=media_urls,
            metrics_data=json.dumps(metrics),
            status=random.choice(['Pending', 'Approved', 'Revision Requested']),
            feedback=fake.paragraph() if random.random() > 0.7 else None,
            created_at=ad_request.updated_at + timedelta(days=random.randint(1, 10)),
            updated_at=ad_request.updated_at + timedelta(days=random.randint(1, 10))
        )
        db.session.add(progress_update)
        progress_updates.append(progress_update)
    
    db.session.commit()
    print(f"Created {len(progress_updates)} progress updates")
    return progress_updates

def create_payments(ad_requests):
    """Create payments for completed ad requests."""
    completed_requests = [ar for ar in ad_requests if ar.status == 'Accepted']
    payments = []
    
    for ad_request in completed_requests:
        if random.random() > 0.8:  # 80% of accepted requests have payments
            continue
            
        # Calculate platform fee (5-10% of payment amount)
        platform_fee = int(ad_request.payment_amount * random.uniform(0.05, 0.1))
        payment_amount = ad_request.payment_amount
        influencer_amount = payment_amount - platform_fee
        
        # Generate fake transaction ID
        transaction_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=15))
        
        # Generate fake payment response
        payment_response = json.dumps({
            'payment_id': transaction_id,
            'order_id': f"order_{transaction_id}",
            'signature': ''.join(random.choices(string.ascii_letters + string.digits, k=30)),
            'status': 'captured',
            'method': random.choice(['card', 'netbanking', 'wallet', 'upi']),
            'amount': payment_amount * 100,  # In paise
            'currency': 'INR',
            'timestamp': datetime.utcnow().isoformat()
        })
        
        payment = Payment(
            ad_request_id=ad_request.id,
            amount=payment_amount,
            platform_fee=platform_fee,
            influencer_amount=influencer_amount,
            status='Completed',
            payment_method=random.choice(['Razorpay', 'Bank Transfer', 'Wallet']),
            transaction_id=transaction_id,
            payment_response=payment_response,
            created_at=ad_request.updated_at + timedelta(days=random.randint(1, 3)),
            updated_at=ad_request.updated_at + timedelta(days=random.randint(1, 7))
        )
        db.session.add(payment)
        payments.append(payment)
    
    db.session.commit()
    print(f"Created {len(payments)} payments")
    return payments

def main():
    """Main function to generate mock data."""
    with app.app_context():
        try:
            clear_existing_data()  # This now does nothing but print a message
            users = create_users()
            sponsors = [u for u in users if u.role == 'sponsor']
            influencers = [u for u in users if u.role == 'influencer']
            
            campaigns = create_campaigns(sponsors)
            ad_requests = create_ad_requests(campaigns, influencers)
            negotiations = create_negotiations(ad_requests)
            progress_updates = create_progress_updates(ad_requests)
            payments = create_payments(ad_requests)
            
            # Calculate total monetary values
            total_campaign_budget = sum(c.budget for c in campaigns)
            total_payments = sum(p.amount for p in payments)
            total_platform_fees = sum(p.platform_fee for p in payments)
            
            # Print summary
            print("\nMock Data Generation Summary:")
            print(f"- {NUM_SPONSORS} Sponsor users (username: sponsor1, password: sponsor123)")
            print(f"- {NUM_INFLUENCERS} Influencer users (username: influencer1, password: influencer123)")
            print(f"- {len(campaigns)} Campaigns (Total budget: ₹{total_campaign_budget:,.2f})")
            print(f"- {len(ad_requests)} Ad Requests")
            print(f"- {len(negotiations)} Negotiation Messages")
            print(f"- {len(progress_updates)} Progress Updates")
            print(f"- {len(payments)} Payments (Total: ₹{total_payments:,.2f}, Platform fees: ₹{total_platform_fees:,.2f})")
            
            print("\nMock data generated successfully! All currency values are in Indian Rupees (₹)")
            print("Note: Existing database records were preserved")
            
        except Exception as e:
            print(f"Error generating mock data: {e}")
            db.session.rollback()
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 