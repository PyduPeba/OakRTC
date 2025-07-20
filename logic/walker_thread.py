# logic/walker_thread.py

from PyQt6.QtCore import QThread, pyqtSignal
from core import Addresses
from core.memory_utils import read_my_wpt
from logic.keyboard_controller import walk, get_direction
from logic.mouse_controller import mouse_function
from core.Addresses import walker_Lock, coordinates_x, coordinates_y
import random
import win32api
import win32con
from PyQt6.QtWidgets import QListWidgetItem
from PyQt6.QtCore import Qt


class WalkerThread(QThread):
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    index_update = pyqtSignal(int, object)

    def __init__(self, waypoints, hud_log=None):
        super().__init__()
        self.waypoints = waypoints
        self.hud_log = hud_log
        self.running = True

    def run(self):
        from core.memory_reader import MemoryReader
        reader = MemoryReader()
        try:
            reader.load_client()
        except Exception as e:
            msg = f"[ERRO] Falha ao carregar cliente: {e}"
            if self.hud_log:
                self.hud_log.log(msg)
            print(msg)
            return

        current_wpt = 0
        timer, timer2 = 0, 0
        old_x, old_y = 0, 0

        self.status_signal.emit("Andando")
        while self.running:
            try:
                if timer2 >= 1:
                    current_wpt = self.find_wpt(current_wpt)
                    timer2 = 0

                self.index_update.emit(0, current_wpt)
                wpt = self.waypoints[current_wpt]
                x, y, z = read_my_wpt()
                while (x or y or z) is None:
                    x, y, z = read_my_wpt()

                if (x, y, z) == (wpt['X'], wpt['Y'], wpt['Z']) and wpt['Action'] == 0:
                    self.log_signal.emit(f"[Walker] ✅ Já está na posição {x, y, z}")
                    self.status_signal.emit("Parado")
                    timer = 0
                    current_wpt = (current_wpt + 1) % len(self.waypoints)
                    continue

                if not walker_Lock.locked() or wpt['Direction'] == 9:
                    if old_x == x and old_y == y:
                        timer2 += 0.2
                    else:
                        timer2 = 0
                    old_x, old_y = x, y

                    if wpt['Action'] == 0:
                        if wpt['Direction'] == 9:
                            direction = get_direction(x, y, wpt['X'], wpt['Y'])
                            self.status_signal.emit("Andando")
                            self.log_signal.emit(f"[Walker] 🚶 Caminhando (modo inteligente). Direção calculada: {direction}")
                            walk(direction)
                        else:
                            self.log_signal.emit(f"[Walker] 🚶 Caminhando... direção fixa: {wpt['Direction']}")
                        
                            walk(wpt['Direction'])

                    elif wpt['Action'] == 1:
                        self.log_signal.emit(f"[Walker] 🪜 Rope action")
                        
                        QThread.msleep(random.randint(500, 600))
                        mouse_function(coordinates_x[10], coordinates_y[10], option=1)
                        QThread.msleep(random.randint(100, 200))
                        x, y, z = read_my_wpt()
                        mouse_function(coordinates_x[0] + (wpt['X'] - x) * 75,
                                        coordinates_y[0] + (wpt['Y'] - y) * 75, option=2)
                        current_wpt = (current_wpt + 1) % len(self.waypoints)

                    elif wpt['Action'] == 2:
                        self.log_signal.emit(f"[Walker] ⛏️ Shovel action")
                        
                        QThread.msleep(random.randint(500, 600))
                        mouse_function(coordinates_x[9], coordinates_y[9], option=1)
                        QThread.msleep(random.randint(100, 200))
                        x, y, z = read_my_wpt()
                        mouse_function(coordinates_x[0] + (wpt['X'] - x) * 75,
                                        coordinates_y[0] + (wpt['Y'] - y) * 75, option=2)
                        current_wpt = (current_wpt + 1) % len(self.waypoints)

                    elif wpt['Action'] == 3:
                        self.log_signal.emit(f"[Walker] 🪜 Ladder action")
                        
                        QThread.msleep(random.randint(500, 600))
                        mouse_function(coordinates_x[0], coordinates_y[0], option=1)
                        current_wpt = (current_wpt + 1) % len(self.waypoints)

                    elif wpt['Action'] == 4:
                        self.log_signal.emit(f"[Walker] ⚙️ Custom Action")
                        self.status_signal.emit("Executando ação...")
                        
                        command = wpt['Direction'].split(' ')
                        handle_action(command)

                if timer > 5000:
                    self.log_signal.emit(f"[Walker] ❌ Perdeu o caminho. Tentando recuperar...")
                    
                    current_wpt = self.lost_wpt(current_wpt)
                    timer = 0

                sleep_value = random.randint(50, 100)
                QThread.msleep(sleep_value)
                if not walker_Lock.locked():
                    timer += sleep_value
            except Exception as e:
                self.log_signal.emit(f"[Walker] ❌ Erro na thread: {e}")
                

    def stop(self):
        self.log_signal.emit(f"[Walker] ⛔ Parando thread do walker...")
        self.status_signal.emit("Parado")
        self.running = False

    def find_wpt(self, index):
        current_wpt = index
        x, y, z = read_my_wpt()
        while (x or y or z) is None:
            x, y, z = read_my_wpt()
        for wpt in range(current_wpt, len(self.waypoints)):
            wpt_data = self.waypoints[wpt]
            if z == wpt_data['Z'] and abs(wpt_data['X'] - x) <= 7 and abs(wpt_data['Y'] - y) <= 5:
                return wpt
        return current_wpt

    def lost_wpt(self, index):
        x, y, z = read_my_wpt()
        while (x or y or z) is None:
            x, y, z = read_my_wpt()
        for wpt in range(len(self.waypoints)):
            wpt_data = self.waypoints[wpt]
            if z == wpt_data['Z'] and abs(wpt_data['X'] - x) <= 7 and abs(wpt_data['Y'] - y) <= 5:
                return wpt
        return 0

def handle_action(command) -> None:
    for i in range(0, len(command)):
        if command[i] == 'say':
            if command[i + 1][-1] != '\'':
                text = command[i + 1].replace("'", '')
                for j in range(i + 2, len(command)):
                    text += ' ' + command[j]
                    if text[-1] == '\'':
                        break
                text = text.replace("'", '')
            else:
                text = command[i + 1].replace("'", '')

            for char in text:
                win32api.PostMessage(Addresses.game, win32con.WM_CHAR, ord(char), 0)
            scan_code = win32api.MapVirtualKey(win32con.VK_RETURN, 0)
            lParam_keydown = 1 | (scan_code << 16)
            lParam_keyup = 1 | (scan_code << 16) | (1 << 30) | (1 << 31)
            win32api.PostMessage(Addresses.game, win32con.WM_KEYDOWN, win32con.VK_RETURN, lParam_keydown)
            win32api.PostMessage(Addresses.game, win32con.WM_KEYUP, win32con.VK_RETURN, lParam_keyup)

        if command[i] == 'wait':
            QThread.msleep(int(command[i + 1]))


