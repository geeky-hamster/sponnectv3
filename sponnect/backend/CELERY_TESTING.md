# Testing Celery Tasks with Beat and Mailhog

This guide explains how to test Celery tasks with Beat scheduler and Mailhog for email testing in the Sponnect application.

## Prerequisites

- Redis server running (for Celery broker and result backend)
- Mailhog running for email testing
- Python environment with all dependencies installed

## Available Tasks

A minute reminder task has been set up for testing purposes:

- `send_minute_test_reminder`: Sends an email every minute with the current timestamp

## Testing Methods

There are several ways to test the Celery functionality:

### 1. Direct Script Execution

Run the test script to execute the task directly without Celery:

```bash
./test_reminder.py
```

This will execute the task once and send the email through Mailhog.

### 2. API Endpoint

Use the API endpoint to trigger the task (requires admin authentication):

```bash
curl -X POST http://localhost:5000/api/admin/test/reminder \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json"
```

### 3. Celery Worker and Beat

For the full Celery experience, run both the worker and beat processes:

#### Start Celery Worker:

```bash
./start_celery_worker.sh
```

This starts a worker that processes the tasks.

#### Start Celery Beat:

```bash
./start_celery_beat.sh
```

This starts the scheduler that will trigger the task every minute.

## Viewing Emails in Mailhog

All emails sent by the tasks will be captured by Mailhog. To view them:

1. Make sure Mailhog is running
2. Open Mailhog web interface (typically at http://localhost:8025)
3. You should see the test emails in the interface

## Troubleshooting

If you're having issues:

1. Check that Redis is running: `redis-cli ping` (should return PONG)
2. Verify Mailhog is running: Open the web interface
3. Check Celery worker logs for errors
4. Ensure the Flask app's mail configuration points to Mailhog (typically localhost:1025)

## Production Considerations

For production, you would want to:

1. Use a proper message broker (Redis or RabbitMQ)
2. Run Celery as a service with proper process management
3. Configure a real email server instead of Mailhog
4. Adjust the schedule to appropriate intervals (not every minute) 