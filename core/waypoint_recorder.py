# core/waypoint_recorder.py
import json
import os

class WaypointRecorder:
    def __init__(self):
        self.path = []
        self.recording = False

    def start(self):
        self.path = []
        self.recording = True

    def stop(self):
        self.recording = False

    def record_position(self, x, y, z):
        if self.recording:
            self.path.append({"x": x, "y": y, "z": z})

    def get_path(self):
        return self.path

    def save_to_file(self, filename="paths/recorded_path.json"):
        import json, os
        os.makedirs("paths", exist_ok=True)
        with open(filename, "w") as f:
            json.dump(self.path, f, indent=4)
