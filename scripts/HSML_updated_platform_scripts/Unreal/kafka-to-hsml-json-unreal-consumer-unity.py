import json
import time
from confluent_kafka import Consumer, KafkaException, KafkaError

# Configuration for Kafka Consumer
conf = {
    'bootstrap.servers': '192.168.1.55:9092',  # Kafka broker address
    'group.id': 'my-consumer131-group',  # Consumer group ID
    'auto.offset.reset': 'latest',  # Start reading from the latest message
    'enable.auto.commit': False,  # Don't commit offsets automatically
}

# Create Consumer instance
consumer = Consumer(conf)

# Subscribe to the topic
consumer.subscribe(['unity-hsml-topic'])

# File path for the output JSON file
file_path = r"C:\Users\Jared\Desktop\kafkaUnrealConsumer_2_hsml.json"

# Maximum number of retries before giving up
max_retries = 5
retry_delay = 0.5  # seconds to wait before retrying

# Time interval between writes (in seconds) to achieve 30 writes per second
write_interval = 1 / 30  # approximately 0.0333 seconds

try:
    last_write_time = time.time()  # Initialize the last write time

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

            # Check if enough time has passed since the last write
            current_time = time.time()
            time_since_last_write = current_time - last_write_time

            if time_since_last_write >= write_interval:
                # Retry logic to handle file being locked or in use
                retries = 0
                while retries < max_retries:
                    try:
                        # Open the file in write mode to overwrite the content with each message
                        with open(file_path, 'w', encoding='utf-8') as file:
                            # Write the parsed JSON message to the file, overwriting it each time
                            json.dump(parsed_message, file, ensure_ascii=False, indent=4)
                            print(f"Written message to {file_path}")
                            last_write_time = current_time  # Update the last write time
                            break  # Exit the retry loop if the write is successful
                    except IOError as e:
                        if e.errno == 13:  # Permission error or file in use
                            retries += 1
                            print(f"File is locked, retrying {retries}/{max_retries}...")
                            time.sleep(retry_delay)  # Wait before retrying
                        else:
                            raise  # Raise any other IO error
                else:
                    if retries == max_retries:
                        print(f"Failed to write to {file_path} after {max_retries} retries.")

            else:
                # Sleep for the remaining time to maintain the 30 writes per second
                time_to_wait = write_interval - time_since_last_write
                if time_to_wait > 0:
                    time.sleep(time_to_wait)

        except json.JSONDecodeError:
            print("Received message is not valid JSON, skipping...")

except KeyboardInterrupt:
    print("Consumer interrupted")

finally:
    # Close the consumer cleanly
    consumer.close()
