#!/usr/bin/env python3
"""
Mock Pending Users Generator

This script creates 5 sponsor accounts and 5 influencer accounts 
that are pending approval by an admin. 
For development and testing purposes only.
"""

import os
import sys
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Add the parent directory to sys.path to allow imports from the Flask app
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import Flask app, models and config
from app import app, db
from models import User
from config import Config

# Mock data lists
sponsor_companies = [
    {
        'username': 'acmebrand',
        'email': 'contact@acmebrand.com',
        'company_name': 'Acme Brand Solutions',
        'industry': 'Retail'
    },
    {
        'username': 'techgenius',
        'email': 'marketing@techgenius.com',
        'company_name': 'Tech Genius Labs',
        'industry': 'Technology'
    },
    {
        'username': 'fitlifestyle',
        'email': 'partners@fitlifestyle.com',
        'company_name': 'Fit Lifestyle Co.',
        'industry': 'Health & Fitness'
    },
    {
        'username': 'foodiedelight',
        'email': 'promo@foodiedelight.com',
        'company_name': 'Foodie Delight',
        'industry': 'Food & Beverage'
    },
    {
        'username': 'traveljunkie',
        'email': 'collab@traveljunkie.com',
        'company_name': 'Travel Junkie Adventures',
        'industry': 'Travel'
    }
]

influencer_profiles = [
    {
        'username': 'fashionista',
        'email': 'contact@fashionista.com',
        'influencer_name': 'The Fashion Guru',
        'category': 'Fashion',
        'niche': 'Sustainable Fashion',
        'reach': 45000
    },
    {
        'username': 'techreviewer',
        'email': 'reviews@techguru.com',
        'influencer_name': 'Tech Review Pro',
        'category': 'Technology',
        'niche': 'Smartphone Reviews',
        'reach': 120000
    },
    {
        'username': 'fitnesslover',
        'email': 'workouts@fitnesslife.com',
        'influencer_name': 'Fitness Life Coach',
        'category': 'Fitness',
        'niche': 'Home Workouts',
        'reach': 78000
    },
    {
        'username': 'foodblogger',
        'email': 'recipes@culinaryadventures.com',
        'influencer_name': 'Culinary Adventures',
        'category': 'Food',
        'niche': 'Vegan Cooking',
        'reach': 63000
    },
    {
        'username': 'travelexplorer',
        'email': 'trips@worldadventurer.com',
        'influencer_name': 'World Adventurer',
        'category': 'Travel',
        'niche': 'Budget Travel Tips',
        'reach': 95000
    }
]

def create_mock_pending_users():
    """Create sponsor and influencer users with pending approval status"""
    # Standard password for all test accounts
    standard_password = 'TestPassword123!'
    
    created_count = 0
    
    # Create timestamp range for "recent" registrations
    now = datetime.utcnow()
    recent_times = [now - timedelta(hours=random.randint(1, 24)) for _ in range(10)]
    
    with app.app_context():
        # Check if database already has these mock users to avoid duplicates
        existing_usernames = [u.username for u in User.query.all()]
        
        # Create sponsor accounts
        for i, sponsor in enumerate(sponsor_companies):
            if sponsor['username'] in existing_usernames:
                print(f"Skipping existing username: {sponsor['username']}")
                continue
                
            new_sponsor = User(
                username=sponsor['username'],
                email=sponsor['email'],
                role='sponsor',
                company_name=sponsor['company_name'],
                industry=sponsor['industry'],
                sponsor_approved=None,  # Pending approval
                is_active=True,
                created_at=recent_times[i]
            )
            # Set password using model method
            new_sponsor.set_password(standard_password)
            db.session.add(new_sponsor)
            created_count += 1
            
        # Create influencer accounts
        for i, influencer in enumerate(influencer_profiles):
            if influencer['username'] in existing_usernames:
                print(f"Skipping existing username: {influencer['username']}")
                continue
                
            new_influencer = User(
                username=influencer['username'],
                email=influencer['email'],
                role='influencer',
                influencer_name=influencer['influencer_name'],
                category=influencer['category'],
                niche=influencer['niche'],
                reach=influencer['reach'],
                influencer_approved=None,  # Pending approval
                is_active=True,
                created_at=recent_times[i+5]
            )
            # Set password using model method
            new_influencer.set_password(standard_password)
            db.session.add(new_influencer)
            created_count += 1
            
        # Commit all changes
        db.session.commit()
        
    return created_count

if __name__ == "__main__":
    try:
        count = create_mock_pending_users()
        print(f"Successfully created {count} pending users")
        print("All users have the password: TestPassword123!")
    except Exception as e:
        print(f"Error creating mock users: {str(e)}") 