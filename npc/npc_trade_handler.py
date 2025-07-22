# npc/npc_trade_handler.py

import win32gui
import win32con
import win32api
import time
import pyautogui

# Função base para detectar a janela do cliente

def get_client_rect(window_name='RubinOT Client - Vayler'):
    hwnd = win32gui.FindWindow(None, window_name)
    if hwnd:
        rect = win32gui.GetWindowRect(hwnd)
        return hwnd, rect
    return None, None

# Simula click relativo ao client

def click_relative(hwnd, offset_x, offset_y):
    left, top, _, _ = win32gui.GetWindowRect(hwnd)
    abs_x = left + offset_x
    abs_y = top + offset_y
    pyautogui.click(abs_x, abs_y)

# Digita texto com ENTER no final

def send_text_hwnd(hwnd, text):
    for c in text:
        win32api.PostMessage(hwnd, win32con.WM_CHAR, ord(c), 0)
        time.sleep(0.01)
    # ENTER
    scan = win32api.MapVirtualKey(win32con.VK_RETURN, 0)
    lParam_down = 1 | (scan << 16)
    lParam_up = 1 | (scan << 16) | (1 << 30) | (1 << 31)
    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, lParam_down)
    win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, lParam_up)

# Processo de compra no NPC Trade

def buy_item_from_npc(item_name, quantity):
    hwnd, rect = get_client_rect()
    if not hwnd:
        print("[NPC] Cliente não encontrado.")
        return

    print("[NPC] Interagindo com janela...")

    # Exemplo: clicar em "Type to search"
    click_relative(hwnd, 230, 100)
    time.sleep(0.2)
    send_text_hwnd(hwnd, item_name)

    time.sleep(0.5)
    # Exemplo: clicar no item listado (precisa ajustar para seu client)
    click_relative(hwnd, 230, 140)

    time.sleep(0.2)
    # Clicar no campo "Amount"
    click_relative(hwnd, 100, 260)
    time.sleep(0.2)
    send_text_hwnd(hwnd, str(quantity))

    time.sleep(0.2)
    # Clicar no botão "Buy"
    click_relative(hwnd, 220, 260)
    print(f"[NPC] Tentando comprar {quantity}x {item_name}")
