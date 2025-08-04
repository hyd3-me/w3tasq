# app/app.py
from flask import Flask, render_template, session, redirect, url_for, request, jsonify
from app import utils, db_utils
from app.models import db # pyright: ignore[reportMissingImports]
from app.config import config_map # pyright: ignore[reportMissingImports]
# Import filters
from app.template_filters import shorten_wallet_address # pyright: ignore[reportMissingImports]


def create_app(config_name='default'):
    """Фабричная функция для создания экземпляра приложения"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_map[config_name])

    # Register custom filters
    app.jinja_env.filters['shorten_wallet'] = shorten_wallet_address
    
    # Initialize application with config (if needed)
    #config_map[config_name].init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    @app.route('/')
    def index():
        # Check if user is authenticated
        if 'user_address' in session and session.get('authenticated'):
            return render_template('index.html', user_address=session.get('user_address'))
        else:
            # Real HTTP redirect to login page
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
            
            if not is_valid:
                return jsonify({'error': message}), 401
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
                
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/tasks', methods=['POST'])
    def create_task():
        """Create a new task for authenticated user"""
        try:
            # Check authentication
            if not session.get('authenticated') or not session.get('user_id'):
                return jsonify({'error': 'Authentication required'}), 401
            
            user_id = session['user_id']
            data = request.get_json()
            
            # Validate required fields
            if not data or not data.get('title'):
                return jsonify({'error': 'Title is required'}), 400
            
            # Create task
            task = db_utils.create_task(
                user_id=user_id,
                title=data['title'],
                description=data.get('description', ''),
                priority=data.get('priority', 3),  # Default LOW
                status=data.get('status', 0)       # Default ACTIVE
            )
            return jsonify({
                'success': True,
                'task': task.to_dict()
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/tasks', methods=['GET'])
    def get_user_tasks():

        """Get tasks for the authenticated user with cursor-based pagination."""
        try:
            # Check authentication
            if not session.get('authenticated') or not session.get('user_id'):
                return jsonify({'error': 'Authentication required'}), 401
            
            user_id = session['user_id']

            # --- Cursor-based Pagination ---
            try:
                # Get cursor from URL
                cursor_str = request.args.get('cursor', None)
                
                # Get limit from config
                limit = app.config.get('TASKS_PER_PAGE', 12)
                
                # Convert cursor to number if it exists
                cursor_id = None
                if cursor_str:
                    cursor_id = int(cursor_str)
                    
            except (ValueError, TypeError):
                cursor_id = None
                limit = app.config.get('TASKS_PER_PAGE', 12)
            
            # Get tasks and pagination info
            tasks, next_cursor_id, has_more = db_utils.get_user_tasks_cursor(
                user_id, cursor_id, limit
            )
            
            # Prepare data for response
            tasks_data = [task.to_dict() for task in tasks]
            
            # Create simplified pagination info
            pagination_info = {
                'has_more': has_more,
                'next_cursor': next_cursor_id if has_more else None
            }
            
            return jsonify({
                'tasks': tasks_data,
                'pagination': pagination_info
            })
            
        except Exception as e:
            print(f"Error retrieving tasks: {e}") # For debugging
            return jsonify({'error': 'Internal server error'}), 500
    
    return app

# Для запуска в production
if __name__ == '__main__':
    app = create_app(config_name='testing')
    app.run(debug=True)