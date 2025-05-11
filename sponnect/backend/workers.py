from celery import Celery

# Initialize celery app
celery = Celery(
    'sponnect',
    include=['task', 'user_notifications'],
    broker='redis://localhost:6379/1',
    backend='redis://localhost:6379/2'
)

# Beat scheduler configuration
celery.conf.beat_schedule_filename = 'celerybeat-schedule'
celery.conf.worker_max_tasks_per_child = 100  # Restart workers after handling 100 tasks
celery.conf.broker_connection_retry_on_startup = True
celery.conf.result_expires = 3600  # Results expire after 1 hour

class ContextTask(celery.Task):
    """Task that provides app context to the task when run"""
    abstract = True
    
    def __call__(self, *args, **kwargs):
        from app import app
        with app.app_context():
            return self.run(*args, **kwargs) 