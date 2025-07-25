# app/app.py
from flask import Flask, render_template, session, redirect, url_for, request, jsonify
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
    
    @app.route('/api/auth/challenge', methods=['POST'])
    def get_challenge():
        """Generate a challenge message for the given address"""
        try:
            data = request.get_json()
            address = data.get('address')
            
            if not address:
                return jsonify({'error': 'Address is required'}), 400
            
            # Generate challenge message using existing utils function
            message = utils.generate_challenge_message(address)
            
            return jsonify({
                'success': True,
                'message': message
            })
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500
    
    return app

# Для запуска в production
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)