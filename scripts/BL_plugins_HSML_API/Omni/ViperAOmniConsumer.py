from omni.kit.scripting import BehaviorScript
from pxr import Gf, UsdGeom, Usd
import json
import os
import omni.usd


class FileReaderScript(BehaviorScript):
    def on_init(self):
        """Initialize the script."""
        global prim1
        stage = omni.usd.get_context().get_stage()
        
        # Viper prim
        prim_path = "/World/Unity_Viper"
        prim1 = stage.GetPrimAtPath(prim_path)

        if not prim1.IsValid():
            print(f"Error: Prim not found or invalid at path {prim_path}.")
            return

        # Ensure the prim is an Xform
        prim1 = UsdGeom.Xform(prim1)
        if not prim1:
            print(f"Error: Prim at {prim_path} is not a valid Xform.")
            return

        self.file_path = r"/home/luke-cortez/dt_interoperability/Omni_scripts/HSMLdemo/kafkaOmniConsumer_1.json"
        print(f"Script initialized. Watching file: {self.file_path}")

    def on_update(self, current_time: float, delta_time: float):
        """Read and extract specific values from the JSON file on every update."""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r') as file:
                    data = json.load(file)

                    # ✅ Extract position values
                    position_data = data.get("position", [])
                    position = {prop["name"]: prop["value"] for prop in position_data}

                    x = position.get("xCoordinate", 0)
                    z = position.get("yCoordinate", 0)
                    y = position.get("zCoordinate", 0)

                    # ✅ Extract rotation values (including w value now part of rotation)
                    rotation_data = data.get("rotation", [])
                    rotation = {prop["name"]: prop["value"] for prop in rotation_data}

                    rx = rotation.get("rx", 0)
                    ry = rotation.get("ry", 0)
                    rz = rotation.get("rz", 0)
                    w = rotation.get("w", 1)  # w is now part of the rotation array

                    # ✅ Desired world position and rotation
                    desired_position = Gf.Vec3d(x, y, z)
                    desired_rotation = Gf.Quatf(w, rx, ry, rz)

                    # ✅ Compute and apply local transform
                    parent_prim = prim1.GetPrim().GetParent()
                    parent_world_transform = UsdGeom.Xformable(parent_prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())

                    # Handle cases where the parent doesn't have a valid transform
                    if not parent_world_transform:
                        print(f"Warning: Parent prim at {parent_prim.GetPath()} has no transform. Using identity.")
                        parent_world_transform = Gf.Matrix4d(1.0)  # Identity matrix

                    parent_world_inverse = parent_world_transform.GetInverse()
                    local_position = parent_world_inverse.TransformAffine(desired_position)

                    # ✅ Apply transformations to the prim
                    xformable = UsdGeom.Xformable(prim1)

                    # Clear existing ops and apply the new transform
                    xformable.ClearXformOpOrder()
                    translate_op = xformable.AddTranslateOp()
                    translate_op.Set(local_position)

                    orient_op = xformable.AddOrientOp()
                    orient_op.Set(desired_rotation)

                    print(f"Prim updated: Local Position {local_position}, Rotation {desired_rotation}")

            else:
                print(f"File not found: {self.file_path}")
        except Exception as e:
            print(f"Error reading or updating prim: {e}")

    def on_shutdown(self):
        """Clean up resources if necessary."""
        print("Shutting down script.")
