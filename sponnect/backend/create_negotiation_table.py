# create_negotiation_table.py
from app import app, NegotiationHistory
from models import db

if __name__ == '__main__':
    with app.app_context():
        # Check if table exists
        table_exists = False
        try:
            NegotiationHistory.query.limit(1).all()
            table_exists = True
            print("NegotiationHistory table already exists")
        except:
            print("Creating NegotiationHistory table...")
            db.create_all()
            print("NegotiationHistory table created successfully!") 