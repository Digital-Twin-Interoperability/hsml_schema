import requests
import json
import os
import time

API_URL = "http://192.168.1.55:8000/producer"
private_key_path = "/home/luke-cortez/dt_interoperability/Omni_scripts/HSMLdemo/demoRegisteredEntities/private_key_Cadre_A.pem"
json_path = "/tmp/producerOmniUpdate.json"
topic = "cadre_a_qbnpru"

# Authenticate
with open(private_key_path, "rb") as key_file:
    auth_response = requests.post(
        f"{API_URL}/authenticate",
        params={"topic": topic},
        files={"private_key": key_file}
    )
    print(auth_response.json())

last_sent = {}

while True:
    try:
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)

            # Avoid re-sending same data
            if data == last_sent:
                time.sleep(1)
                continue

            hsml_message = {
                "@context": "https://digital-twin-interoperability.github.io/hsml-schema-context/hsml.jsonld",
                "@type": "Agent",
                "name": "Omni_Cadre",
                "swid": "did:key:6MkpwzV9tEHwpxkadMdWGZdXdzQSKVyih4y1zVcA13Bv6K2",
                "url": "https://example.com/3dmodel",
                "creator": {
                    "@type": "Person",
                    "name": "Alicia Sanjurjo",
                    "swid": "did:key:6MktsGJxcNwZaC1vuimSYai7Zs9ykPwwrAfeVQtMLDU3nqQ"
                },
                "dateCreated": "2024-01-01",
                "dateModified": data["modifiedDate"],
                "encodingFormat": "application/x-obj",
                "contentUrl": "https://example.com/models/3dmodel-001.obj",
                "description": "Rover data with world position and rotation",
                "platform": "Omniverse",
                "inControl": True,
                "spaceLocation": [{"@type": "Hyperspace", "name": "Moon"}],
                "position": [
                    {"@type": "schema:PropertyValue", "name": "xCoordinate", "value": data["position"][0]},
                    {"@type": "schema:PropertyValue", "name": "yCoordinate", "value": data["position"][1]},
                    {"@type": "schema:PropertyValue", "name": "zCoordinate", "value": data["position"][2]}
                ],
                "rotation": [
                    {"@type": "schema:PropertyValue", "name": "rx", "value": data["rotation"][1]},
                    {"@type": "schema:PropertyValue", "name": "ry", "value": data["rotation"][2]},
                    {"@type": "schema:PropertyValue", "name": "rz", "value": data["rotation"][3]},
                    {"@type": "schema:PropertyValue", "name": "w", "value": data["rotation"][0]}
                ],
                "additionalProperty": [
                    {"@type": "schema:PropertyValue", "name": "scale", "value": 100}
                ]
            }

            response = requests.post(f"{API_URL}/send-message", params={"topic": topic}, json=hsml_message)
            print(f"Message sent: {response.json()}")
            last_sent = data

    except Exception as e:
        print(f"Error: {e}")

    time.sleep(0.01)
