# logic/keyboard_controller.py
import win32api
import win32con
from core.input_sender import send_arrow_key
from core.Addresses import game  # janela do cliente RubinOT
import time

# Mapeamento completo e correto
DIRECTION_MAP = {
    1: 'down_left',
    2: 'down',
    3: 'down_right',
    4: 'left',
    5: None,  # centro
    6: 'right',
    7: 'up_left',
    8: 'up',
    9: 'up_right'
}

KEY_MAP = {
    'up': win32con.VK_UP,
    'down': win32con.VK_DOWN,
    'left': win32con.VK_LEFT,
    'right': win32con.VK_RIGHT
}

DIAGONALS = {
    'up_left': ('up', 'left'),
    'up_right': ('up', 'right'),
    'down_left': ('down', 'left'),
    'down_right': ('down', 'right')
}

def walk(direction_index, *args):
    direction = DIRECTION_MAP.get(direction_index)
    if direction:
        send_arrow_key(direction)
    else:
        print(f"[keyboard_controller] Direção inválida: {direction_index}")

def hold_key(direction):
    keys = DIAGONALS.get(direction, (direction,))
    for key in keys:
        key_code = KEY_MAP.get(key)
        if key_code:
            lParam = (0x00000001 | (win32api.MapVirtualKey(key_code, 0) << 16))
            win32api.PostMessage(game, win32con.WM_KEYDOWN, key_code, lParam)

def release_all_keys():
    for key in KEY_MAP.values():
        lParam = (0xC0000001 | (win32api.MapVirtualKey(key, 0) << 16))
        win32api.PostMessage(game, win32con.WM_KEYUP, key, lParam)

def get_direction(curr_x, curr_y, target_x, target_y):
    dx = target_x - curr_x
    dy = target_y - curr_y

    if dx == 0 and dy == 0:
        return None  # já está no lugar

    if dx == 0:
        return 8 if dy < 0 else 2
    elif dy == 0:
        return 4 if dx < 0 else 6
    elif dx < 0 and dy < 0:
        return 7  # up-left
    elif dx > 0 and dy < 0:
        return 9  # up-right
    elif dx < 0 and dy > 0:
        return 1  # down-left
    elif dx > 0 and dy > 0:
        return 3  # down-right

    return None

# def send_text(text: str):
#     for char in text:
#         win32api.PostMessage(game, win32con.WM_CHAR, ord(char), 0)
#     scan_code = win32api.MapVirtualKey(win32con.VK_RETURN, 0)
#     lParam_down = 1 | (scan_code << 16)
#     lParam_up = lParam_down | (1 << 30) | (1 << 31)
#     win32api.PostMessage(game, win32con.WM_KEYDOWN, win32con.VK_RETURN, lParam_down)
#     win32api.PostMessage(game, win32con.WM_KEYUP, win32con.VK_RETURN, lParam_up)
#     time.sleep(0.1)

# def press_enter(hwnd):
#     scan_code = win32api.MapVirtualKey(win32con.VK_RETURN, 0)
#     lParam_down = 1 | (scan_code << 16)
#     lParam_up = 1 | (scan_code << 16) | (1 << 30) | (1 << 31)
#     win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, lParam_down)
#     win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, lParam_up)

def send_text(text: str):
    import win32api
    import win32con
    from core.Addresses import game
    import time

    def press_enter():
        scan_code = win32api.MapVirtualKey(win32con.VK_RETURN, 0)
        lParam_down = 1 | (scan_code << 16)
        lParam_up = lParam_down | (1 << 30) | (1 << 31)
        win32api.PostMessage(game, win32con.WM_KEYDOWN, win32con.VK_RETURN, lParam_down)
        win32api.PostMessage(game, win32con.WM_KEYUP, win32con.VK_RETURN, lParam_up)
        time.sleep(0.1)

    # Abrir o chat
    press_enter()
    time.sleep(0.05)

    # Digitar caractere por caractere
    for char in text:
        win32api.PostMessage(game, win32con.WM_CHAR, ord(char), 0)
        time.sleep(0.02)  # delay entre caracteres

    time.sleep(0.05)

    # Enviar mensagem
    press_enter()
    time.sleep(0.1)


__all__ = ['walk', 'hold_key', 'release_all_keys', 'get_direction', 'send_text']
