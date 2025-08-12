# run.py
from app.app import create_app
from app.config import FLASK_ENV

# Set configuration mode from FLASK_ENV (defaults to 'development')
config_name = FLASK_ENV

# Initialize Flask application
app = create_app(config_name=config_name)

if __name__ == '__main__':
    # Run server for development or testing
    app.run(host='0.0.0.0', port=5000, debug=config_name != 'production')