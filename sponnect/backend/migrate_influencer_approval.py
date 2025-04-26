import os
import sys
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from models import db, User

# Get the absolute path to the database
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, 'instance', 'app.db')
db_uri = f'sqlite:///{db_path}'

# Create a minimal Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', db_uri)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with this app
db.init_app(app)

def migrate_influencer_approval():
    """
    Migration script to add influencer_approved field to all existing influencer accounts.
    Sets the field to True for active influencers and False for inactive influencers.
    """
    with app.app_context():
        try:
            # Connect to the database
            print(f"Connecting to database at: {db_path}")
            
            # Check if column already exists
            print("Checking if column exists...")
            column_exists = False
            
            try:
                # Try to query a user with the column to check if it exists
                test_result = db.session.execute(text("SELECT influencer_approved FROM users LIMIT 1")).fetchone()
                column_exists = True
                print("Column 'influencer_approved' already exists.")
            except Exception as e:
                print("Column doesn't exist yet, adding it...")
                
            # Add the column if it doesn't exist
            if not column_exists:
                try:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN influencer_approved BOOLEAN"))
                    db.session.commit()
                    print("Successfully added 'influencer_approved' column to users table.")
                except Exception as e:
                    print(f"Error adding column: {e}")
                    db.session.rollback()
                    raise e
            
            # Now update all influencer records
            influencers = User.query.filter_by(role='influencer').all()
            print(f"Found {len(influencers)} influencer accounts to migrate")
            
            # Direct SQL update for all active influencers
            db.session.execute(
                text("UPDATE users SET influencer_approved = :approved WHERE role = :role AND is_active = :active"),
                {"approved": True, "role": "influencer", "active": True}
            )
            
            # Direct SQL update for all inactive influencers
            db.session.execute(
                text("UPDATE users SET influencer_approved = :approved WHERE role = :role AND is_active = :active"),
                {"approved": False, "role": "influencer", "active": False}
            )
            
            # Commit changes
            db.session.commit()
            print(f"Migration completed successfully. Updated influencer approval status.")
            
            # Verify results
            active_approved = db.session.execute(
                text("SELECT COUNT(*) FROM users WHERE role = :role AND is_active = :active AND influencer_approved = :approved"),
                {"role": "influencer", "active": True, "approved": True}
            ).scalar()
            
            inactive_pending = db.session.execute(
                text("SELECT COUNT(*) FROM users WHERE role = :role AND is_active = :active AND influencer_approved = :approved"),
                {"role": "influencer", "active": False, "approved": False}
            ).scalar()
            
            print(f"Results: {active_approved} active influencers set to approved, {inactive_pending} inactive influencers set as pending")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error during migration: {e}")
            sys.exit(1)

if __name__ == "__main__":
    migrate_influencer_approval() 