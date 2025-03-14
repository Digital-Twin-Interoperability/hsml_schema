from confluent_kafka import Producer
import json
import time
import os

# Kafka server details
kafka_server = '192.168.1.55:9092'
topic = 'unreal-hsml-topic'
client_id = 'unreal-rover-producer'

# JSON file path
json_file_path = os.path.join(os.path.expanduser("~"), "Desktop", "kafkaUnrealProducer_hsml.json")

# Initialize Kafka producer
producer_config = {
    'bootstrap.servers': kafka_server,
    'client.id': client_id
}
producer = Producer(producer_config)

def send_json_to_kafka():
    try:
        while True:
            try:
                # Check if the file exists
                if os.path.exists(json_file_path):
                    # Read JSON data from the file
                    with open(json_file_path, 'r') as json_file:
                        json_data = json.load(json_file)
                    
                    # Convert JSON data to string format
                    json_data_str = json.dumps(json_data)

                    # Send JSON data to Kafka topic
                    producer.produce(topic, key=client_id, value=json_data_str)
                    producer.flush()  # Ensure message is sent
                    print(f"Sent data to Kafka: {json_data_str}")

                else:
                    print("JSON file not found.")

            except PermissionError as e:
                print(f"Permission error: {e}. Retrying in 0.1 seconds...")
                time.sleep(0.01)  # Short delay before retrying

            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}. Skipping this iteration.")
                # This happens if the file is being written to and is incomplete
                time.sleep(0.01)  # Short delay before retrying

            except Exception as e:
                print(f"Unexpected error: {e}. Retrying in 0.1 seconds...")
                time.sleep(0.01)  # Catch any other unexpected errors

            # Wait before rechecking the file
            time.sleep(0.03)

    except KeyboardInterrupt:
        print("Stopping Kafka producer.")
    finally:
        producer.flush()  # Ensure all messages are sent before closing

# Run the function
send_json_to_kafka()
