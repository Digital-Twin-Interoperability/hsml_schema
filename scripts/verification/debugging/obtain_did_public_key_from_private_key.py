from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
import base58

def derive_public_key_from_private_key(private_key_path):
    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(key_file.read(), password=None)

    if not isinstance(private_key, Ed25519PrivateKey):
        raise ValueError("Invalid key type. Expected Ed25519.")

    public_key = private_key.public_key()
    
    # Serialize the public key to raw bytes
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    
    # Multicodec prefix for Ed25519 keys
    multicodec_prefix = b'\xed\x01'  # 0xED01 prefix for Ed25519
    multicodec_key = multicodec_prefix + public_key_bytes
    
    # Base58 encoding for DID:key format
    did_key = "did:key:" + base58.b58encode(multicodec_key).decode('utf-8')
    
    return did_key

# Example usage
private_key_path = "C:/Users/abarrio/OneDrive - JPL/Desktop/Digital Twin Interoperability/Codes/HSML Examples/registeredExamples/private_key_example_agent_2.pem"
did_key = derive_public_key_from_private_key(private_key_path)
print(did_key)
