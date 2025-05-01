"""
Standalone script to add the status field to the campaigns table
"""
from flask import Flask
from sqlalchemy.sql import text
from config import Config
import sys
import os

# Add the parent directory to sys.path to ensure imports work
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Create a minimal Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Import models after creating the app
from models import db

# Initialize app with the SQLAlchemy instance imported from models
db.init_app(app)

def update_campaigns_table():
    """Add status column to campaigns table if it doesn't exist"""
    with app.app_context():
        # Check if status column exists using SQLite's PRAGMA
        check_query = text("PRAGMA table_info(campaigns)")
        result = db.session.execute(check_query).fetchall()
        
        # Check if the status column exists in the result
        status_exists = any(row[1] == 'status' for row in result)
        
        if not status_exists:
            print("Adding status column to campaigns table...")
            
            try:
                # Add column with default value 'active'
                add_column_query = text("ALTER TABLE campaigns ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'active'")
                db.session.execute(add_column_query)
                
                # SQLite doesn't support adding an index in the same transaction as ALTER TABLE
                db.session.commit()
                
                # Add index for better query performance
                add_index_query = text("CREATE INDEX IF NOT EXISTS idx_campaign_status ON campaigns (status)")
                db.session.execute(add_index_query)
                
                db.session.commit()
                print("Status column added successfully to campaigns table.")
            except Exception as e:
                db.session.rollback()
                print(f"Error adding status column: {e}")
        else:
            print("Status column already exists in campaigns table. No changes made.")

if __name__ == "__main__":
    update_campaigns_table() 