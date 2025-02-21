import json
from pyld import jsonld

# Path to your example file
example_file_path = 'C:/Users/abarrio/OneDrive - JPL/Desktop/Digital Twin Interoperability/HSML Schema/Examples/Examples 12-16/credentialExample.json'
# example_file_path = r'C:\Users\abarrio\OneDrive - JPL\Desktop\Digital Twin Interoperability\HSML Schema\Examples\Examples 12-16\credentialExample.json'


# Load the example JSON-LD file
with open(example_file_path, 'r') as f:
    example_jsonld = json.load(f)

# Print basic info about the JSON file
print("Loaded JSON file successfully")

# Expand the JSON-LD (this applies the context)
try:
    expanded_jsonld = jsonld.expand(example_jsonld)
    print("\n Expanded JSON-LD successfully \n")
    print(json.dumps(expanded_jsonld, indent=2))
except Exception as e:
    print("\n Error expanding JSON-LD ")
    print(str(e))
