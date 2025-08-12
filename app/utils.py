import logging
import secrets
from datetime import datetime, timedelta
from web3 import Web3
from eth_account.messages import encode_defunct
import os, sys
import redis
import json

def get_source_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.dirname(get_source_dir()))

import private_data

# Set up logger
logger = logging.getLogger('w3tasq.utils')

# Initialize Redis client
redis_client = None

def init_redis(app):
    """Initialize Redis client with app configuration"""
    global redis_client
    redis_client = redis.Redis(
        host=app.config['REDIS_HOST'],
        port=app.config['REDIS_PORT'],
        password=app.config['REDIS_PASSWORD'],
        decode_responses=True  # Automatically decode strings
    )
    logger.debug("Redis client initialized")

def get_redis_pwd():
    return private_data.REDIS_PWD

def get_redis_host():
    return os.getenv('REDIS_HOST', 'host.docker.internal')

def get_redis_port():
    return int(os.getenv('REDIS_PORT', 6379))

def get_env():
    return os.getenv('FLASK_ENV', 'default')

def generate_challenge_message(address):
    """
    Generate a unique challenge message for the given address
    This simulates what the server sends to the client
    """
    logger.debug(f"Generating challenge for address {address}")
    # Validate address format
    if not Web3.is_address(address):
        logger.error(f"Invalid Ethereum address format: {address}")
        raise ValueError("Invalid Ethereum address format")
    
    # Normalize address
    normalized_address = Web3.to_checksum_address(address)
    
    # Generate unique challenge
    challenge = secrets.token_hex(16)
    timestamp = datetime.utcnow().isoformat()
    
    # Create message for signing
    message = f"Sign this message to authenticate: {challenge} at {timestamp}"
    
    # Store challenge in Redis with 5-minute TTL
    redis_key = f"w3tasq_challenge:{normalized_address}"
    redis_client.hset(redis_key, mapping={
        'challenge': challenge,
        'message': message,
        'expires_at': timestamp
    })
    redis_client.expire(redis_key, 300)  # 5 minutes TTL
    logger.info(f"Challenge generated for address {normalized_address}")
    return message

def get_test_w3addres():
    return private_data.TEST_ADDR1

def verify_signature(address, signature):
    """
    Verify that the signature corresponds to the address for the given message
    """
    logger.debug(f"Verifying signature for address {address}")
    try:
        # Normalize address
        normalized_address = Web3.to_checksum_address(address)
        
        # Check if challenge exists in Redis
        redis_key = f"w3tasq_challenge:{normalized_address}"
        stored_challenge = redis_client.hgetall(redis_key)
        
        if not stored_challenge:
            logger.warning(f"No challenge found for address {normalized_address}")
            return False, "No challenge found for this address"
        
        # Check if challenge has expired
        expires_at = datetime.fromisoformat(stored_challenge['expires_at'])
        if datetime.utcnow() > expires_at + timedelta(minutes=5):
            logger.warning(f"Challenge expired for address {normalized_address}")
            redis_client.delete(redis_key)
            return False, "Challenge has expired"
        
        # Create Web3 instance
        w3 = Web3()
        
        # Encode message properly for Ethereum signing
        message_hash = encode_defunct(text=stored_challenge['message'])
        
        # Recover address from signature
        recovered_address = w3.eth.account.recover_message(
            message_hash, 
            signature=signature
        )
        
        # Verify addresses match
        is_valid = Web3.to_checksum_address(recovered_address) == normalized_address
        
        # If valid, remove used challenge
        if is_valid:
            logger.info(f"Signature verified for address {normalized_address}")
            redis_client.delete(redis_key)
        else:
            logger.warning(f"Signature does not match address {normalized_address}")
        
        return is_valid, "Signature verified successfully" if is_valid else "Signature does not match the address"
    
    except Exception as e:
        logger.error(f"Verification error for address {address}: {str(e)}")
        return False, f"Verification error: {str(e)}"

def sign_message_with_private_key(message):
    """
    Sign a message with a private key - simulates what the client does in browser
    The client receives only the message and returns the signature
    Client returns: signature (and uses the message internally for signing)
    """
    # In real browser, client would use their wallet to sign
    # Here we simulate with a test private key
    logger.debug("Signing message with private key")
    w3 = Web3()
    # This private key is for testing only
    private_key = private_data.PRIVATE_KEY
    
    # Properly encode the message for Ethereum signing
    message_hash = encode_defunct(text=message)
    
    # Sign the encoded message
    signed_message = w3.eth.account.sign_message(
        message_hash,
        private_key=private_key
    )
    logger.info("Message signed successfully")
    return signed_message.signature.hex()

def get_secret_key():
    """
    Get secret key from private_data or generate a temporary one
    """
    # Check if SECRET_KEY exists in private_data
    logger.debug("Retrieving secret key")
    if private_data and hasattr(private_data, 'SECRET_KEY'):
        secret_key = private_data.SECRET_KEY
        # Check if it's not a placeholder value
        if secret_key and not secret_key.startswith('your-super-secret'):
            logger.info("Using secret key from private_data")
            return secret_key
    
    logger.warning("Using temporary secret key for development")
    return secrets.token_urlsafe(32)

def get_database_path():
    """
    Get database file path outside of repository
    Returns path to tasks_notes.db file one level above project directory
    """
    logger.debug("Retrieving database path")
    db_path = join_path(os.path.dirname(get_source_dir()), 'db', 'tasks_notes.db')
    logger.info(f"Database path: {db_path}")
    return db_path

def join_path(*args):
    return os.path.join(*args)

def is_log_dir():
    return os.path.exists(join_path(get_source_dir(), 'logs'))

def make_log_dir():
    os.makedirs(join_path(get_source_dir(), 'logs'))