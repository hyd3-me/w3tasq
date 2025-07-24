# tests/test_auth.py
import app.utils as utils

def test_signature_verification_valid():
    """Test: valid signature should pass verification"""
    # Generate message as server would do
    message = utils.generate_challenge_message()
    
    # Client receives message and returns signature
    signature = utils.sign_message_with_private_key(message)
    
    # Server verifies using address, signature and original message
    address = utils.get_test_w3addres()
    
    # Verify the signature
    result = utils.verify_signature(address, f"0x{signature}", message)
    assert result is True

def test_signature_verification_invalid():
    """Test: invalid signature should not pass verification"""
    message = "Sign this message to authenticate: abc123"
    address = "0x742d35Cc6634C0532925a3b8D4C7d26990d0f7f6"
    signature = "0xinvalidsignature"
    
    result = utils.verify_signature(address, signature, message)
    assert result is False