import json
import pymysql
import base58
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

# Database connection
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "MoonwalkerJPL85!",
    "database": "did_registry"
}

def validate_json(json_data):
    """Validate JSON format and required fields."""
    if not isinstance(json_data, dict):
        return False, "Invalid JSON format. Expected an object."
    
    if "type" not in json_data or json_data["type"] != "HSML":
        return False, "Entity type is missing or not HSML."
    
    required_fields = ["name", "description"]  # Add required fields per type
    missing_fields = [field for field in required_fields if field not in json_data]
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, "Valid JSON."

def check_existing_swid(swid):
    """Check if swid already exists in the database."""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM did_keys WHERE did = %s", (swid,))
    exists = cursor.fetchone()[0] > 0
    conn.close()
    return exists

def generate_did_key():
    """Generate a did:key and private key."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    
    multicodec_prefix = b'\xed\x01'
    multicodec_key = multicodec_prefix + public_key_bytes
    
    did_key = f"did:key:{base58.b58encode(multicodec_key).decode('utf-8')}"
    return did_key, private_key

def save_private_key(private_key, filename="private_key.pem"):
    """Save private key to a file."""
    with open(filename, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))

def store_entity(did, public_key, metadata):
    """Store DID, public key, and metadata in the database."""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO did_keys (did, public_key, metadata) 
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE public_key = %s, metadata = %s
    """, (did, public_key, json.dumps(metadata), public_key, json.dumps(metadata)))
    conn.commit()
    conn.close()

def register_entity(json_file):
    """Main function to process entity registration."""
    with open(json_file, "r") as f:
        json_data = json.load(f)
    
    is_valid, message = validate_json(json_data)
    if not is_valid:
        return message
    
    if "swid" in json_data and check_existing_swid(json_data["swid"]):
        print("Warning: swid already exists and will be overwritten.")
    
    did_key, private_key = generate_did_key()
    json_data["swid"] = did_key  # Attach DID to swid
    
    store_entity(did_key, did_key.split(":")[-1], json_data)
    save_private_key(private_key)
    
    with open("updated_entity.json", "w") as f:
        json.dump(json_data, f, indent=4)
    
    return "Entity registered successfully. Private key saved to private_key.pem."
