#!/usr/bin/env python3
"""
Debug script to test the ad request creation process
"""

from app import app, db
from models import User, Campaign, AdRequest, NegotiationHistory
import sys

def test_ad_request_creation(campaign_id=1, influencer_id=7):
    """Test the ad request creation process step by step"""
    print(f"Testing ad request creation for campaign ID {campaign_id} and influencer ID {influencer_id}...")
    
    with app.app_context():
        # 1. Check if campaign exists
        campaign = Campaign.query.filter_by(id=campaign_id).first()
        if not campaign:
            print("Campaign not found!")
            return
        
        print(f"Found campaign: {campaign.name}")
        
        # 2. Check if influencer exists and meets criteria
        influencer = User.query.filter_by(
            id=influencer_id, 
            role='influencer', 
            is_active=True,
            influencer_approved=True,
            is_flagged=False
        ).first()
        
        if not influencer:
            print("Influencer not found or doesn't meet criteria!")
            return
            
        print(f"Found influencer: {influencer.username}")
        
        # 3. Check if request already exists
        existing_request = AdRequest.query.filter_by(
            campaign_id=campaign.id,
            influencer_id=influencer.id
        ).first()
        
        if existing_request:
            print(f"Request already exists with status: {existing_request.status}")
            return
            
        # 4. Try creating the ad request
        try:
            ad_request = AdRequest(
                campaign_id=campaign.id, 
                influencer_id=influencer.id, 
                initiator_id=campaign.sponsor_id, 
                last_offer_by='sponsor',
                message="Test message", 
                requirements="Test requirements", 
                payment_amount=1000, 
                status='Pending'
            )
            db.session.add(ad_request)
            db.session.flush()  # Get the ad_request ID before committing
            
            print(f"Created AdRequest with ID: {ad_request.id}")
            
            # 5. Create initial history record
            history = NegotiationHistory(
                ad_request_id=ad_request.id,
                user_id=campaign.sponsor_id,
                user_role='sponsor',
                action='propose',
                message="Test message",
                payment_amount=1000,
                requirements="Test requirements"
            )
            db.session.add(history)
            
            # Commit both objects
            db.session.commit()
            print("Successfully created ad request and history record!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating ad request: {e}")

if __name__ == "__main__":
    # Get command line arguments if provided
    campaign_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    influencer_id = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    test_ad_request_creation(campaign_id, influencer_id) 