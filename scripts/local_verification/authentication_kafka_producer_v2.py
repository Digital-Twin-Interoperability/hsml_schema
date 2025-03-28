import json
import time
import threading
from confluent_kafka import Producer
import keyboard
from CLItool import extract_did_from_private_key
import mysql.connector

# Configuration for Kafka broker
KAFKA_CONFIG = {
    'bootstrap.servers': 'localhost:9092'
}

# MySQL Database Configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "MoonwalkerJPL85!",
    "database": "did_registry"
}

authenticated = False

def delivery_report(err, msg):
    if err is not None:
        print(f'Error: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

def authenticate(producer, private_key_path, topic):
    global authenticated
    print(f"Loading private key from: {private_key_path}")
    producer_did = extract_did_from_private_key(private_key_path)
    
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT did FROM did_keys WHERE did = %s AND kafka_topic = %s", (producer_did, topic))
    result = cursor.fetchone()
    db.close()
    
    if result:
        print(f"Authentication successful. {producer_did} is authorized for topic {topic}.")
        authenticated = True
    else:
        print(f"Authentication failed. {producer_did} is NOT authorized for topic {topic}.")
        authenticated = False

def send_data(producer, topic):
    while authenticated:
        message = json.dumps({"data": "Simulation update"})
        producer.produce(topic, message.encode('utf-8'), callback=delivery_report)
        producer.flush()
        time.sleep(1)
        if keyboard.is_pressed('q'):
            print("Stopping producer.")
            break

def main():
    private_key = input("Enter directory to your private key: ")
    topic = input("Enter the Kafka topic: ")
    producer = Producer(KAFKA_CONFIG)
    authenticate(producer, private_key, topic)
    if authenticated:
        send_data(producer, topic)
    print("Producer stopped.")

if __name__ == "__main__":
    main()
