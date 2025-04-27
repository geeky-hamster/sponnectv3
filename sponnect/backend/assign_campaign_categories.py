#!/usr/bin/env python
"""
Script to map sponsor industries to categories and update campaigns.

Usage:
    python assign_campaign_categories.py
"""

import os
import sys
from flask import Flask
from models import db, User, Campaign
from constants import INDUSTRY_TO_CATEGORY, DEFAULT_CATEGORY, map_industry_to_category

def assign_campaign_categories():
    """
    Map sponsor industries to categories and update campaigns
    """
    # Get all campaigns
    campaigns = Campaign.query.all()
    print(f"Found {len(campaigns)} campaigns to process")
    
    updated = 0
    skipped = 0
    
    for campaign in campaigns:
        # Get the sponsor for this campaign
        sponsor = User.query.filter_by(id=campaign.sponsor_id).first()
        
        if sponsor and sponsor.industry:
            # Map industry to category
            category = map_industry_to_category(sponsor.industry)
            campaign.category = category
            updated += 1
            print(f"Campaign {campaign.id}: '{campaign.name}' - Industry: '{sponsor.industry}' -> Category: '{category}'")
        else:
            # No sponsor or no industry
            skipped += 1
            if sponsor:
                print(f"Skipped campaign {campaign.id}: '{campaign.name}' - sponsor has no industry")
            else:
                print(f"Skipped campaign {campaign.id}: '{campaign.name}' - sponsor not found")
    
    # Commit changes
    db.session.commit()
    
    print(f"\nUpdated {updated}/{len(campaigns)} campaigns with categories")
    return updated, skipped

if __name__ == "__main__":
    # Setup Flask app context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///sponnect.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        updated, skipped = assign_campaign_categories()
        
        if updated > 0:
            print("Successfully assigned categories based on sponsor industries!")
            sys.exit(0)
        else:
            print("No campaigns were updated. Check if sponsors have industries set.")
            sys.exit(1) 