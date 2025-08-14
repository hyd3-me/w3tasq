w3tasq
A Flask-based task management application with Ethereum wallet authentication, using SQLite for persistent storage and Redis for temporary session data.
Project Structure
/var/www/w3tasq/
├── private_data.py     # Configuration file with secrets
├── db/
│   └── tasks_notes.db  # SQLite database for tasks
├── source/
│   ├── app/
│   │   ├── main.py
│   │   ├── app.py      # Main Flask application
│   │   ├── utils.py    # Utility functions (e.g., Ethereum auth)
│   │   ├── models.py   # Database models
│   │   ├── db_utils.py # Database utilities
│   │   ├── static/
│   │   ├── templates/
│   │   └── config.py   # Flask configuration
│   |── run.py
│   ├── Dockerfile      # Docker image definition
│   ├── docker-compose.yml  # Docker Compose configuration
│   ├── requirements.txt    # Python dependencies
│   ├── logs/           # Gunicorn logs (created in container)
│   ├── tests/
│   └── README.md       # This file



Status
This project is in active development and deployed in production.



Features

Ethereum Wallet Authentication: Secure login via signing messages with an Ethereum wallet.
Task Management: Create, update, and delete tasks via a REST API.
Persistent Storage: Uses SQLite (tasks_notes.db) for task data.
Session Management: Stores temporary authentication challenges in Redis.
Dockerized Deployment: Runs in a lightweight python:3.9-alpine container with Gunicorn.
Systemd Integration: Automatic startup via w3tasq.service.

Prerequisites

Python 3.9: For local development or dependency installation.
Docker 28.3.3: For containerized deployment.
Docker Compose 2.33.0: For managing the application container.
Redis: A Redis server must be running and accessible at 172.17.0.1:6379 with a password (configured in private_data.py).
SQLite: Included with Python, no separate installation required.
Ubuntu 22.04: Recommended OS for production deployment.

Installation

Clone the repository:
git clone https://github.com/your-repo/w3tasq.git
cd /var/www/w3tasq/source


Set up Redis:Ensure a Redis server is running at 172.17.0.1:6379 with the password specified in private_data.py. Install Redis if not present:
sudo apt update
sudo apt install redis-server


Create private_data.py:Create the file at /var/www/w3tasq/private_data.py with the following:
REDIS_PWD = 'topsecret_pass'  # Redis password
SECRET_KEY = 'your-super-secret-key'  # Flask secret key
TEST_ADDR1 = '0xYourTestEthereumAddress'  # Test Ethereum address
PRIVATE_KEY = '0xYourTestPrivateKey'  # Test private key


Set up SQLite database:Ensure the directory /var/www/w3tasq/db/ exists:
mkdir -p /var/www/w3tasq/db

The tasks_notes.db file will be created automatically at /var/www/w3tasq/db/tasks_notes.db.

Build and start the Docker container:
docker-compose build
docker-compose up -d



Configuration

Environment Variables (in docker-compose.yml):environment:
  - FLASK_ENV=production
  - REDIS_HOST=172.17.0.1
  - REDIS_PORT=6379


Database: SQLite database at /var/www/w3tasq/db/tasks_notes.db.
Secrets: Stored in /var/www/w3tasq/private_data.py.



Usage

Access the application:Open https://w3tasq.1384139-cx33953.tw1.ru/ in a browser. Unauthenticated users are redirected to /login.

API Endpoints:

POST /api/auth/logout: Log out the authenticated user.
PATCH /api/tasks/<task_id>: Update task status (requires authentication).Example:

curl -X PATCH -H "Content-Type: application/json" -d '{"status": 1}' https://w3tasq.1384139-cx33953.tw1.ru/api/tasks/123



Development

Install dependencies:
pip install -r requirements.txt


Run locally (development mode):
export FLASK_ENV=development
python run.py



Deployment

Install Docker and systemd:
sudo apt update
sudo apt install docker.io docker-compose


Set up systemd service:
sudo vim /etc/systemd/system/w3tasq.service

Add:
[Unit]
Description=w3tasq Flask Application
After=network.target docker.service
Requires=docker.service

[Service]
WorkingDirectory=/var/www/w3tasq/source
ExecStart=/usr/bin/docker-compose -f docker-compose.yml up
ExecStop=/usr/bin/docker-compose -f docker-compose.yml down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target


Enable and start the service:
sudo systemctl daemon-reload
sudo systemctl enable w3tasq.service
sudo systemctl start w3tasq.service


Check status:
sudo systemctl status w3tasq.service


Support

Create an issue: https://github.com/hyd3-me/w3tasq/issues
Contact: w1ld.s3dg@gmail.com

Acknowledgements

Built with Flask, Gunicorn, and eth-account.
Thanks to the open-source community for tools and inspiration.
