import os
from cryptography.hazmat.primitives.asymmetric import ed25519

def generate_challenge():
    return os.urandom(32)  # Random 32-byte challenge

def sign_challenge(private_key_pem, challenge):
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(
        serialization.load_pem_private_key(private_key_pem.encode(), password=None).private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    return private_key.sign(challenge)  # Signed challenge

def verify_signature(did, challenge, signature):
    stored_public_key = get_public_key_from_db(did)  # Retrieve from database
    public_key = ed25519.Ed25519PublicKey.from_public_bytes(stored_public_key)
    
    try:
        public_key.verify(signature, challenge)  # Verify the signature
        return True
    except:
        return False  # Verification failed
