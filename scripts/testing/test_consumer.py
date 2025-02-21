from confluent_kafka import Consumer

# Replace with the IP address of your Kafka broker
kafka_broker = '192.168.1.55:9092'

# Create a consumer instance
consumer = Consumer({
    'bootstrap.servers': kafka_broker,
    'group.id': 'test-group',  # Consumer group ID
    'auto.offset.reset': 'earliest'  # Start reading from the beginning
})

topic_name = 'test-topic'

try:
    consumer.subscribe([topic_name])
    print(f"Connected to topic '{topic_name}'. Waiting for messages...\n")
    
    while True:
        msg = consumer.poll(1.0)  # Poll for messages (timeout = 1 second)
        if msg is None:
            continue  # No message, try again
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue

        print(f"Received message: {msg.value().decode('utf-8')}")
except KeyboardInterrupt:
    print("Consumer stopped.")
finally:
    consumer.close()
