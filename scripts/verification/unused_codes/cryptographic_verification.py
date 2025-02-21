from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import base58

def verify_private_key(did, private_key_pem):
    # Fetch the stored public key from the database using the DID
    stored_public_key = get_public_key_from_db(did)  # This function queries the DB
    
    # Load the user's private key
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(
        serialization.load_pem_private_key(private_key_pem.encode(), password=None).private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

    # Get the derived public key from the private key
    derived_public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )

    # Compare the derived public key with the one stored in the database
    return stored_public_key == derived_public_key

def get_public_key_from_db(did):
    # This is a mock function, replace with actual DB query
    return b"\x12\x34\x56..."  # Retrieved stored public key as bytes
