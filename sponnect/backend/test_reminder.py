#!/usr/bin/env python3
"""
Test script for the minute reminder Celery task.
This script can be run directly to test the task without using Celery Beat.
"""

import os
import sys
from flask import Flask
from models import db
from task import send_minute_test_reminder

# Create a minimal Flask app for context
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///sponnect.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def test_minute_reminder():
    """Run the minute reminder task directly for testing"""
    with app.app_context():
        result = send_minute_test_reminder()
        print(result)
        print("\nCheck Mailhog for the test email!")

if __name__ == "__main__":
    print("Testing the minute reminder Celery task...")
    test_minute_reminder()
    print("Done!") 