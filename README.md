# Sponnect

Sponnect is a platform that connects influencers with sponsors for promotional campaigns and collaborations.

## Features

- **User Management**: Separate interfaces for sponsors, influencers, and administrators
- **Campaign Management**: Create, browse, and manage promotional campaigns
- **Ad Request System**: Facilitate the negotiation process between sponsors and influencers
- **Progress Tracking**: Document and review campaign progress and performance metrics
- **Payment Processing**: Seamless payment handling for completed collaborations
- **Admin Dashboard**: Comprehensive platform statistics and user management

## Recent Updates

- Removed unnecessary backup files and scripts
- Updated the mock data generator to create more realistic test data
- Fixed date format issues in the frontend
- Improved search functionality for campaigns
- Unified data handling across components

## Project Structure

```
sponnect/
├── backend/           # Flask API server
│   ├── models.py      # Database models
│   ├── app.py         # Main application
│   ├── config.py      # Configuration settings
│   ├── constants.py   # Shared constants
│   ├── mock_data.py   # Test data generator
│   └── run.py         # Application launcher
├── frontend/          # Vue.js frontend
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   ├── stores/
│   │   ├── utils/
│   │   └── views/
│   ├── index.html
│   └── package.json
└── reports/           # Analytics and reporting
```

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/sponnect.git
   cd sponnect
   ```

2. **Backend Setup**
   ```bash
   cd sponnect/backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd ../frontend
   npm install
   ```

4. **Generate Test Data** (Optional)
   ```bash
   cd ../backend
   python3 -c "from mock_data import main; main()"
   ```

5. **Run the Application**
   ```bash
   cd ..
   python3 sponnect/backend/run.py
   ```

This will start both the backend and frontend servers, and you can access the application at http://localhost:5173

## Development Notes

- The backend API runs on port 5000
- Frontend development server runs on port 5173
- Redis is used for caching and Celery tasks
- Make sure both frontend and backend are running for full functionality

## License

[MIT License](LICENSE)

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