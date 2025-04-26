#!/bin/bash

echo "Running migration to add influencer_approved field to existing records..."
python3 migrate_influencer_approval.py

echo "Migration complete." 