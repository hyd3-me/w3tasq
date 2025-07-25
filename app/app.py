# app/app.py
from flask import Flask, render_template
from app import utils


def create_app():
    """Фабричная функция для создания экземпляра приложения"""
    app = Flask(__name__)
    
    # Configure secret key for sessions using utils
    app.secret_key = utils.get_secret_key()
    
    @app.route('/')
    def hello_world():
        return render_template('index.html')
    
    @app.route('/login')
    def login():
        return render_template('login.html')
    return app

# Для запуска в production
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)