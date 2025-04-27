#!/usr/bin/env python
"""
Migration script to add the category column to the campaigns table.
Run this before running migrate_campaign_categories.py.

Usage:
    python add_category_column.py
"""

import os
import sys
from flask import Flask
from models import db
from sqlalchemy import text

def add_category_column():
    """
    Add the category column to the campaigns table.
    """
    try:
        # Execute raw SQL to add the column
        db.session.execute(text("ALTER TABLE campaigns ADD COLUMN category VARCHAR(50)"))
        db.session.commit()
        print("Successfully added category column to campaigns table")
        return True
    except Exception as e:
        print(f"Error adding category column: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    # Setup Flask app context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        success = add_category_column()
        if success:
            sys.exit(0)
        else:
            sys.exit(1) 