#!/bin/bash

# Make script executable
chmod +x "$0"

# Set base directory
BASE_DIR=$(dirname "$(readlink -f "$0")")
cd "$BASE_DIR"

# Create necessary directories
echo "Setting up directories..."
python directories.py

# Check if Redis is running
redis-cli ping > /dev/null 2>&1
REDIS_RUNNING=$?

if [ $REDIS_RUNNING -eq 0 ]; then
    echo "Redis is already running."
else
    echo "Redis is not running. Starting Redis..."
    # Try to start Redis (this may require sudo in some environments)
    redis-server &
    sleep 2
    
    # Verify Redis started successfully
    redis-cli ping > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "Redis started successfully."
    else
        echo "WARNING: Failed to start Redis. Please start Redis manually."
        echo "You can do this by running 'redis-server' in a separate terminal."
        read -p "Continue anyway? (y/n): " CONTINUE
        if [[ $CONTINUE != "y" && $CONTINUE != "Y" ]]; then
            echo "Exiting."
            exit 1
        fi
    fi
fi

# Clear terminal
clear

echo "Starting Sponnect services..."
echo "=============================="
echo ""

# Function to start a service in a new terminal
start_service() {
    local name="$1"
    local command="$2"
    
    echo "Starting $name..."
    case "$OSTYPE" in
        linux*)
            # Try different terminal emulators
            if command -v gnome-terminal > /dev/null; then
                gnome-terminal -- bash -c "cd '$BASE_DIR' && $command; exec bash"
            elif command -v xterm > /dev/null; then
                xterm -e "cd '$BASE_DIR' && $command; exec bash" &
            elif command -v konsole > /dev/null; then
                konsole -e "cd '$BASE_DIR' && $command; exec bash" &
            else
                echo "No supported terminal emulator found. Please run manually: $command"
                return 1
            fi
            ;;
        darwin*)
            # macOS
            osascript -e "tell app \"Terminal\" to do script \"cd '$BASE_DIR' && $command\""
            ;;
        msys*|cygwin*|mingw*)
            # Windows/Git Bash
            start cmd /k "cd /d $BASE_DIR && $command"
            ;;
        *)
            echo "Unknown OS. Please run manually: $command"
            return 1
            ;;
    esac
    
    echo "$name started."
    sleep 1
}

# Start Flask application
start_service "Flask App" "python app.py"

# Start Celery worker
start_service "Celery Worker" "celery -A workers.celery worker --loglevel=info"

# Start Celery beat for scheduled tasks
start_service "Celery Beat" "celery -A workers.celery beat --loglevel=info"

echo ""
echo "All services started. Press Ctrl+C to exit."
echo "To stop services, close the terminal windows or use Ctrl+C in each window."
echo ""
echo "Services:"
echo "- Flask: http://localhost:5000"
echo "- Celery worker: See terminal window"
echo "- Celery beat: See terminal window"
echo ""
echo "To test email functionality, ensure Mailhog is running and visit:"
echo "- Mailhog: http://localhost:8025"

# Keep script running
while true; do
    sleep 1
done 