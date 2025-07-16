import json
import os

class WaypointManager:
    def __init__(self, path_dir="paths"):
        self.path_dir = path_dir
        os.makedirs(self.path_dir, exist_ok=True)

    def save_path(self, path, filename="recorded_path.json"):
        full_path = os.path.join(self.path_dir, filename)
        with open(full_path, "w") as f:
            json.dump(path, f, indent=4)

    def load_path(self, filename="recorded_path.json"):
        full_path = os.path.join(self.path_dir, filename)
        with open(full_path, "r") as f:
            return json.load(f)
