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

id = 3
did_key = " did:key:6MkhaP2tuJVTJQ16Xna4yqXn9hD3a32ermE82niVS4kF2t1"
new_json_path = "C:/Users/abarrio/OneDrive - JPL/Desktop/Digital Twin Interoperability/Codes/HSML Examples/registeredExamples/agent_Example_4.json"
try:
    with open(new_json_path, "r") as file:
        data = json.load(file)
except json.JSONDecodeError:
    raise ValueError("Invalid JSON format")

new_metadata_json = json.dumps(data)

# Store Kafka topic in the database
db = connect_db()
cursor = db.cursor()
cursor.execute("UPDATE did_keys SET metadata = %s WHERE did = %s", (new_metadata_json, did_key))
db.commit()
db.close()