# app/app.py
from flask import Flask, render_template, session, redirect, url_for
from app import utils


def create_app():
    """Фабричная функция для создания экземпляра приложения"""
    app = Flask(__name__)
    
    # Configure secret key for sessions using utils
    app.secret_key = utils.get_secret_key()
    
    @app.route('/')
    def index():
        # Проверяем, авторизован ли пользователь
        if 'user_address' in session and session.get('authenticated'):
            return render_template('index.html', user_address=session.get('user_address'))
        else:
            # Настоящий HTTP редирект на страницу логина
            return redirect(url_for('login'))
    
    @app.route('/login')
    def login():
        return render_template('login.html')
    return app

# Для запуска в production
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)