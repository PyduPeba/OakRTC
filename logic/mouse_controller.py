import win32api
import win32con
import time

def mouse_click(x, y, button='left'):
    win32api.SetCursorPos((x, y))
    if button == 'left':
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.05)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    elif button == 'right':
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        time.sleep(0.05)
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)

def mouse_function(x, y, option=1):
    print(f"[Walker] 🖱️ Movendo com mouse para ({x}, {y})")
    mouse_click(x, y, button='left' if option == 1 else 'right')
