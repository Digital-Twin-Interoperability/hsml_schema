import json
import os
import subprocess
import random
import string
import mysql.connector

# MySQL Database Configuration
db_config = {
    "host": "localhost", # Put here instead the EC2 IP address
    "user": "root",
    "password": "MoonwalkerJPL85!",
    "database": "did_registry"
}

# Connect to MySQL
def connect_db():
    return mysql.connector.connect(**db_config)


###### MODIFY EACH OF THESE FOR EACH ENTITY #######
did_key = "did:key:6MkhaP2tuJVTJQ16Xna4yqXn9hD3a32ermE82niVS4kF2t1"  # Replace

public_key_part = did_key.replace("did:key:", "")

json_path = "Your Path to the hsml schema repo/hsml_schema/scripts/demoRegisteredEntities/entity_name.json" # Replace
try:
    with open(json_path, "r") as file:
        data = json.load(file)
except json.JSONDecodeError:
    raise ValueError("Invalid JSON format")
metadata_json = json.dumps(data)

# Note: For Persons, put the same as did_key; for the Agents put the one of the creator; for the Credentials; put the one of the issued by field in the JSON
registered_by = "did:key:OfThePersonWhoRegisteredTheEntity" # Replace 

# For Persons and Credentials leave as None
topic_name = None # Replace for Agents

# For Persons and Credentials leave as None
allowed_did = None # Replace for Agents (put the one of the other Agent)


###### SEND TO THE DATABASE ##########

# Connect to DB
db = connect_db()
cursor = db.cursor()

# Store in MySQL
cursor.execute(
    "REPLACE INTO did_keys (did, public_key, metadata, registered_by, kafka_topic, allowed_did) VALUES (%s, %s, %s, %s, %s, %s)",
    (did_key, public_key_part, metadata_json, registered_by, topic_name, allowed_did)
)
db.commit()
db.close()