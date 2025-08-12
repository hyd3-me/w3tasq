import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, session, redirect, url_for, request, jsonify
from app import utils, db_utils
from app.models import db
from app.config import config_map, FLASK_ENV
from app.template_filters import shorten_wallet_address

app_logger = logging.getLogger('w3tasq.app')

def create_app(config_name='default'):
    """Factory function to create an application instance"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_map[config_name])

    # Configure logger
    root_logger = logging.getLogger('w3tasq')
    root_logger.setLevel(app.config['LOG_LEVEL'])
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        app.config['LOG_FORMAT'],
        datefmt=app.config.get('LOG_DATEFMT')
    )
    
    # Add console handler for development
    if not app.config.get('LOG_TO_FILE', False):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    else:
        # Ensure logs directory exists
        if not utils.is_log_dir():
            utils.make_log_dir()
        # Add file handler with rotation for testing/production
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=app.config.get('LOG_MAX_BYTES', 1 * 1024 * 1024),
            backupCount=app.config.get('LOG_BACKUP_COUNT', 3)
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Initialize Redis
    utils.init_redis(app)
    
    # Log application start
    root_logger.info(f"Starting w3tasq in {config_name} mode")
    app_logger.debug(f"db_path: {app.config.get('SQLALCHEMY_DATABASE_URI')}")

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
        app_logger.debug("Processing index route")
        # Check if user is authenticated
        if 'user_address' in session and session.get('authenticated'):
            return render_template('index.html', user_address=session.get('user_address'))
        else:
            app_logger.info("Redirecting unauthenticated user to login")
            # Real HTTP redirect to login page
            return redirect(url_for('login'))
    
    @app.route('/login')
    def login():
        app_logger.debug("Rendering login page")
        return render_template('login.html')
    
    @app.route('/api/auth/logout', methods=['POST'])
    def logout():
        app_logger.info(f"User {shorten_wallet_address(session.get('user_address', 'unknown'))} logged out")
        """Clear authentication session"""
        session.clear()
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    
    @app.route('/api/auth/challenge', methods=['POST'])
    def get_challenge():
        app_logger.debug("Processing challenge request")
        """Generate a challenge message for the given address"""
        try:
            data = request.get_json()
            address = data.get('address')
            
            if not address:
                app_logger.error("Address is required for challenge")
                return jsonify({'error': 'Address is required'}), 400
            
            # Generate challenge message using existing utils function
            message = utils.generate_challenge_message(address)
            
            app_logger.info(f"Generated challenge for address {shorten_wallet_address(address)}")
            return jsonify({
                'success': True,
                'message': message
            })
            
        except ValueError as e:
            app_logger.error(f"ValueError in challenge request: {str(e)}")
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            app_logger.error(f"Unexpected error in challenge request: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/auth/verify', methods=['POST'])
    def verify_signature():
        app_logger.debug("Processing signature verification")
        """Verify the signature provided by the client"""
        try:
            data = request.get_json()
            address = data.get('address')
            signature = data.get('signature')
            
            if not address or not signature:
                app_logger.error("Address and signature are required for verification")
                return jsonify({'error': 'Address and signature are required'}), 400
            
            # Verify signature using existing utils function
            is_valid, message = utils.verify_signature(address, signature)
            
            if not is_valid:
                app_logger.warning(f"Signature verification failed for address {shorten_wallet_address(address)}: {message}")
                return jsonify({'error': message}), 401
            user_db, was_created = db_utils.get_or_create_user(address)

            app_logger.info(f"Signature verified for address {shorten_wallet_address(address)}, user {'created' if was_created else 'exists'}")

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
            app_logger.error(f"Unexpected error in signature verification: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/tasks', methods=['POST'])
    def create_task():
        """Create a new task for authenticated user"""
        app_logger.debug("Processing task creation")
        try:
            # Check authentication
            if not session.get('authenticated') or not session.get('user_id'):
                app_logger.warning("Unauthorized task creation attempt")
                return jsonify({'error': 'Authentication required'}), 401
            
            user_id = session['user_id']
            data = request.get_json()
            
            # Validate required fields
            if not data or not data.get('title'):
                app_logger.error("Title is required for task creation")
                return jsonify({'error': 'Title is required'}), 400
            
            # Create task
            task = db_utils.create_task(
                user_id=user_id,
                title=data['title'],
                description=data.get('description', ''),
                priority=data.get('priority', 3),  # Default LOW
                status=data.get('status', 0)       # Default ACTIVE
            )
            app_logger.info(f"Task '{data['title']}' added by user {shorten_wallet_address(session.get('user_address', 'unknown'))}")
            return jsonify({
                'success': True,
                'task': task.to_dict()
            }), 201

        except Exception as e:
            app_logger.error(f"Unexpected error in task creation: {str(e)}")
            db.session.rollback()
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/tasks', methods=['GET'])
    def get_user_tasks():
        """Get tasks for the authenticated user with cursor-based pagination."""
        app_logger.debug("Processing task retrieval")
        try:
            # Check authentication
            if not session.get('authenticated') or not session.get('user_id'):
                app_logger.warning("Unauthorized task retrieval attempt")
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
                app_logger.debug("Invalid cursor, resetting to None")
                cursor_id = None
                limit = app.config.get('TASKS_PER_PAGE', 12)
            
            # Get tasks and pagination info
            tasks, next_cursor_id, has_more = db_utils.get_user_tasks_cursor(
                user_id, cursor_id, limit
            )

            app_logger.info(f"Retrieved {len(tasks)} tasks for user {shorten_wallet_address(session.get('user_address', 'unknown'))}")
            
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
            app_logger.error(f"Unexpected error in task retrieval: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/tasks/<int:task_id>', methods=['PATCH'])
    def update_task_status(task_id):
        """
        Update the status of a specific task for the authenticated user.
        PATCH /api/tasks/<task_id>
        Expects JSON: {"status": 0|1|2}
        """
        app_logger.debug(f"Processing status update for task {task_id}")
        try:
            # 1. Check authentication
            if not session.get('authenticated') or not session.get('user_id'):
                app_logger.warning("Unauthorized task status update attempt")
                return jsonify({'error': 'Authentication required'}), 401

            user_id = session['user_id']
            data = request.get_json()

            # 2. Validate incoming data presence and structure
            if not data:
                app_logger.error("Request body must be valid JSON")
                return jsonify({'error': 'Request body must be valid JSON'}), 400

            if 'status' not in data:
                app_logger.error("Missing required field: status")
                return jsonify({'error': 'Missing required field: status'}), 400

            new_status = data['status']
            # Note: Validation of the status value (e.g., is it 0, 1, or 2?) 
            # is delegated to the db_utils.update_task_status_internal function.
            # This avoids duplicating business logic.

            # 3. Check authorization and get the task instance
            # Use the existing db utility function for authorization and retrieval
            authorized_result, auth_message = db_utils.is_user_authorized_for_task(user_id, task_id)

            if authorized_result is False:
                # User is not authorized (task not found or belongs to another user)
                # Returning 404 aligns with common REST practices for this scenario.
                app_logger.warning(f"Unauthorized task update attempt: {auth_message}")
                return jsonify({'error': auth_message}), 404

            # If authorized_result is not False, it's the Task instance
            task_instance = authorized_result

            # 4. Update the task status using the existing db utility function
            # This function handles validation of new_status and performs the update.
            success, update_message = db_utils.update_task_status_internal(task_instance, new_status)

            if not success:
                # 5a. Return error response if update failed (validation or DB error)
                # The utility function should have handled session rollback on error
                app_logger.error(f"Task status update failed: {update_message}")
                return jsonify({'error': update_message}), 400 # Use 400 for client errors like validation
            # 5a. Return success response with updated task data
            # The task_instance should be updated by update_task_status_internal
            app_logger.info(f"Task {task_id} status updated to {new_status} by user {shorten_wallet_address(session.get('user_address', 'unknown'))}")                        
            return jsonify({
                'success': True,
                'message': update_message, # Message from the utility function
                'task': task_instance.to_dict() # Return the updated task
            }), 200 # 200 OK is standard for successful PATCH       

        except Exception as e:
            # 6. Handle unexpected errors
            # Log the error for debugging in production (consider using app.logger)
            # print(f"Unexpected error in update_task_status: {e}") # For debugging
            app_logger.error(f"Unexpected error in task status update: {str(e)}")
            db.session.rollback() # Ensure session is clean on unexpected error
            return jsonify({'error': 'Internal server error'}), 500
    
    return app

# app = create_app(config_name=FLASK_ENV)

# For running in production
if __name__ == '__main__':
    app = create_app(config_name=FLASK_ENV)
    app.run(debug=True)