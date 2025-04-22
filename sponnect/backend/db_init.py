# db_init.py
from app import app
from flask_migrate import Migrate, init, migrate, upgrade
from models import db

if __name__ == '__main__':
    with app.app_context():
        # Init migrations directory
        init()
        # Create initial migration
        migrate(message='Initial migration')
        # Apply migration
        upgrade()
        print("Database initialized successfully!") 