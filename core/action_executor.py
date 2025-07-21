import time
import re
from PyQt6.QtCore import QThread
from core.action_context import context_vars, update_context
from logic.keyboard_controller import send_text

def send_char(c):
    import win32api, win32con
    from core.Addresses import game
    win32api.PostMessage(game, win32con.WM_CHAR, ord(c), 0)  # -1 será o HWND correto

def press_enter():
    import win32api, win32con
    from core.Addresses import game
    scan_code = win32api.MapVirtualKey(win32con.VK_RETURN, 0)
    lParam_keydown = 1 | (scan_code << 16)
    lParam_keyup = 1 | (scan_code << 16) | (1 << 30) | (1 << 31)
    win32api.PostMessage(game, win32con.WM_KEYDOWN, win32con.VK_RETURN, lParam_keydown)
    win32api.PostMessage(game, win32con.WM_KEYUP, win32con.VK_RETURN, lParam_keyup)

def evaluate_condition(line: str) -> bool:
    match = re.match(r"if\s+(.+?)\s+then", line)
    if not match:
        return False
    expr = match.group(1)

    for var, val in context_vars.items():
        expr = expr.replace(var, str(val))

    try:
        return eval(expr)
    except Exception as e:
        print(f"[Condicional] Erro ao avaliar: {e}")
        return False

def handle_action(commands: list[str], reader=None):
    if reader:
        update_context(reader)

    if isinstance(commands, str):
        commands = commands.splitlines()

    skip = False
    i = 0
    while i < len(commands):
        cmd = commands[i].strip()

        if cmd.startswith("if"):
            skip = not evaluate_condition(cmd)
            i += 1
            continue
        if cmd == "end":
            skip = False
            i += 1
            continue
        if skip:
            i += 1
            continue

        if cmd.startswith("say("):
            text = re.findall(r"say\(['\"](.+?)['\"]\)", cmd)
            if text:
                send_text(text[0])
                QThread.msleep(100)

        elif cmd.startswith("wait("):
            delay = re.findall(r"wait\((\d+)\)", cmd)
            if delay:
                QThread.msleep(int(delay[0]))

        elif cmd.startswith("hotkey("):
            key = re.findall(r"hotkey\(['\"](.+?)['\"]\)", cmd)
            if key:
                send_text(key[0])

        elif " " in cmd and cmd.startswith("say"):
            # estilo Windbot: say 'hi there'
            parts = cmd.split()
            if len(parts) >= 2:
                text = " ".join(parts[1:]).replace("'", "")
                for c in text:
                    send_char(c)
                press_enter()

        elif cmd.startswith("wait"):
            parts = cmd.split()
            if len(parts) == 2 and parts[1].isdigit():
                QThread.msleep(int(parts[1]))

        else:
            print(f"[Ação] ⚠️ Comando desconhecido: {cmd}")

        i += 1