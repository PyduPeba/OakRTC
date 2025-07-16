import pyautogui
import time
import random

class InputController:
    def __init__(self):
        pass

    def walk(self, direction):
        key_map = {
            "north": "w",
            "south": "s",
            "east": "d",
            "west": "a"
        }

        if direction in key_map:
            key = key_map[direction]
            pyautogui.keyDown(key)
            time.sleep(random.uniform(0.05, 0.15))  # Pequena variação de tempo para humanizar
            pyautogui.keyUp(key)
