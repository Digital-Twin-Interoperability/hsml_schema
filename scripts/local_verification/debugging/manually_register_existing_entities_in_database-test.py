import json
import mysql.connector

# MySQL Database Configuration
db_config = {
    "host": "52.202.163.49", # Put here instead the EC2 IP address if you're connecting to EC2 from your laptop's terminal
    "user": "labuser",
    "password": "MoonwalkerJPL85!",
    "database": "did_registry"
}

# Connect to MySQL
def connect_db():
    return mysql.connector.connect(**db_config)


###### MODIFY EACH OF THESE FOR EACH ENTITY #######
did_key = "did:key:6MkfEe4cTUbgQm47SRYBZ61KQSiobVdbQ2r7zFL13jtYD7t"  # Replace

public_key_part = did_key.replace("did:key:", "")

json_path = "C:/Users/abarrio/OneDrive - JPL/Desktop/Digital Twin Interoperability/Codes/demoRegisteredEntities/Feedback_Channel_for_Cadre_A_and_Viper_A.json" # Replace

try:
    with open(json_path, "r") as file:
        data = json.load(file)
except json.JSONDecodeError:
    raise ValueError("Invalid JSON format")
metadata_json = json.dumps(data)

# Note: For Persons, put the same as did_key; for the Agents put the one of the creator; for the Credentials; put the one of the issued by field in the JSON
registered_by = "did:key:6MktsGJxcNwZaC1vuimSYai7Zs9ykPwwrAfeVQtMLDU3nqQ" # Replace 

# For Persons and Credentials leave as None
topic_name = "feedback_channel" # Replace for Agents

# For Persons and Credentials leave as None
allowed_did = "did:key:6MkpwzV9tEHwpxkadMdWGZdXdzQSKVyih4y1zVcA13Bv6K2,did:key:6MkfqM9m882vjWv9ex9HkBQitUQWcCNw8KKfB5vEwRLGrFS" # Replace for Agents (put the one of the other Agent)


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