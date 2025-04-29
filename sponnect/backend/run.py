#!/usr/bin/env python3
"""
Comprehensive application launcher for Sponnect
Launches all required services in separate terminals:
- Redis server
- Celery worker
- Celery beat
- Flask backend
- Frontend (Vite dev server)
- Mailhog (for email testing)

This script works in Linux environments and attempts to use
VSCode terminals as first preference if available.
"""

import os
import sys
import subprocess
import platform
import time
import shutil
import signal
import json
from pathlib import Path

# Base directories
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BACKEND_DIR))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'sponnect', 'frontend')

# Process list to keep track of launched processes
processes = []

# Terminal detection and configuration
def is_vscode_terminal():
    """Check if we're running in a VSCode terminal"""
    return 'TERM_PROGRAM' in os.environ and os.environ['TERM_PROGRAM'] == 'vscode'

def get_terminal_command():
    """Get the appropriate terminal command for the environment"""
    # Check for common terminal emulators
    terminals = [
        ('gnome-terminal', ['gnome-terminal', '--']),
        ('xterm', ['xterm', '-e']),
        ('konsole', ['konsole', '-e']),
        ('xfce4-terminal', ['xfce4-terminal', '-e']),
        ('terminator', ['terminator', '-e']),
        ('tilix', ['tilix', '-e']),
    ]
    
    for cmd, args in terminals:
        if shutil.which(cmd):
            return args
    
    # If no GUI terminal is found, return None (will use background process)
    return None

def get_vscode_terminal_api():
    """Try to access VSCode terminal API if available"""
    try:
        # Check if the VSCODE_IPC_HOOK_CLI environment variable is set
        if 'VSCODE_IPC_HOOK_CLI' in os.environ:
            return True
    except:
        pass
    return False

def open_vscode_terminal(name, command):
    """Attempt to open a new VSCode terminal with the given command"""
    try:
        # This requires VSCode extension: Command ID "workbench.action.terminal.newWithName"
        # and then executing the command via the VS Code CLI
        script_path = os.path.join(BACKEND_DIR, f"terminal_{name}.sh")
        
        # Create a temporary script file
        with open(script_path, 'w') as f:
            f.write('#!/bin/bash\n')
            f.write(f'cd {os.path.dirname(command[0])}\n')
            f.write(' '.join(command) + '\n')
            f.write('read -p "Press enter to close..."\n')
        
        os.chmod(script_path, 0o755)
        
        # Try to create a new terminal with a specific name
        subprocess.run(['code', '--ms-enable-electron-run-as-node', 
                      '/usr/share/code/resources/app/out/cli.js', 
                      'workbench.action.terminal.newWithName', name])
        
        time.sleep(1)  # Allow terminal to open
        
        # Then send the command to run the script
        subprocess.run(['code', '--ms-enable-electron-run-as-node', 
                      '/usr/share/code/resources/app/out/cli.js', 
                      'workbench.action.terminal.sendSequence', 
                      json.dumps({"text": f"{script_path}\n"})])
        
        return True
    except Exception as e:
        print(f"Failed to open VSCode terminal: {e}")
        return False

def run_service(name, command, cwd=None):
    """Run a service command in a new terminal window or as a background process"""
    print(f"Starting {name}...")
    
    # Set the working directory
    if cwd:
        original_dir = os.getcwd()
        os.chdir(cwd)
        command_path = os.path.abspath(command[0])
        command[0] = command_path
    
    # Try VSCode terminal if in VSCode
    if is_vscode_terminal() and get_vscode_terminal_api():
        success = open_vscode_terminal(name, command)
        if success:
            if cwd:
                os.chdir(original_dir)
            return None  # No process to track when using VSCode terminal
    
    # Otherwise try system terminal
    terminal_cmd = get_terminal_command()
    if terminal_cmd:
        full_command = terminal_cmd + [' '.join(command)]
        try:
            # Launch in a new terminal window
            proc = subprocess.Popen(full_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if cwd:
                os.chdir(original_dir)
            return proc
        except Exception as e:
            print(f"Failed to open terminal: {e}")
    
    # Fallback: run as background process
    try:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if cwd:
            os.chdir(original_dir)
        return proc
    except Exception as e:
        print(f"Failed to start {name}: {e}")
        if cwd:
            os.chdir(original_dir)
        return None

def check_redis():
    """Check if Redis is running, start it if not"""
    try:
        subprocess.run(['redis-cli', 'ping'], stdout=subprocess.PIPE, check=True)
        print("Redis is already running")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Redis is not running, attempting to start...")
        proc = run_service("Redis", ["redis-server"])
        if proc:
            processes.append(proc)
            # Give Redis time to start
            time.sleep(2)
            return True
        return False

def check_mailhog():
    """Check if Mailhog is installed, start it if available"""
    # Use the explicit path in home directory for MailHog
    mailhog_path = os.path.expanduser("~/go/bin/MailHog")
    
    if os.path.exists(mailhog_path) and os.access(mailhog_path, os.X_OK):
        proc = run_service("MailHog", [mailhog_path])
        if proc:
            processes.append(proc)
            print("Mailhog started on 0.0.0.0:8025")
            return True
    else:
        print(f"MailHog not found at {mailhog_path}. Email testing will not be available.")
        print("To install Mailhog: 'go install github.com/mailhog/MailHog@latest'")
        return False

def start_celery_worker():
    """Start Celery worker"""
    worker_script = os.path.join(BACKEND_DIR, "celery_worker.sh")
    
    # Create worker script if it doesn't exist
    if not os.path.exists(worker_script):
        with open(worker_script, 'w') as f:
            f.write('#!/bin/bash\n')
            f.write('cd "$(dirname "$0")"\n')
            f.write('celery -A workers.celery worker --loglevel=info\n')
        os.chmod(worker_script, 0o755)
    
    proc = run_service("Celery Worker", [worker_script], cwd=BACKEND_DIR)
    if proc:
        processes.append(proc)
        return True
    return False

def start_celery_beat():
    """Start Celery beat scheduler"""
    beat_script = os.path.join(BACKEND_DIR, "celery_beat.sh")
    
    # Create beat script if it doesn't exist
    if not os.path.exists(beat_script):
        with open(beat_script, 'w') as f:
            f.write('#!/bin/bash\n')
            f.write('cd "$(dirname "$0")"\n')
            f.write('celery -A workers.celery beat --loglevel=info\n')
        os.chmod(beat_script, 0o755)
    
    proc = run_service("Celery Beat", [beat_script], cwd=BACKEND_DIR)
    if proc:
        processes.append(proc)
        return True
    return False

def start_flask():
    """Start Flask backend"""
    flask_script = os.path.join(BACKEND_DIR, "flask_run.sh")
    
    # Create flask script if it doesn't exist
    if not os.path.exists(flask_script):
        with open(flask_script, 'w') as f:
            f.write('#!/bin/bash\n')
            f.write('cd "$(dirname "$0")"\n')
            f.write('export FLASK_APP=app.py\n')
            f.write('export FLASK_ENV=development\n')
            f.write('flask run --debug\n')
        os.chmod(flask_script, 0o755)
    
    proc = run_service("Flask Backend", [flask_script], cwd=BACKEND_DIR)
    if proc:
        processes.append(proc)
        return True
    return False

def start_frontend():
    """Start frontend development server"""
    if not os.path.exists(FRONTEND_DIR):
        print(f"Frontend directory not found at {FRONTEND_DIR}")
        return False
    
    frontend_script = os.path.join(FRONTEND_DIR, "npm_run_dev.sh")
    
    # Create frontend script if it doesn't exist
    if not os.path.exists(frontend_script):
        with open(frontend_script, 'w') as f:
            f.write('#!/bin/bash\n')
            f.write('cd "$(dirname "$0")"\n')
            f.write('npm run dev\n')
        os.chmod(frontend_script, 0o755)
    
    proc = run_service("Frontend", [frontend_script], cwd=FRONTEND_DIR)
    if proc:
        processes.append(proc)
        return True
    return False

def cleanup(signum=None, frame=None):
    """Clean up processes on exit"""
    print("\nShutting down all services...")
    for proc in processes:
        try:
            proc.terminate()
        except:
            pass
    
    print("All services stopped. Goodbye!")
    sys.exit(0)

def main():
    """Main function to start all services"""
    print("=== Sponnect Application Launcher ===")
    print(f"Project root: {PROJECT_ROOT}")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    print(f"Running in {platform.system()} environment")
    
    # Start Redis
    if not check_redis():
        print("ERROR: Failed to start Redis. Redis is required for the application to work.")
        sys.exit(1)
    
    # Start Mailhog (optional)
    check_mailhog()
    
    # Start Celery worker
    if not start_celery_worker():
        print("WARNING: Failed to start Celery worker. Background tasks will not work.")
    
    # Start Celery beat
    if not start_celery_beat():
        print("WARNING: Failed to start Celery beat. Scheduled tasks will not work.")
    
    # Start Flask backend
    if not start_flask():
        print("ERROR: Failed to start Flask backend.")
        cleanup()
        sys.exit(1)
    
    # Start frontend
    if not start_frontend():
        print("WARNING: Failed to start frontend development server.")
    
    print("\nAll services started successfully!")
    print("Backend: http://localhost:5000")
    print("Frontend: http://localhost:5173")
    print("Mailhog: http://0.0.0.0:8025")
    print("\nPress Ctrl+C to shut down all services.")
    
    # Keep the script running to maintain the process group
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()

