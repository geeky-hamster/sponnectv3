#!/usr/bin/env python3
"""
Migration script to add is_flagged field to AdRequest model.
"""
import sys
import os
import sqlite3

def add_flag_field():
    """Add is_flagged field to ad_requests table"""
    try:
        # Get the database path from the environment or use the default
        db_path = os.environ.get('DATABASE_PATH', 'instance/app.db')
        
        # Ensure the full path is resolved
        if not os.path.isabs(db_path):
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), db_path)
        
        print(f"Using database at: {db_path}")
        
        # Connect directly to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(ad_requests)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'is_flagged' not in column_names:
            print("Adding is_flagged column to ad_requests table...")
            cursor.execute('ALTER TABLE ad_requests ADD COLUMN is_flagged BOOLEAN DEFAULT 0 NOT NULL')
            conn.commit()
            print("Migration complete: Added is_flagged field to ad_requests table")
        else:
            print("Column is_flagged already exists in ad_requests table. No migration needed.")
        
        # Verify the number of records
        cursor.execute("SELECT COUNT(*) FROM ad_requests")
        count = cursor.fetchone()[0]
        print(f"Total ad requests in database: {count}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        return False

if __name__ == "__main__":
    success = add_flag_field()
    sys.exit(0 if success else 1) 