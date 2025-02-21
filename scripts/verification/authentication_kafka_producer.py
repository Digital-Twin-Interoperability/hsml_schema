import json
import mysql.connector
from confluent_kafka import Producer
from CLItool import extract_did_from_private_key

## CODE to very the ownership of the Entity, to Authenticate the Kafka Producer

# Kafka Configuration
KAFKA_CONFIG = {
    "bootstrap.servers": "localhost:9092"
}
producer = Producer(KAFKA_CONFIG)

# MySQL Database Configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "MoonwalkerJPL85!",
    "database": "did_registry"
}

def authenticate_producer(private_key_path, topic):
    """Authenticates the producer before allowing message publishing."""
    print(f"Loading private key from: {private_key_path}")
    producer_did = extract_did_from_private_key(private_key_path)

    db = mysql.connector.connect(**db_config)
    cursor = db.cursor(dictionary=True)

    # Check if the DID is the one of the Agent sending the data (did) and matches topic name (kafka_topic)
    cursor.execute("SELECT did, kafka_topic FROM did_keys WHERE did = %s AND kafka_topic = %s", (producer_did, topic))
    result = cursor.fetchone()

    db.close()

    #
    #if result and result["did"] == producer_did:
    #    print(f"Authentication successful. {producer_did} is authorized to produce to {topic}")
    #    return True
    #else:
    #    print(f"Authentication failed. {producer_did} is NOT authorized to produce to {topic}")
    #    return False
    #
    if result:
        print(f"Authentication successful. {producer_did} is authorized to produce to {topic}")
        return True
    else:
        print(f"Authentication failed. {producer_did} is NOT authorized to produce to {topic}")
        return False

def send_kafka_message(topic, message, private_key_path):
    """Sends a Kafka message after verifying producer ownership."""
    if authenticate_producer(private_key_path, topic):
        producer.produce(topic, json.dumps(message))
        producer.flush()
        print(f"Message sent to Kafka topic '{topic}': {message}")
    else:
        print("Access denied. Unable to send message.")

# Example Usage
if __name__ == "__main__":
    #private_key = "private_key.pem"  # Path to user's private key
    private_key = input("Enter directory to your private key: ")
    # message = input("Enter message: ") # Change later instead of saying status:active
    send_kafka_message("example_agent_4", {"status": "active"}, private_key) # replace example_agent by agent_topic_name
