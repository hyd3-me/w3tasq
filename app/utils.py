# app/utils.py
import secrets
from datetime import datetime, timedelta
from web3 import Web3
from eth_account.messages import encode_defunct
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import private_data


# Временное хранилище для challenge (в production лучше использовать Redis)
CHALLENGES = {}

def generate_challenge_message(address):
    """
    Generate a unique challenge message for the given address
    This simulates what the server sends to the client
    """
    # Validate address format
    if not Web3.is_address(address):
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
    
    return message

def get_test_w3addres():
    return private_data.TEST_ADDR1

def verify_signature(address, signature, message):
    """
    Verify that the signature corresponds to the address for the given message
    """
    try:
        # Create Web3 instance
        w3 = Web3()
        
        # Encode message properly for Ethereum signing
        message_hash = encode_defunct(text=message)
        
        # Recover address from signature
        recovered_address = w3.eth.account.recover_message(
            message_hash, 
            signature=signature
        )
        
        # Verify addresses match
        return Web3.to_checksum_address(recovered_address) == Web3.to_checksum_address(address)
    except Exception as e:
        print(f"Verification error: {e}")
        return False

def sign_message_with_private_key(message):
    """
    Sign a message with a private key - simulates what the client does in browser
    The client receives only the message and returns the signature
    Client returns: signature (and uses the message internally for signing)
    """
    # In real browser, client would use their wallet to sign
    # Here we simulate with a test private key
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
    
    return signed_message.signature.hex()

def get_secret_key():
    """
    Get secret key from private_data or generate a temporary one
    """
    # Проверяем, есть ли SECRET_KEY в private_data
    if private_data and hasattr(private_data, 'SECRET_KEY'):
        secret_key = private_data.SECRET_KEY
        # Проверяем, не является ли это placeholder значением
        if secret_key and not secret_key.startswith('your-super-secret'):
            return secret_key
    
    # Для разработки генерируем временный ключ
    print("WARNING: Using temporary secret key. For production, set SECRET_KEY in private_data.py")
    return secrets.token_urlsafe(32)