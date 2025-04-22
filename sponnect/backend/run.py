# run.py
from app import app

if __name__ == '__main__':
    # Debug mode is controlled by FLASK_DEBUG in .env when using `flask run`
    # Or set directly here if running via `python run.py`
    app.run(debug=app.config['DEBUG'])

