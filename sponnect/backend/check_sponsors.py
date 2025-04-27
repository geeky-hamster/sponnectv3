#!/usr/bin/env python
"""
Script to check if sponsors have industries set.

Usage:
    python check_sponsors.py
"""

import os
from flask import Flask
from models import db, User

def check_sponsors():
    """
    Check if sponsors have industries set
    """
    sponsors = User.query.filter_by(role='sponsor').all()
    print(f"Found {len(sponsors)} sponsors")
    
    sponsors_with_industry = 0
    
    for sponsor in sponsors:
        print(f"Sponsor ID: {sponsor.id}, Name: {sponsor.username}, Industry: {sponsor.industry}")
        if sponsor.industry:
            sponsors_with_industry += 1
    
    print(f"\nTotal sponsors with industry: {sponsors_with_industry}/{len(sponsors)}")

if __name__ == "__main__":
    # Setup Flask app context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        check_sponsors() 