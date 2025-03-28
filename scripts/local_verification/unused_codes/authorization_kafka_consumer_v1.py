import json
import mysql.connector
from confluent_kafka import Consumer, KafkaException
from CLItool import extract_did_from_private_key

## CODE to authenticate the Consumer, and check they have authorization to access the topic and receive messages

# Kafka Consumer Configuration
KAFKA_CONFIG = {
    "bootstrap.servers": "localhost:9092",
    "group.id": "my_consumer_group", # Not sure about this
    "auto.offset.reset": "earliest"
}

# MySQL Database Configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "MoonwalkerJPL85!",
    "database": "did_registry"
}


def authenticate_consumer(private_key_path, topic):
    """Authenticates the consumer before allowing subscription to a topic."""
    consumer_did = extract_did_from_private_key(private_key_path)
    print(consumer_did)

    db = mysql.connector.connect(**db_config)
    cursor = db.cursor(dictionary=True)

    # Retrieve allowed DID keys for the topic
    cursor.execute("SELECT allowed_did FROM did_keys WHERE kafka_topic = %s", (topic,))
    result = cursor.fetchone()
    
    db.close()

    if result and result["allowed_did"]:
        allowed_dids = result["allowed_did"].split(",")  # Convert CSV to list
        if consumer_did in allowed_dids:
            print(f"Authentication successful. {consumer_did} is authorized to consume from {topic}")
            return True
        else:
            print(f"Authentication failed. {consumer_did} is NOT authorized to consume from {topic}")
    else:
        print(f"Authentication failed. No allowed consumers for {topic}")
    
    return False

def consume_kafka_messages(topic, private_key_path):
    """Consumes Kafka messages only if authentication is successful."""
    if not authenticate_consumer(private_key_path, topic):
        print("Access denied. Unable to consume messages.")
        return

    consumer = Consumer(KAFKA_CONFIG)
    consumer.subscribe([topic])

    print(f"Listening for messages on topic '{topic}'...")

    try:
        while True:
            msg = consumer.poll(1.0)  # Wait for message (1 sec timeout)
            if msg is None:
                continue
            if msg.error():
                raise KafkaException(msg.error())

            print(f"Received message: {msg.value().decode('utf-8')}")
    except KeyboardInterrupt:
        print("Consumer interrupted.")
    finally:
        consumer.close()


# Example Usage
if __name__ == "__main__":
    private_key = "C:/Users/abarrio/OneDrive - JPL/Desktop/Digital Twin Interoperability/Codes/HSML Examples/registeredExamples/private_key_example_agent_2.pem"   # Path to user's private key
    #private_key = input("Enter directory to your private key: ")
    consume_kafka_messages("example_agent_4", private_key)
