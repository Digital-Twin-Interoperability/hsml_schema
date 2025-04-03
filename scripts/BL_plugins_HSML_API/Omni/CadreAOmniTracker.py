from omni.kit.scripting import BehaviorScript
from pxr import Gf, UsdGeom
import omni.usd
import json
from datetime import datetime
import os

# Global cache to track last written state
previous_state = {}

class CadreAOmniTracker(BehaviorScript):
    def on_init(self):
        stage = omni.usd.get_context().get_stage()
        self.output_path = "/tmp/producerOmniUpdate.json"
        self._prim_path = "/World/Omni_Cadre/CADRE_Demo/Chassis"

        tracked_prim = stage.GetPrimAtPath(self._prim_path)
        if not tracked_prim.IsValid():
            print(f"[ERROR] Prim not found at path: {self._prim_path}")
            self.tracked_prim = None
            return

        self.tracked_prim = tracked_prim
        print(f"[INFO] Tracker initialized for prim: {self._prim_path}")

    def on_update(self, current_time: float, delta_time: float):
        if not self.tracked_prim:
            return

        try:
            matrix = omni.usd.get_world_transform_matrix(self.tracked_prim)
            translate = matrix.ExtractTranslation()
            rotation = matrix.ExtractRotation().GetQuaternion()

            position = [translate[0], translate[1], translate[2]]
            rotation_q = [rotation.GetReal()] + list(rotation.GetImaginary())

            current_data = {
                "position": position,
                "rotation": rotation_q,
                "modifiedDate": datetime.now().isoformat()
            }

            global previous_state
            if current_data != previous_state:
                with open(self.output_path, 'w') as f:
                    json.dump(current_data, f, indent=4)
                previous_state = current_data
                print(f"[INFO] Wrote new transform data to {self.output_path}")

        except Exception as e:
            print(f"[ERROR] Exception during update: {e}")
