"""
Standalone script to check for expired campaigns and mark them as completed
"""
from flask import Flask
from datetime import datetime, UTC
from config import Config
import sys
import os

# Add the parent directory to sys.path to ensure imports work
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Create a minimal Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Import models after creating the app but before creating SQLAlchemy
from models import db, Campaign

# Initialize app with the SQLAlchemy instance imported from models
db.init_app(app)

def update_expired_campaigns():
    """Find campaigns with end dates in the past and mark them as completed"""
    with app.app_context():
        try:
            # Using timezone-aware UTC now
            now = datetime.now(UTC)
            
            # Find active campaigns with end_date in the past
            expired_campaigns = Campaign.query.filter(
                Campaign.status == 'active',
                Campaign.end_date.isnot(None),
                Campaign.end_date < now
            ).all()
            
            if not expired_campaigns:
                print("No expired campaigns found.")
                return
            
            # Update status to completed
            completed_count = 0
            for campaign in expired_campaigns:
                print(f"Marking campaign '{campaign.name}' (ID: {campaign.id}) as completed. End date: {campaign.end_date}")
                campaign.status = 'completed'
                completed_count += 1
            
            db.session.commit()
            print(f"Successfully marked {completed_count} expired campaigns as completed.")
        except Exception as e:
            db.session.rollback()
            print(f"Error updating expired campaigns: {e}")

if __name__ == "__main__":
    update_expired_campaigns() 