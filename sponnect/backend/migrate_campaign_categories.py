#!/usr/bin/env python
"""
Migration script to add categories to all existing campaigns based on their sponsor's category.
Run this after adding the category field to the Campaign model.

Usage:
    python migrate_campaign_categories.py
"""

import os
import sys
from flask import Flask
from models import db, Campaign, User

def migrate_campaign_categories():
    """
    Update all existing campaigns to inherit their categories from their sponsors.
    """
    # Get all campaigns (don't filter by category as the column was just added)
    campaigns = Campaign.query.all()
    print(f"Found {len(campaigns)} campaigns to process")
    
    updated = 0
    skipped = 0
    
    for campaign in campaigns:
        # Get the sponsor for this campaign
        sponsor = User.query.filter_by(id=campaign.sponsor_id).first()
        
        if sponsor and sponsor.category:
            # Update the campaign with the sponsor's category
            campaign.category = sponsor.category
            updated += 1
            print(f"Updated campaign {campaign.id}: {campaign.name} with category {sponsor.category}")
        else:
            # Skip if sponsor not found or has no category
            skipped += 1
            if sponsor:
                print(f"Skipped campaign {campaign.id}: {campaign.name} - sponsor has no category")
            else:
                print(f"Skipped campaign {campaign.id}: {campaign.name} - sponsor not found")
    
    # Commit all changes
    db.session.commit()
    
    print(f"Migration completed: Updated {updated} campaigns, skipped {skipped} campaigns")
    return updated, skipped

if __name__ == "__main__":
    # Setup Flask app context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        updated, skipped = migrate_campaign_categories()
        
        if updated > 0:
            print("Successfully migrated campaign categories!")
            sys.exit(0)
        else:
            print("No campaigns were updated. Check if they already have categories or if sponsors have categories.")
            sys.exit(1) 