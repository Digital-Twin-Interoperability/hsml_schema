import json
import os
import subprocess
import mysql.connector

# MySQL Database Configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "MoonwalkerJPL85!",
    "database": "did_registry"
}

# Connect to MySQL
def connect_db():
    return mysql.connector.connect(**db_config)

topic_name = "example_agent_3"
did_key = "did:key:6Mkk4dyAJmSPFKiWSVf3ZuzE2bpWqcxRbkBXiT7k9Fp8YNV"

# Store Kafka topic in the database
db = connect_db()
cursor = db.cursor()
cursor.execute(
"UPDATE did_keys SET kafka_topic = %s WHERE did = %s",
(topic_name, did_key)
)
db.commit()
db.close()