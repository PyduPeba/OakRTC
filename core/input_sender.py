# core/input_sender.py
import win32api
import win32con
import time

# Mapeamento de direções com base em lParam e rParam
KEYBOARD_MAP = {
    'up': (0x26, 0x00480001),
    'down': (0x28, 0x00500001),
    'right': (0x27, 0x004D0001),
    'left': (0x25, 0x004B0001),
    'up_right': (0x21, 0x00490001),
    'up_left': (0x24, 0x00470001),
    'down_right': (0x22, 0x00510001),
    'down_left': (0x23, 0x004F0001),
}

def send_arrow_key(direction: str):
    import core.Addresses as Addresses
    game_hwnd = Addresses.game

    if not game_hwnd:
        print("[input_sender] ERRO: game HWND não definido.")
        return

    if direction not in KEYBOARD_MAP:
        print(f"[input_sender] Direção inválida: {direction}")
        return

    rParam, lParam = KEYBOARD_MAP[direction]
    print(f"[input_sender] ▶️ Enviando tecla '{direction.upper()}' via lParam/rParam")
    win32api.PostMessage(game_hwnd, win32con.WM_KEYDOWN, rParam, lParam)
    time.sleep(0.05)
    win32api.PostMessage(game_hwnd, win32con.WM_KEYUP, rParam, lParam)
