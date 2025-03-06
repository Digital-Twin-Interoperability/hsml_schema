import json
import os
import subprocess
import mysql.connector
import requests  # Used to fetch HSML schema
from flask import Flask, request, jsonify
from kafka import KafkaProducer

app = Flask(__name__)

# MySQL connection setup
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "MoonwalkerJPL85!",
    "database": "did_registry"
}

# Kafka setup
KAFKA_SERVER = "localhost:9092"
producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER, value_serializer=lambda v: json.dumps(v).encode("utf-8"))

# HSML Schema URL
HSML_SCHEMA_URL = "https://digital-twin-interoperability.github.io/hsml-schema-context/hsml.jsonld"

def fetch_hsml_schema():
    """Fetch the official HSML schema"""
    try:
        response = requests.get(HSML_SCHEMA_URL)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching HSML schema: {e}")
        return None

def validate_json(json_data, hsml_schema):
    """Validate JSON against HSML schema"""
    # Ensure the @context matches HSML
    if json_data.get("@context") != hsml_schema["@context"]:
        return False, "Invalid @context. Expected HSML context."

    entity_type = json_data.get("@type")
    
    # Check if @type is in the schema
    if entity_type not in hsml_schema["@graph"]:
        return False, f"Unknown entity type: {entity_type}"

    entity_schema = next((item for item in hsml_schema["@graph"] if item["@id"] == entity_type), None)

    if not entity_schema:
        return False, f"Entity type {entity_type} is not defined in HSML."

    # Extract required fields dynamically
    required_fields = [field["@id"] for field in entity_schema.get("required", [])]
    missing_fields = [field for field in required_fields if field not in json_data]

    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"

    return True, None

def generate_did_key():
    """Generate a DID:key pair using CLI tool"""
    result = subprocess.run(["python", "CLItool.py", "--export-private"], capture_output=True, text=True)
    
    if "Generated DID:key" not in result.stdout:
        return None, None, "Failed to generate DID"
    
    did_key = result.stdout.split("Generated DID:key: ")[1].split("\n")[0]
    
    private_key_path = "private_key.pem"
    
    return did_key, private_key_path, None

def store_in_mysql(did_key, public_key, metadata, registered_by):
    """Store DID, public key, and metadata in MySQL"""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    query = """
    INSERT INTO did_keys (did, public_key, metadata, registered_by) 
    VALUES (%s, %s, %s, %s)
    """
    try:
        cursor.execute(query, (did_key, public_key, json.dumps(metadata), registered_by))
        conn.commit()
        return True, None
    except mysql.connector.Error as err:
        return False, str(err)
    finally:
        cursor.close()
        conn.close()

@app.route('/register', methods=['POST'])
def register_entity():
    """API Endpoint for Entity Registration"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    json_data = json.load(file)

    # Step 1: Fetch HSML schema
    hsml_schema = fetch_hsml_schema()
    if not hsml_schema:
        return jsonify({"error": "Failed to retrieve HSML schema"}), 500

    # Step 2: Validate JSON
    is_valid, error = validate_json(json_data, hsml_schema)
    if not is_valid:
        return jsonify({"error": error}), 400
    
    entity_type = json_data["@type"]
    swid = json_data.get("swid", None)

    # Step 3: Check SWID existence
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT did FROM did_keys WHERE metadata->>'$.swid' = %s", (swid,))
    existing_record = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if existing_record:
        return jsonify({"warning": "SWID already exists. This will overwrite the existing entry."})
    
    # Step 4: Generate DID Key
    did_key, private_key_path, error = generate_did_key()
    if error:
        return jsonify({"error": error}), 500
    
    json_data["swid"] = did_key  # Attach did:key to SWID property
    
    # Step 5: Store in MySQL
    success, error = store_in_mysql(did_key, did_key.split(":")[-1], json_data, did_key)
    if not success:
        return jsonify({"error": error}), 500
    
    # Step 6: Kafka Topic Creation (For Agents & Credentials)
    if entity_type in ["Agent", "Credential"]:
        topic_name = json_data["name"].replace(" ", "_").lower()
        producer.send(topic_name, {"message": f"New {entity_type} registered: {json_data['name']}"})
    
    # Step 7: Provide response with private key
    response = {
        "message": "Entity registered successfully",
        "did": did_key,
        "private_key_path": private_key_path,
        "updated_json": json_data
    }
    return jsonify(response), 201

if __name__ == '__main__':
    app.run(debug=True)
