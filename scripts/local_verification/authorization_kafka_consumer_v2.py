import json
import time
import threading
from confluent_kafka import Consumer, KafkaException
import keyboard
from CLItool import extract_did_from_private_key
import mysql.connector

# Configuration for Kafka broker
KAFKA_CONFIG = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'consumer_group',
    'auto.offset.reset': 'earliest'
}

# MySQL Database Configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "MoonwalkerJPL85!",
    "database": "did_registry"
}

authenticated = False

def authenticate_consumer(private_key_path, topic):
    global authenticated
    print(f"Loading private key from: {private_key_path}")
    consumer_did = extract_did_from_private_key(private_key_path)
    
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT allowed_did FROM did_keys WHERE kafka_topic = %s", (topic,))
    result = cursor.fetchone()
    db.close()
    
    if result and result["allowed_did"]:
        allowed_dids = result["allowed_did"].split(",")
        if consumer_did in allowed_dids:
            print(f"Authentication successful. {consumer_did} is authorized for topic {topic}.")
            authenticated = True
        else:
            print(f"Authentication failed. {consumer_did} is NOT authorized for topic {topic}.")
    else:
        print(f"Authentication failed. No allowed consumers for {topic}.")
    
    return authenticated

def receive_messages(consumer, topic):
    print(f"Listening for messages on topic '{topic}'... Press 'Esc' to stop.")
    while authenticated:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            raise KafkaException(msg.error())
        print(f"Received message: {msg.value().decode('utf-8')}")
        if keyboard.is_pressed("esc"):
            print("Stopping consumer.")
            break

def main():
    private_key = input("Enter directory to your private key: ")
    topic = input("Enter the Kafka topic: ")
    
    if authenticate_consumer(private_key, topic):
        consumer = Consumer(KAFKA_CONFIG)
        consumer.subscribe([topic])
        receive_messages(consumer, topic)
        consumer.close()
    print("Consumer stopped.")

if __name__ == "__main__":
    main()
