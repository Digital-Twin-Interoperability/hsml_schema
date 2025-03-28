from omni.kit.scripting import BehaviorScript
from pxr import Gf, UsdGeom, Usd
import omni.usd
import json
from datetime import datetime
import requests

# API endpoints
API_URL = "http://192.168.1.55:8000/producer"

# Request data
private_key_path = "PATH/TO/private_key_CadreA.pem"
topic = "cadreA_new_topic"

# Dictionary to store the previous state for all tracked prims
previous_states = {}

# Authenticate once at the beginning
with open(private_key_path, "rb") as key_file:
    auth_response = requests.post(
        f"{API_URL}/authenticate",
        params={"topic": topic},
        files={"private_key": key_file}
    )
print(auth_response.json())

# Function to send full message
def send_full_message(schema_id, modelName, modelNumber, objectLink, creatorName, creationDate, modifiedDate, position, rotation):
    hsml_message = {
        "@context": "https://digital-twin-interoperability.github.io/hsml-schema-context/hsml.jsonld",
        "@type": "Agent",
        "name": modelName,
        "swid": f"did:key:{schema_id}",
        "url": objectLink,
        "creator": {
            "@type": "Person",
            "name": creatorName,
            "swid": "did:key:personMustBeRegisteredBefore"
        },
        "dateCreated": creationDate,
        "dateModified": modifiedDate,
        "encodingFormat": "application/x-obj",
        "contentUrl": "https://example.com/models/3dmodel-001.obj",
        "description": "Rover data with world position and rotation",
        "platform": "Omniverse",
        "inControl": True,
        "spaceLocation": [
            {
                "@type": "Hyperspace",
                "name": "Moon"
            }
        ],
        "position": [
            {
                "@type": "schema:PropertyValue",
                "name": "xCoordinate",
                "value": position[0]
            },
            {
                "@type": "schema:PropertyValue",
                "name": "yCoordinate",
                "value": position[1]
            },
            {
                "@type": "schema:PropertyValue",
                "name": "zCoordinate",
                "value": position[2]
            }
        ],
        "rotation": [
            {
                "@type": "schema:PropertyValue",
                "name": "rx",
                "value": rotation[1]
            },
            {
                "@type": "schema:PropertyValue",
                "name": "ry",
                "value": rotation[2]
            },
            {
                "@type": "schema:PropertyValue",
                "name": "rz",
                "value": rotation[3]
            },
            {
                "@type": "schema:PropertyValue",
                "name": "w",
                "value": rotation[0]
            }
        ],
        "additionalProperty": [
            {
                "@type": "schema:PropertyValue",
                "name": "scale",
                "value": 100
            }
        ]
    }

    # Send the full message to Kafka
    response = requests.post(
        f"{API_URL}/send-message",
        params={"topic": topic},
        json=hsml_message
    )
    print(f"Sent message to HSML API for {modelName}:{response.json()}")

# Isaac Sim Class
class OmniControls(BehaviorScript):
    def on_init(self):
        print("CONTROLS TEST INIT")
        stage = omni.usd.get_context().get_stage()
        # List of prims to track
        self.prims = [
            stage.GetPrimAtPath("/World/Omni_Cadre/CADRE_Demo/Chassis"),
        ]

    def on_play(self):
        print("CONTROLS TEST PLAY")
        for prim in self.prims:
            prim_name = prim.GetName()
            schema_id = f"schema_{prim_name}"  # Use the prim's name for schema_id

            # Initialize previous state for this prim
            previous_states[prim_name] = {
                "x": None,
                "y": None,
                "z": None,
                "rx": None,
                "ry": None,
                "rz": None,
                "w": None
            }

            print(f"Tracking prim: {prim_name} with schema_id: {schema_id}")

    def get_transform(self, prim):
        # Get the world transformation matrix
        matrix: Gf.Matrix4d = omni.usd.get_world_transform_matrix(prim)
        translate: Gf.Vec3d = matrix.ExtractTranslation()  # Absolute world position
        rotation: Gf.Rotation = matrix.ExtractRotation()  # Absolute world rotation
        rotation_quaternion = rotation.GetQuaternion()
        return {
            "translate": translate,
            "rotation": [
                rotation_quaternion.GetReal(),  # w value first
                rotation_quaternion.GetImaginary()[0],
                rotation_quaternion.GetImaginary()[1],
                rotation_quaternion.GetImaginary()[2]
            ]
        }

    def has_state_changed(self, prim_name, position, rotation):
        prev = previous_states[prim_name]
        has_changed = (
            prev["x"] != position[0] or prev["y"] != position[1] or prev["z"] != position[2] or
            prev["rx"] != rotation[1] or prev["ry"] != rotation[2] or 
            prev["rz"] != rotation[3] or prev["w"] != rotation[0]
        )

        if has_changed:
            # Update the previous state
            previous_states[prim_name] = {
                "x": position[0], "y": position[1], "z": position[2],
                "rx": rotation[1], "ry": rotation[2], "rz": rotation[3], "w": rotation[0]
            }

        return has_changed

    def on_update(self, current_time: float, delta_time: float):
        # Iterate over all prims and send updates if state has changed
        for prim in self.prims:
            prim_name = prim.GetName()
            schema_id = f"schema_{prim_name}"
            transform = self.get_transform(prim)
            position = [transform["translate"][0], transform["translate"][1], transform["translate"][2]]
            rotation = transform["rotation"]

            # Check for state change before sending a message
            if self.has_state_changed(prim_name, position, rotation):
                send_full_message(
                    schema_id=schema_id,
                    modelName=prim_name,
                    modelNumber="001",
                    objectLink="https://example.com/3dmodel",
                    creatorName="Jared Carrillo",
                    creationDate="2024-01-01",
                    modifiedDate=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                    position=position,
                    rotation=rotation
                )
