"""
Script to run all migrations
"""

def run_migrations():
    """
    Run all migration scripts in the correct order
    """
    print("Starting database migrations...")
    
    # Import and run migrations in order
    try:
        print("\n1. Adding campaign status field")
        from add_campaign_status_field import run_migration as add_campaign_status_field
        add_campaign_status_field()
        
        # Add other migrations here in order
        
        print("\nAll migrations completed successfully.")
    except Exception as e:
        print(f"\nError during migration: {e}")
        raise

if __name__ == "__main__":
    run_migrations() 