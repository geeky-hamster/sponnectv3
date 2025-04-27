# Sponnect

Sponnect is a platform that connects influencers with sponsors for advertising campaigns.

## Features

- User management (influencers, sponsors, admins)
- Campaign creation and management
- Ad request processing and negotiation
- Email notifications
- Analytics and reporting

## Testing Celery Tasks with Beat and Mailhog

A minute reminder task has been implemented for testing Celery's scheduled tasks. This task sends an email every minute and can be used to test the integration with Mailhog.

### Running with Docker Compose

The easiest way to test the Celery functionality is using Docker Compose:

```bash
docker-compose -f docker-compose-celery.yml up
```

This will start:
- Redis (broker and result backend)
- Mailhog (for email testing)
- Celery worker
- Celery beat scheduler

### Manual Testing

You can also test the functionality manually:

1. Start Redis server
2. Start Mailhog
3. Run Celery worker:
   ```bash
   cd sponnect/backend
   ./start_celery_worker.sh
   ```
4. Run Celery beat:
   ```bash
   cd sponnect/backend
   ./start_celery_beat.sh
   ```

### Testing a Single Task Execution

To test a single execution of the task:

```bash
cd sponnect/backend
python3 test_reminder.py
```

### Viewing Test Emails

Access the Mailhog interface at: http://localhost:8025

### Detailed Documentation

For more details, see [CELERY_TESTING.md](sponnect/backend/CELERY_TESTING.md) 