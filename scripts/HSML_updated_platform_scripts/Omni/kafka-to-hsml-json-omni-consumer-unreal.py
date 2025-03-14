import json
from confluent_kafka import Consumer, KafkaException, KafkaError

# Configuration for Kafka Consumer
conf = {
    'bootstrap.servers': '192.168.1.55:9092',  # Kafka broker address
    'group.id': 'my-consumer11-group',  # Consumer group ID
    'auto.offset.reset': 'latest',  # Start reading from the latest message
    'enable.auto.commit': False,  # Don't commit offsets automatically
}

# Create Consumer instance
consumer = Consumer(conf)

# Subscribe to the topic
consumer.subscribe(['unreal-hsml-topic'])

# File path for the output JSON file
file_path = r"C:\Users\Jared\Desktop\kafkaOmniConsumer_2_hsml.json"

try:
    while True:
        # Poll for messages
        msg = consumer.poll(timeout=1.0)  # Timeout after 1 second if no message

        if msg is None:
            continue  # No message available within timeout
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                # End of partition reached (only log this)
                continue
            else:
                raise KafkaException(msg.error())

        # Assuming the message is already in JSON format
        message_data = msg.value().decode('utf-8')  # Decode the message

        try:
            # Try to parse the message as JSON
            parsed_message = json.loads(message_data)

            # Open the file in write mode to overwrite the content with each message
            with open(file_path, 'w', encoding='utf-8') as file:
                # Write the parsed JSON message to the file, overwriting it each time
                json.dump(parsed_message, file, ensure_ascii=False, indent=4)
                print(f"Written message to {file_path}")

        except json.JSONDecodeError:
            print("Received message is not valid JSON, skipping...")

except KeyboardInterrupt:
    print("Consumer interrupted")

finally:
    # Close the consumer cleanly
    consumer.close()
