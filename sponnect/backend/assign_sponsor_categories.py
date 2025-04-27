#!/usr/bin/env python
"""
Script to assign categories to sponsors.

Usage:
    python assign_sponsor_categories.py
"""

import os
import random
from flask import Flask
from models import db, User

# Define categories to match what's in frontend
CATEGORIES = [
    'beauty',
    'fashion',
    'food',
    'technology',
    'travel',
    'gaming',
    'fitness',
    'other'
]

def assign_sponsor_categories():
    """
    Assign random categories to sponsors without categories
    """
    sponsors = User.query.filter_by(role='sponsor').all()
    print(f"Found {len(sponsors)} sponsors")
    
    updated = 0
    
    for sponsor in sponsors:
        if not sponsor.category:
            # Assign a random category
            sponsor.category = random.choice(CATEGORIES)
            print(f"Assigned category '{sponsor.category}' to sponsor {sponsor.id}: {sponsor.username}")
            updated += 1
    
    # Commit changes
    db.session.commit()
    
    print(f"\nUpdated {updated}/{len(sponsors)} sponsors with categories")
    return updated

if __name__ == "__main__":
    # Setup Flask app context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        assign_sponsor_categories() 