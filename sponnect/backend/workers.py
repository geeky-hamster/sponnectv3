from celery import Celery

# Initialize celery app
celery = Celery(
    'sponnect',
    include=['task'],
    broker='redis://localhost:6379/1',
    backend='redis://localhost:6379/2'
)

class ContextTask(celery.Task):
    """Task that provides app context to the task when run"""
    abstract = True
    
    def __call__(self, *args, **kwargs):
        from app import app
        with app.app_context():
            return self.run(*args, **kwargs) 