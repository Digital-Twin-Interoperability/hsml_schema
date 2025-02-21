from confluent_kafka import Consumer

# Create a consumer instance
consumer = Consumer({
    "bootstrap.servers": "localhost:9092",
    "group.id": "my_consumer_group", # Not sure about this
    "auto.offset.reset": "earliest"
})

topic_name = 'example_agent_4'

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
