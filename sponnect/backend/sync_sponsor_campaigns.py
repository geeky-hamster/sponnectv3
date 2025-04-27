#!/usr/bin/env python
"""
Script to update the Campaign model and add API logic to sync campaign categories with sponsor industries.

Usage:
    python sync_sponsor_campaigns.py
"""

import os
from flask import Flask
from models import db, User, Campaign
from constants import INDUSTRY_TO_CATEGORY, DEFAULT_CATEGORY, map_industry_to_category

def update_profile_handler_code():
    """
    Show the code that should be added to update_profile handler
    """
    code = """
# In the update_profile route handler, after updating the sponsor's industry:
if user.role == 'sponsor' and 'industry' in data:
    new_industry = data['industry']
    
    # Get all campaigns for this sponsor
    campaigns = Campaign.query.filter_by(sponsor_id=user_id).all()
    
    # Update all campaigns with the new category based on industry
    new_category = map_industry_to_category(new_industry)
    for campaign in campaigns:
        campaign.category = new_category
    
    # Commit changes
    db.session.commit()
    """
    
    print("Code to add to update_profile handler:")
    print(code)

def create_campaign_handler_code():
    """
    Show the code that should be added to create_campaign handler
    """
    code = """
# In the sponsor_create_campaign route handler:
# Get sponsor to inherit category based on industry
sponsor = User.query.filter_by(id=sponsor_id).first()
category = map_industry_to_category(sponsor.industry)

campaign = Campaign(
    sponsor_id=sponsor_id, 
    name=data['name'], 
    budget=budget, 
    start_date=start_date,
    end_date=end_date, 
    visibility=data['visibility'], 
    category=category,  # Set category based on sponsor's industry
    description=data.get('description'), 
    goals=data.get('goals')
)
    """
    
    print("\nCode to add to create_campaign handler:")
    print(code)

if __name__ == "__main__":
    # Setup Flask app context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///sponnect.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        # Print code snippets for implementation
        update_profile_handler_code()
        create_campaign_handler_code()
        
        # Ask if the user wants to run the campaign category update now
        answer = input("\nDo you want to update all campaign categories now based on sponsor industries? (y/n): ")
        if answer.lower() == 'y':
            from assign_campaign_categories import assign_campaign_categories
            updated, skipped = assign_campaign_categories()
            print(f"Updated {updated} campaigns, skipped {skipped} campaigns.") 