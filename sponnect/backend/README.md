# Sponnect Backend

## Overview
This is the backend API service for Sponnect, a platform connecting sponsors and influencers.

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Redis server (for Celery and caching)
- Mailhog (for email testing)

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/sponnect.git
cd sponnect/backend
```

2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables (create a .env file)
```
JWT_SECRET_KEY=your_jwt_secret_key
MAIL_SERVER=localhost
MAIL_PORT=1025
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

### Running Services

#### Redis (required for Celery and caching)
Make sure Redis is installed and running. On most systems:
```bash
# Start Redis server
redis-server
```

#### Mailhog (for email testing)
Mailhog provides a local SMTP server and web interface for testing emails.
```bash
# If installed via go
~/go/bin/MailHog

# If installed via Docker
docker run -p 1025:1025 -p 8025:8025 mailhog/mailhog
```
Access the Mailhog web interface at: http://localhost:8025

#### Flask Application
```bash
# Run the Flask application
flask run --debug
# Or alternatively
python app.py
```

#### Celery Worker
Run the Celery worker to process background tasks:
```bash
celery -A workers.celery worker --loglevel=info
```

#### Celery Beat (for scheduled tasks)
Run Celery Beat to enable scheduled tasks:
```bash
celery -A workers.celery beat --loglevel=info
```

## API Documentation

API documentation is available at `/api/docs` when the server is running.

## Testing

### Testing Email Functionality
1. Make sure Mailhog is running
2. Make a POST request to `/api/admin/test/celery` with a JSON body containing the email address: `{"email": "test@example.com"}`
3. Check the Mailhog web interface (http://localhost:8025) to see if the email was received

### Testing Celery Tasks
1. Use the `/api/admin/test/celery` endpoint to trigger a test email
2. The response will include a `task_id`
3. Check the task status at `/api/admin/tasks/{task_id}`

## Troubleshooting

### Redis Connection Issues
- Ensure Redis is running: `redis-cli ping` should return `PONG`
- Check the connection URL in your .env file

### Celery Worker Not Processing Tasks
- Check if the worker is running with the correct app name
- Look for error messages in the worker logs
- Verify that Redis is accessible by the Celery worker

## Caching System

The application uses Redis-based caching to improve performance, particularly for the admin dashboard and statistics pages. Here's how the caching system works:

### Backend Caching

The backend uses Flask-Caching with Redis to cache API responses:

- **Admin Dashboard Stats**: Cached for 60 seconds to balance data freshness with performance
- **Dashboard Summary Charts**: Cached for 120 seconds (2 minutes)
- **User Growth Charts**: Cached for 300 seconds (5 minutes), varies by query parameters
- **Campaign Distribution**: Cached for 180 seconds (3 minutes)
- **Ad Request Status**: Cached for 180 seconds (3 minutes)
- **Campaign Activity**: Cached for 180 seconds (3 minutes), varies by query parameters
- **Pending Users Lists**: Cached for 15 seconds to ensure quick approval updates

### When to Use Caching

The caching system is optimized for the following use cases:

- **High Traffic Admin Pages**: The dashboard and statistics pages can handle higher traffic without overloading the database
- **Complex Queries**: Charts and statistics that require complex database queries are cached
- **Real-time Not Critical**: Data where real-time accuracy isn't mission-critical (trends, general statistics)

### When Not to Use Caching

Caching should not be used for:

- **Critical State Changes**: User approvals, payments, or other state changes should bypass cache
- **User-specific Data**: Personal user data that needs to be always current
- **Security-related Features**: Authentication, permissions checking should never be cached

### Frontend Caching

The frontend implements smart client-side caching that:

1. Tracks when data was last fetched
2. Only requests new data when the cache expires
3. Provides manual refresh buttons for immediate updates
4. Shows last refresh time to users
5. Optimizes API calls by bundling requests

This dual-layer caching approach (backend + frontend) provides excellent performance while maintaining data freshness where needed. 