#!/usr/bin/env python3
# init_db.py
from app import app, db
from models import User

if __name__ == '__main__':
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        print("Database tables created successfully!")
        
        # Check if admin user already exists
        admin_email = "admin@sponnect.com"
        if not User.query.filter_by(email=admin_email).first():
            # Create admin user
            admin = User(
                username="admin",
                email=admin_email,
                role="admin",
                is_active=True,
                sponsor_approved=True
            )
            admin.set_password("admin123")  # Simple password for testing
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user '{admin_email}' created with password 'admin123'")
        else:
            print(f"Admin user '{admin_email}' already exists") 