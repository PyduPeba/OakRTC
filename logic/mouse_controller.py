import win32gui
import win32con
import win32api
import time
from core.memory_reader import fin_window_name

def send_mouse_click(hwnd, x, y, button='left'):
    lParam = win32api.MAKELONG(x, y)
    if button == 'left':
        win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
        time.sleep(0.05)
        win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)
    elif button == 'right':
        win32api.PostMessage(hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, lParam)
        time.sleep(0.05)
        win32api.PostMessage(hwnd, win32con.WM_RBUTTONUP, 0, lParam)

def mouse_function(x, y, option=1):
    window_name = fin_window_name("RubinOT")  # Busca título exato da janela
    hwnd = win32gui.FindWindow(None, window_name)
    if hwnd == 0:
        print(f"[Walker] ❌ Janela '{window_name}' não encontrada!")
        return

    print(f"[Walker] 🖱️ Enviando clique para ({x}, {y}) na janela '{window_name}'")
    send_mouse_click(hwnd, x, y, button='left' if option == 1 else 'right')
