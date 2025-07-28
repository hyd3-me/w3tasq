# app/app.py
from flask import Flask, render_template, session, redirect, url_for, request, jsonify
from app import utils, db_utils
from app.models import db


def create_app(config_name='default'):
    """Фабричная функция для создания экземпляра приложения"""
    app = Flask(__name__)
    
    # Configure secret key for sessions using utils
    app.secret_key = utils.get_secret_key()

    # Configuration
    if config_name == 'testing':
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    else:
        # Configure database using path from utils
        db_path = utils.get_database_path()
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
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
    
    @app.route('/api/auth/logout', methods=['POST'])
    def logout():
        """Clear authentication session"""
        session.clear()
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    
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
    
    @app.route('/api/auth/verify', methods=['POST'])
    def verify_signature():
        """Verify the signature provided by the client"""
        try:
            data = request.get_json()
            address = data.get('address')
            signature = data.get('signature')
            
            if not address or not signature:
                return jsonify({'error': 'Address and signature are required'}), 400
            
            # Verify signature using existing utils function
            is_valid, message = utils.verify_signature(address, signature)
            
            if is_valid:

                user_db, was_created = db_utils.get_or_create_user(address)

                # Store user in session
                session['user_address'] = address
                session['user_id'] = user_db.id
                session['authenticated'] = True
                
                return jsonify({
                    'success': True,
                    'address': address,
                    'message': message
                })
            else:
                return jsonify({'error': message}), 401
                
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/tasks', methods=['POST'])
    def create_task():
        """Create a new task for authenticated user"""
        try:
            # Проверяем аутентификацию
            if not session.get('authenticated') or not session.get('user_id'):
                return jsonify({'error': 'Authentication required'}), 401
            
            user_id = session['user_id']
            data = request.get_json()
            
            # Валидация обязательных полей
            if not data or not data.get('title'):
                return jsonify({'error': 'Title is required'}), 400
            
            # Создаем задачу
            task = db_utils.create_task(
                user_id=user_id,
                title=data['title'],
                description=data.get('description', ''),
                priority=data.get('priority', 3),  # По умолчанию LOW
                status=data.get('status', 0)       # По умолчанию ACTIVE
            )
            return jsonify({
                'success': True,
                'task': task.to_dict()
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Internal server error'}), 500
    
    return app

# Для запуска в production
if __name__ == '__main__':
    app = create_app(config_name='testing')
    app.run(debug=True)