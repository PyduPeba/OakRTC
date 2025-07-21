# core/waypoint_recorder.py
import json
import os

class WaypointRecorder:
    def __init__(self):
        self.path = []
        self.recording = False
        self.last_position = None

    def start(self):
        self.path = []
        self.recording = True

    def stop(self):
        self.recording = False

    def record_position(self, x, y, z):
        if not self.recording:
            return

        if self.last_position:
            lx, ly, lz = self.last_position
            if (x, y, z) == (lx, ly, lz):
                return  # ignorar mesma posição
            if abs(x - lx) + abs(y - ly) < 2:
                return  # muito perto, ignora
        self.last_position = (x, y, z)
        self.path.append({"x": x, "y": y, "z": z})

    def get_path(self):
        return self.path
    
    def simplify_path(self):
        if len(self.path) < 3:
            return self.path

        simplified = [self.path[0]]
        for i in range(1, len(self.path) - 1):
            prev = self.path[i - 1]
            curr = self.path[i]
            next_ = self.path[i + 1]

            dx1 = curr["x"] - prev["x"]
            dy1 = curr["y"] - prev["y"]
            dx2 = next_["x"] - curr["x"]
            dy2 = next_["y"] - curr["y"]

            if dx1 == dx2 and dy1 == dy2:
                continue  # ponto intermediário linear, ignorar
            simplified.append(curr)
        simplified.append(self.path[-1])
        return simplified


    # def save_to_file(self, filename="paths/recorded_path.json"):
    #     import json, os
    #     os.makedirs("paths", exist_ok=True)
    #     with open(filename, "w") as f:
    #         json.dump(self.path, f, indent=4)

    def save_to_file(self, file_path=None):
        simplified = self.simplify_path()

        if not file_path:
            os.makedirs("paths", exist_ok=True)
            file_path = "paths/recorded_path.json"

        data = []
        for index, point in enumerate(simplified):
            data.append({
                "WP": index + 1,
                "Type": "Walk",
                "Label": "",
                "X": point["x"],
                "Y": point["y"],
                "Z": point["z"],
                "RangeX": 0,
                "RangeY": 0,
                "Action": 0,
                "Direction": 0
            })

        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
