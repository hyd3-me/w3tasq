# app/utils.py
import secrets
from datetime import datetime
from web3 import Web3
from eth_account.messages import encode_defunct
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import private_data

def generate_challenge_message():
    """
    Generate a unique challenge message for authentication
    This simulates what the server sends to the client
    """
    # Generate a random challenge
    challenge = secrets.token_hex(16)
    # Include timestamp for freshness
    timestamp = datetime.utcnow().isoformat()
    return f"Sign this message to authenticate: {challenge} at {timestamp}"

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