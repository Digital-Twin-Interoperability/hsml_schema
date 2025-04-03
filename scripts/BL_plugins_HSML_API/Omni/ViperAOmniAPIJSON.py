import requests
import json
import time

# API endpoint base
API_URL = "http://192.168.1.55:8000/consumer"

# Paths and topic
private_key_path = r"/home/luke-cortez/dt_interoperability/Omni_scripts/HSMLdemo/demoRegisteredEntities/private_key_Cadre_A.pem" # Key of the Producer Agent of Omniverse
topic = "viper_a_0wawiy"
output_file_path = r"/home/luke-cortez/dt_interoperability/Omni_scripts/HSMLdemo/kafkaOmniConsumer_1.json"

# Step 0: Read private key
try:
    private_key_file = open(private_key_path, "rb")
except Exception as e:
    print(f"Error reading private key: {e}")
    exit(1)

# Step 1: Authorize
auth_response = requests.post(
    f"{API_URL}/authorize",
    params={"topic": topic},
    files={"private_key": private_key_file}
)
print(auth_response.json())

# Step 2: Start consumer
start_response = requests.post(f"{API_URL}/start", params={"topic": topic})
print(start_response.json())

# Step 3: Poll and fetch latest HSML message
print("Polling latest messages from HSML API. Press Ctrl+C to stop.\n")
try:
    while True:
        response = requests.get(f"{API_URL}/latest-message", params={"topic": topic})
        if response.status_code == 200:
            hsml_data = response.json()

            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(hsml_data, f, indent=4)
                print(f"Message written to: {output_file_path}")
        else:
            print("No new message yet or error fetching.")

        time.sleep(1)  # Poll every second
except KeyboardInterrupt:
    print("Stopped by user.")

# Step 4: Stop consumer
stop_response = requests.post(f"{API_URL}/stop", params={"topic": topic})
print(stop_response.json())
