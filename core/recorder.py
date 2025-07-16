import json
import time

class AutoRecorder:
    def __init__(self, memory_reader, save_path='data/paths.json'):
        self.reader = memory_reader
        self.save_path = save_path
        self.recording = []

    def record_step(self):
        pos = self.reader.get_position()
        print(f"Gravando passo: {pos}")
        self.recording.append({"x": pos[0], "y": pos[1], "z": pos[2]})

    def save(self):
        with open(self.save_path, 'w') as f:
            json.dump(self.recording, f, indent=2)
