from confluent_kafka import Producer

# Replace with the IP address of your Kafka broker
kafka_broker = '192.168.1.55:9092'

# Callback to confirm message delivery
def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

# Create a producer instance
producer = Producer({'bootstrap.servers': kafka_broker})

# Send a test message to a topic
topic_name = 'test-topic'
message = 'Hello from Confluent Kafka Producer from Laptop of Alicia!'

try:
    producer.produce(topic_name, value=message, callback=delivery_report)
    producer.flush()  # Wait for all messages to be delivered
except Exception as e:
    print(f"Error producing message: {e}")
