#!/usr/bin/env python3
"""
Debug script to test the problematic influencer query
"""

from app import app
from models import User, db

def test_query_with_flag_condition():
    """Test the influencer query with is_flagged condition"""
    print("Testing query with is_flagged=False condition...")
    
    with app.app_context():
        # Get all influencers
        all_influencers = User.query.filter_by(role='influencer').all()
        print(f"Total influencers: {len(all_influencers)}")
        
        # Try the query with only approved condition
        approved_influencers = User.query.filter_by(
            role='influencer', 
            is_active=True,
            influencer_approved=True
        ).all()
        print(f"Active, approved influencers: {len(approved_influencers)}")
        
        # Now try with the is_flagged condition
        approved_not_flagged = User.query.filter_by(
            role='influencer', 
            is_active=True,
            influencer_approved=True,
            is_flagged=False
        ).all()
        print(f"Active, approved, not flagged influencers: {len(approved_not_flagged)}")
        
        # Check data for a sample influencer
        if all_influencers:
            sample = all_influencers[0]
            print(f"\nSample influencer (ID: {sample.id}):")
            print(f"- Username: {sample.username}")
            print(f"- Is active: {sample.is_active}")
            print(f"- Approved: {sample.influencer_approved}")
            print(f"- Is flagged: {sample.is_flagged}")

if __name__ == "__main__":
    test_query_with_flag_condition() 