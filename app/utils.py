import logging
import secrets
from datetime import datetime, timedelta
from web3 import Web3
from eth_account.messages import encode_defunct
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import private_data

# Set up logger
logger = logging.getLogger('w3tasq.utils')

# Temporary storage for challenges (use Redis in production)
CHALLENGES = {}

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
    
    # Store challenge with expiration (5 minutes)
    CHALLENGES[normalized_address] = {
        'challenge': challenge,
        'message': message,
        'expires_at': datetime.utcnow() + timedelta(minutes=5)
    }
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
        
        # Check if challenge exists for this address
        if normalized_address not in CHALLENGES:
            logger.warning(f"No challenge found for address {normalized_address}")
            return False, "No challenge found for this address"
        
        # Get stored challenge
        stored_challenge = CHALLENGES[normalized_address]
        
        # Check if challenge has expired
        if datetime.utcnow() > stored_challenge['expires_at']:
            # Remove expired challenge
            logger.warning(f"Challenge expired for address {normalized_address}")
            del CHALLENGES[normalized_address]
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
            del CHALLENGES[normalized_address]
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
    db_path = os.path.join(os.path.dirname(get_source_dir()), 'tasks_notes.db')
    logger.info(f"Database path: {db_path}")
    return db_path

def get_source_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def join_path(*args):
    return os.path.join(*args)

def is_log_dir():
    return os.path.exists(join_path(get_source_dir(), 'logs'))

def make_log_dir():
    os.makedirs(join_path(get_source_dir(), 'logs'))