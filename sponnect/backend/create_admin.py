# create_admin.py
from app import app, Config
from models import db, User

if __name__ == '__main__':
    admin_email = Config.ADMIN_EMAIL
    admin_password = Config.ADMIN_PASSWORD

    with app.app_context():
        if not admin_email or not admin_password:
            print("Error: ADMIN_EMAIL/PASSWORD missing in .env")
        elif User.query.filter_by(email=admin_email, role='admin').first():
            print(f"Admin '{admin_email}' already exists.")
        else:
            # Create a username from email prefix if not specified
            admin_username = admin_email.split('@')[0]
            
            admin_user = User(
                username=admin_username,
                email=admin_email, 
                role='admin', 
                is_active=True, 
                sponsor_approved=True
            )
            admin_user.set_password(admin_password)
            db.session.add(admin_user)
            db.session.commit()
            print(f"Admin user '{admin_email}' created with username '{admin_username}'.")
