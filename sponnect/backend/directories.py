import os
import sys

def setup_directories():
    """Create necessary directories for the application"""
    # Get the base directory of the app
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Directories to create
    directories = [
        os.path.join(base_dir, 'templates'),
        os.path.join(base_dir, 'templates', 'emails'),
        os.path.join(base_dir, 'exports'),
        os.path.join(base_dir, 'reports')
    ]
    
    # Create each directory if it doesn't exist
    for directory in directories:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                print(f"Created directory: {directory}")
            except Exception as e:
                print(f"Error creating directory {directory}: {str(e)}")
    
    return True

if __name__ == "__main__":
    # Run the setup when the script is executed directly
    setup_directories()
    print("Directory setup complete.") 