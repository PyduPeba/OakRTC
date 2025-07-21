# logic/walker_thread.py

from PyQt6.QtCore import QThread, pyqtSignal
from core import Addresses
from core.memory_utils import read_my_wpt
from core.input_sender import hold_arrow_key, release_arrow_key
from logic.keyboard_controller import get_direction, DIRECTION_MAP
from logic.mouse_controller import mouse_function
from core.Addresses import walker_Lock, coordinates_x, coordinates_y
import random
import win32api
import win32con
import win32gui
import time
from PyQt6.QtWidgets import QListWidgetItem
from PyQt6.QtCore import Qt


class WalkerThread(QThread):
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    index_update = pyqtSignal(int, object)

    def __init__(self, waypoints, hud_log=None, character_center=(0,0)):
        super().__init__()
        self.waypoints = waypoints
        self.hud_log = hud_log
        self.running = True
        self.character_center = character_center

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
                if current_wpt > 0:
                    prev = self.waypoints[current_wpt - 1]
                    if (prev['X'], prev['Y'], prev['Z']) == (wpt['X'], wpt['Y'], wpt['Z']):
                        self.log_signal.emit("[Walker] ⚠️ Waypoint repetido, pulando.")
                        current_wpt = (current_wpt + 1) % len(self.waypoints)
                        continue
                x, y, z = read_my_wpt()
                while (x or y or z) is None:
                    x, y, z = read_my_wpt()

                # if (x, y, z) == (wpt['X'], wpt['Y'], wpt['Z']) and wpt['Action'] == 0:
                if self.reached_wpt(x, y, z, wpt):
                    self.log_signal.emit(f"[Walker] ✅ Já está na posição {x, y, z}")
                    self.status_signal.emit("Parado")
                    
                    current_wpt = (current_wpt + 1) % len(self.waypoints)
                    timer = 0
                    continue

                if not walker_Lock.locked() or wpt['Direction'] == 9:
                    if old_x == x and old_y == y:
                        timer2 += 0.2
                    else:
                        timer2 = 0
                    old_x, old_y = x, y

                    if wpt['Action'] == 0:
                        moved = self.smart_walk(reader, wpt)
                        if not moved:
                            # Aqui pode chamar lógica de pathfinding custom ou alertar no HUD
                            self.log_signal.emit("[Walker] Fallback não conseguiu resolver, precisa de atenção manual ou implementar pathfinding real.")
                        # if wpt['Direction'] == 9:
                        #     direction = get_direction(x, y, wpt['X'], wpt['Y'])
                        #     self.status_signal.emit("Andando")
                        #     self.log_signal.emit(f"[Walker] 🚶 Caminhando (modo inteligente). Direção calculada: {direction}")
                        #     walk(direction)
                        # else:
                        #     self.log_signal.emit(f"[Walker] 🚶 Caminhando... direção fixa: {wpt['Direction']}")
                        
                        #     walk(wpt['Direction'])

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
    
    def get_window_position(self, window_name="RubinOT"):
        hwnd = win32gui.FindWindow(None, window_name)
        if hwnd == 0:
            return (0, 0)
        rect = win32gui.GetWindowRect(hwnd)
        return rect[0], rect[1]  # posição x, y da janela no monitor
    
    def smart_walk(self, reader, wpt):
        current_x, current_y, current_z = reader.get_position()
        char_center = self.character_center

        # Clique com mouse
        screen_x, screen_y = self.calculate_screen_position((current_x, current_y), (wpt['X'], wpt['Y']), char_center)
        mouse_function(int(screen_x), int(screen_y))
        self.log_signal.emit(f"[Walker] 🖱️ Clique ajustado: [{screen_x}, {screen_y}]")

        initial_pos = (current_x, current_y)
        start_time = time.time()
        while time.time() - start_time < 0.5:
            new_x, new_y, _ = reader.get_position()
            if (new_x, new_y) != initial_pos:
                self.log_signal.emit("[Walker] ✅ Moveu com mouse.")
                return True
            QThread.msleep(50)

        # Movimento contínuo via teclado
        direction_index = get_direction(current_x, current_y, wpt['X'], wpt['Y'])
        if direction_index is None:
            return False

        direction = DIRECTION_MAP.get(direction_index)
        if direction:
            self.log_signal.emit(f"[Walker] ⌨️ Movimento contínuo para {direction}")
            hold_arrow_key(direction)

            start = time.time()
            while time.time() - start < 2.0:  # segura por até 2s
                new_x, new_y, _ = reader.get_position()
                if (new_x, new_y) == (wpt['X'], wpt['Y']):
                    release_arrow_key(direction)
                    self.log_signal.emit("[Walker] ✅ Chegou ao destino com tecla segurada.")
                    return True
                QThread.msleep(50)

            release_arrow_key(direction)
            self.log_signal.emit("[Walker] ⚠️ Timeout com tecla segurada.")

        return self.intelligent_fallback(reader, (current_x, current_y), wpt)
    
    def intelligent_fallback(self, reader, initial_pos, wpt):
        directions_attempted = set()
        max_attempts = 10
        timeout = 0.3

        for _ in range(max_attempts):
            curr_x, curr_y, _ = reader.get_position()

            # Sempre tenta a direção correta primeiro
            direction_index = get_direction(curr_x, curr_y, wpt['X'], wpt['Y'])

            if direction_index in directions_attempted or direction_index is None:
                # Seleciona direção ainda não testada aleatoriamente
                remaining = [i for i in range(1, 10) if i not in directions_attempted]
                if not remaining:
                    break
                direction_index = random.choice(remaining)

            directions_attempted.add(direction_index)

            direction_str = DIRECTION_MAP.get(direction_index)
            if direction_str is None:
                continue

            self.log_signal.emit(f"[Walker] 🔄 Fallback tentando direção {direction_str.upper()}")
            hold_arrow_key(direction_str)
            QThread.msleep(int(timeout * 1000))
            release_arrow_key(direction_str)

            new_x, new_y, _ = reader.get_position()
            if (new_x, new_y) != (curr_x, curr_y):
                self.log_signal.emit("[Walker] ✅ Fallback avançado funcionou.")
                # Evita recursão em smart_walk
                return True

        self.log_signal.emit("[Walker] ❌ Fallback avançado falhou.")
        return False
    
    def calculate_screen_position(self, current_pos, target_pos, char_center):
        tile_size = 32  # ajuste conforme o seu cliente (geralmente entre 32 e 64 pixels por tile)
        dx = target_pos[0] - current_pos[0]
        dy = target_pos[1] - current_pos[1]

        # Calcula a posição exata na tela para clicar com base na posição atual e no destino
        screen_x = char_center[0] + (dx * tile_size)
        screen_y = char_center[1] + (dy * tile_size)

        return screen_x, screen_y
    
    def reached_wpt(self, current_x, current_y, current_z, wpt):
        return (
            abs(current_x - wpt['X']) <= 1 and
            abs(current_y - wpt['Y']) <= 1 and
            current_z == wpt['Z']
        )

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


