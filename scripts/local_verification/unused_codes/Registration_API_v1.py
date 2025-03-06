import json
import subprocess
import mysql.connector
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka import Producer

# Kafka Configuration
KAFKA_CONFIG = {
    "bootstrap.servers": "localhost:9092"
}
admin_client = AdminClient(KAFKA_CONFIG)
producer = Producer(KAFKA_CONFIG)

# MySQL Database Configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "MoonwalkerJPL85!",
    "database": "did_registry"
}

# Connect to MySQL
def connect_db():
    return mysql.connector.connect(**db_config)

# Function to create a Kafka topic for Agents
def create_kafka_topic(topic_name, num_partitions=1, replication_factor=1):
    """Creates a Kafka topic using Confluent Kafka AdminClient"""
    topic_list = [NewTopic(topic_name, num_partitions=num_partitions, replication_factor=replication_factor)]
    fs = admin_client.create_topics(topic_list)
    
    for topic, f in fs.items():
        try:
            f.result()  # Block until topic creation is done
            print(f"Kafka topic '{topic}' created successfully.")
        except Exception as e:
            print(f"Failed to create topic '{topic}': {e}")

# Function to send a Kafka message
def send_kafka_message(topic, message):
    """Sends a message to a Kafka topic"""
    try:
        producer.produce(topic, json.dumps(message))
        producer.flush()
        print(f"Message sent to Kafka topic '{topic}': {message}")
    except Exception as e:
        print(f"Failed to send message to Kafka topic '{topic}': {e}")

# Function to generate DID:key using CLI tool
def generate_did_key():
    """Runs the CLI tool to generate a DID:key and private key"""
    result = subprocess.run(["python", "CLItool.py", "--export-private"], capture_output=True, text=True)
    output = result.stdout.split("\n")
    
    did_key = None
    for line in output:
        if "Generated DID:key:" in line:
            did_key = line.split("Generated DID:key: ")[1]
    
    if not did_key:
        raise ValueError("Failed to generate DID:key")

    return did_key, "private_key.pem"  # Private key is stored in a file

# Function to validate JSON and register entity
def register_entity(json_file_path):
    """Validates, registers, and stores an HSML entity"""
    try:
        with open(json_file_path, "r") as file:
            data = json.load(file)
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON format"}

    # Check @context for HSML
    if "@context" not in data or "https://digital-twin-interoperability.github.io/hsml-schema-context/hsml.jsonld" not in data["@context"]:
        return {"status": "error", "message": "Not a valid HSML JSON"}

    # Check for required fields based on type
    entity_type = data.get("@type")
    required_fields = {
        "Entity": ["name", "description"],
        "Person": ["name", "birthDate", "email"],
        "Agent": ["name", "creator", "dateCreated", "dateModified", "description"],
        "Credential": ["name", "description", "issuedBy", "accessAuthorization", "authorizedForDomain"]
    }
    
    if entity_type not in required_fields:
        return {"status": "error", "message": "Unknown or missing entity type"}

    missing_fields = [field for field in required_fields[entity_type] if field not in data]
    if missing_fields:
        return {"status": "error", "message": f"Missing required fields: {missing_fields}"}

    # Check if SWID exists in DB
    swid = data.get("swid")
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM did_keys WHERE did = %s", (swid,))
    existing = cursor.fetchone()[0]
    
    if existing:
        print(f"Warning: SWID '{swid}' already exists and will be overwritten.")

    # Generate a new DID:key
    did_key, private_key_path = generate_did_key()
    data["swid"] = did_key  # Attach new DID:key to swid

    # Store in MySQL
    cursor.execute(
        "REPLACE INTO did_keys (did, public_key, metadata) VALUES (%s, %s, %s)",
        (did_key, did_key, json.dumps(data))
    )
    db.commit()
    db.close()

    # Special case: If entity is an "Agent", create a Kafka topic
    if entity_type == "Agent":
        topic_name = data["name"].replace(" ", "_").lower()
        create_kafka_topic(topic_name)
        send_kafka_message(topic_name, {"message": f"New Agent registered: {data['name']}"})

    return {
        "status": "success",
        "message": "Entity registered successfully",
        "did_key": did_key,
        "private_key_path": private_key_path,
        "updated_json": data
    }

# Example usage
if __name__ == "__main__":
    json_file_path = "C:/Users/abarrio/OneDrive - JPL/Desktop/Digital Twin Interoperability/Codes/HSML Examples/Examples 2025-02-03/entityExample/entityExample.json"  # Provide your JSON file
    result = register_entity(json_file_path)
    print(result)
