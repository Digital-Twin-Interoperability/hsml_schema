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

allowed_did_change = "did:key:6Mkq47kEVpasYSLxc2DM1951tSw2hPQyT7nhdVrnT6YawM5"
did_key = "did:key:6MkhaP2tuJVTJQ16Xna4yqXn9hD3a32ermE82niVS4kF2t1" # Example Agent 4

# Store Kafka topic in the database
db = connect_db()
cursor = db.cursor()
cursor.execute(
"UPDATE did_keys SET allowed_did = %s WHERE did = %s",
(allowed_did_change, did_key)
)
db.commit()
db.close()