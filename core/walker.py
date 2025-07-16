import time
import math
import random
import win32gui
import win32con
import core.Addresses as Addresses
from core.memory_utils import read_my_wpt
from Functions.MouseFunctions import mouse_function

keyboard_directions = {
    (0, -1): (Addresses.rParam[0], Addresses.lParam[0]),
    (0, 1):  (Addresses.rParam[1], Addresses.lParam[1]),
    (1, 0):  (Addresses.rParam[2], Addresses.lParam[2]),
    (-1, 0): (Addresses.rParam[3], Addresses.lParam[3])
}

def has_arrived(x1, y1, z1, x2, y2, z2, tolerance=1):
    return abs(x1 - x2) <= tolerance and abs(y1 - y2) <= tolerance and z1 == z2

def get_distance(from_x, from_y, to_x, to_y):
    dx = abs(from_x - to_x)
    dy = abs(from_y - to_y)
    manhattan = dx + dy
    euclidean = math.sqrt(dx**2 + dy**2)
    return manhattan, euclidean

def delay_by_distance(distance):
    # Base de 0.3s até no máximo 0.8s para distâncias maiores
    return min(0.3 + (distance * 0.1), 0.8)

def walk_to(target_x, target_y, target_z, show_status=None):
    # Garantir que a base foi carregada
    if Addresses.base_address is None:
        try:
            print("[Walker] 🔄 Tentando carregar cliente automaticamente.")
            from core.memory_reader import MemoryReader
            reader = MemoryReader()
            reader.load_client()
        except Exception as e:
            print(f"[Walker] ❌ Falha ao carregar cliente: {e}")
            if show_status:
                show_status("❌ Cliente não carregado.")
            return

    my_x, my_y, my_z = read_my_wpt()
    if None in (my_x, my_y, my_z):
        print("[Walker] ❌ Posição atual inválida.")
        if show_status:
            show_status("❌ Falha ao obter posição atual.")
        return

    if has_arrived(my_x, my_y, my_z, target_x, target_y, target_z):
        print(f"[Walker] ✅ Já está na posição ({target_x}, {target_y}, {target_z})")
        if show_status:
            show_status(f"✅ Chegou em x:{target_x}, y:{target_y}, z:{target_z}")
        return

    dx = target_x - my_x
    dy = target_y - my_y
    dz = target_z - my_z

    dist_sqm, dist_euc = get_distance(my_x, my_y, target_x, target_y)
    debug_text = f"[Walker] ▶️ Indo de ({my_x}, {my_y}, {my_z}) → ({target_x}, {target_y}, {target_z}) | Distância: {dist_sqm} sqm / {dist_euc:.2f}"
    print(debug_text)
    if show_status:
        show_status(debug_text)

    # 🖱️ Mouse se dentro da tela
    if abs(dx) <= 7 and abs(dy) <= 5 and dz == 0:
        screen_x = Addresses.coordinates_x[0] + dx * 75
        screen_y = Addresses.coordinates_y[0] + dy * 75
        print(f"[Walker] 🖱️ Clicando em ({screen_x}, {screen_y})")
        mouse_function(screen_x, screen_y, option=2)
        time.sleep(delay_by_distance(dist_sqm))
        return

    # ⌨️ Teclado se não for possível clicar
    step = (int(math.copysign(1, dx)) if dx != 0 else 0, int(math.copysign(1, dy)) if dy != 0 else 0)
    if step in keyboard_directions:
        r_param, l_param = keyboard_directions[step]
        print(f"[Walker] ⌨️ Andando com teclado: direção {step}")
        win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, r_param, l_param)
        win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, r_param, l_param)
        time.sleep(delay_by_distance(dist_sqm))
    else:
        print("[Walker] ⚠️ Direção inválida ou fora do alcance.")
        if show_status:
            show_status("⚠️ Direção inválida ou fora do alcance.")
