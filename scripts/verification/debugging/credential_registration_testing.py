import json
import os
import subprocess
import mysql.connector
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka import Producer
from CLItool import extract_did_from_private_key

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


# Function to validate JSON and register entity
def register_entity_testing(json_file_path, output_directory, registered_by=None):
    """Validates, registers, and stores an HSML entity"""
    try:
        with open(json_file_path, "r") as file:
            data = json.load(file)
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON format"}
    
    # Check if JSON file is actually JSON
    if not isinstance(data, dict):
        return {"status": "error", "message": "Uploaded file is not a valid JSON object"}

    # Check @context for HSML
    if "@context" not in data or "https://digital-twin-interoperability.github.io/hsml-schema-context/hsml.jsonld" not in data["@context"]:
        return {"status": "error", "message": "Not a valid HSML JSON"}
    print("HSML JSON accepted.")

    # Check for required fields based on type
    entity_type = data.get("@type")
    required_fields = {
        "Credential": ["name", "description", "issuedBy", "accessAuthorization", "authorizedForDomain"],
    }
    if entity_type not in required_fields:
        return {"status": "error", "message": "Unknown or missing entity type"}
    missing_fields = [field for field in required_fields[entity_type] if field not in data]
    if missing_fields:
        return {"status": "error", "message": f"Missing required fields: {missing_fields}"}

    # Special case: If entity is a "Credential", more checks needed
    if entity_type == "Credential":
        issued_by_did = data.get("issuedBy", {}).get("swid") # SWID of user registering Credential
        authorized_for_domain_did = data.get("authorizedForDomain", {}).get("swid") # SWID of Domain that Credential is giving access to
        credential_domain_name = data.get("authorizedForDomain", {}).get("name") # Name of Domain that Credential is giving access to
        access_authorization_did = data.get("accessAuthorization",{}).get("swid") # SWID of new Domain/Person/Organization that Credential is granting access authorization
        access_authorization_type = data.get("accessAuthorization",{}).get("@type") # Type of new Domain/Person/Organization that Credential is granting access authorization
        access_authorization_name = data.get("accessAuthorization",{}).get("name") # Name of new Domain/Person/Organization that Credential is granting access authorization

        print(f"'{issued_by_did}', '{authorized_for_domain_did}', '{credential_domain_name}', '{access_authorization_did}','{access_authorization_type}','{access_authorization_name}' ")

        if not (issued_by_did and authorized_for_domain_did and access_authorization_did):
            raise ValueError("Missing required 'swid' in Credential fields")

        # Ensure issuedBy matches the logged in User's swid registering the Credential
        if issued_by_did != registered_by:
            raise ValueError("issuedBy field must match the User registering the Credential")

        # Verify authorizedForDomain ownership 
        #private_key_path_credential_domain = input(f"Provide your private_key.pem path for '{credential_domain_name}' this Credential is giving access to: ")
        private_key_path_credential_domain = "C:/Users/abarrio/OneDrive - JPL/Desktop/Digital Twin Interoperability/Codes/HSML Examples/registeredExamples/private_key_example_agent_4.pem"
        credential_domain_did = extract_did_from_private_key(private_key_path_credential_domain)
        print(f"credential_domain DID: {credential_domain_did}")

        if credential_domain_did != authorized_for_domain_did:
            print(f"Invalid private_key.pem for '{credential_domain_name}'")
            return None
        
        db = connect_db()
        cursor = db.cursor()
        cursor.execute("SELECT metadata FROM did_keys WHERE did = %s", (authorized_for_domain_did,))
        domain_did_result = cursor.fetchone()
        if not domain_did_result:
            print(f"DID not found in database. Please register '{credential_domain_name}' first.")
            return None

        # Update authorizedForDomain's metadata to include the new accessAuthorization swid in "canAccess"
        domain_data = json.loads(domain_did_result[0])
        print(domain_data)
        new_access_auth = data.get("accessAuthorization", {})
        #print(f"{domain_data}")
        if "canAccess" not in domain_data:
            # Write canAccess property
            #domain_data["canAccess"] = data.get("accessAuthorization",{})
            domain_data["canAccess"] = [new_access_auth]
            #print(json.dumps(domain_data)) 
        else:
            # Attach to the existing canAccess property and existing allowed_did (fetch and merge)
            existing_can_access = domain_data.get("canAccess", [])
            
            # Ensure it's a list (sometimes it could be a single dict mistakenly)
            if not isinstance(existing_can_access, list):
                existing_can_access = [existing_can_access]
            
            # Extract existing swids to prevent duplicates
            existing_swids = {entry["swid"] for entry in existing_can_access if "swid" in entry}

            if new_access_auth.get("swid") and new_access_auth["swid"] not in existing_swids:
                existing_can_access.append(new_access_auth)
            else:
                print(f"{new_access_auth["swid"]} arlready has access to '{credential_domain_name}'")
            
            # Update the JSON structure with the merged list
            domain_data["canAccess"] = existing_can_access

        # Must dump also into metadata and save in location
            cursor.execute("UPDATE did_keys SET metadata = %s WHERE did = %s", (json.dumps(domain_data), authorized_for_domain_did))
            domain_output_directory = "C:/Users/abarrio/OneDrive - JPL/Desktop/Digital Twin Interoperability/Codes/HSML Examples/testing" # For testing
            domain_json_output = os.path.join(domain_output_directory, f"{domain_data['name'].replace(' ', '_')}.json")
            with open(domain_json_output, "w") as json_file:
                json.dump(domain_data, json_file, indent=4)
            print(f"Updated {credential_domain_name} JSON saved to: {domain_json_output}")
        
        # Now to dump into allowed_did
        # Fetch the existing allowed_did list from the database
        cursor.execute("SELECT allowed_did FROM did_keys WHERE did = %s", (authorized_for_domain_did,))
        allowed_did_result = cursor.fetchone()

        # Convert the existing allowed_did value into a list (splitting by comma)
        if allowed_did_result and allowed_did_result[0]:
            allowed_did_list = allowed_did_result[0].split(",")  # Stored as comma-separated values
        else:
            allowed_did_list = []  # Initialize as empty list if nothing exists

        # Add the new DID if it's not already present
        new_did = new_access_auth.get("swid")
        if new_did and new_did not in allowed_did_list:
            allowed_did_list.append(new_did)

        # Convert the list back into a comma-separated string for database storage
        allowed_did_string = ",".join(allowed_did_list)

        # Update the database with the modified allowed_did list
        cursor.execute("UPDATE did_keys SET allowed_did = %s WHERE did = %s", 
                    (allowed_did_string, authorized_for_domain_did))

        

    # Store in MySQL
    db.commit()
    db.close()

    return {
        "status": "success"
    }

if __name__ == "__main__":
    json_file_path = "C:/Users/abarrio/OneDrive - JPL/Desktop/Digital Twin Interoperability/Codes/HSML Examples/Examples 2025-02-24/credentialExample/credential_example_Agent_4.json"  # Provide your JSON file
    #json_file_path = input("Enter the directory to your HSML JSON to be registered: ")
    #output_directory = input("Enter the directory to save the private key and updated JSON: ")
    output_directory = "C:/Users/abarrio/OneDrive - JPL/Desktop/Digital Twin Interoperability/Codes/HSML Examples/registeredExamples"
    user_did = "did:key:6MktmNuF2PjyfLHd1pTKsu62ZPAMamzmGu6S2byfHUog2EA"
    
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    result = register_entity_testing(json_file_path, output_directory, registered_by=user_did)
    print(result)
    



