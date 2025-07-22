import time
import win32gui
import win32con
import win32api

def find_client_window(title_prefix='RubinOT Client'):
    def enum_handler(hwnd, result):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title.startswith(title_prefix):
                result.append(hwnd)

    results = []
    win32gui.EnumWindows(enum_handler, results)
    return results[0] if results else None

def get_client_rect():
    hwnd = find_client_window()
    if not hwnd:
        raise Exception("Janela do cliente não encontrada.")
    return win32gui.GetWindowRect(hwnd), hwnd

def click(hwnd, x, y):
    lParam = win32api.MAKELONG(x, y)
    win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
    time.sleep(0.05)
    win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, None, lParam)

def send_text(hwnd, text):
    for char in text:
        win32api.PostMessage(hwnd, win32con.WM_CHAR, ord(char), 0)
        time.sleep(0.01)

def buy_item_from_npc(item_name="mana potion", amount=100):
    rect, hwnd = get_client_rect()

    # Valores de exemplo, ajustar conforme teste real
    search_x, search_y = 150, 160  # campo "Type to search"
    item_x, item_y = 150, 200      # item na lista
    amount_x, amount_y = 90, 300   # campo Amount
    ok_x, ok_y = 210, 360          # botão Buy

    # Etapa 1: clicar no campo de busca
    click(hwnd, search_x, search_y)
    time.sleep(0.1)
    send_text(hwnd, item_name)
    time.sleep(0.5)

    # Etapa 2: clicar no item
    click(hwnd, item_x, item_y)
    time.sleep(0.1)

    # Etapa 3: digitar quantidade
    click(hwnd, amount_x, amount_y)
    time.sleep(0.1)
    send_text(hwnd, str(amount))
    time.sleep(0.1)

    # Etapa 4: clicar no botão Buy
    click(hwnd, ok_x, ok_y)
    time.sleep(0.2)

    print(f"[NPC] 🛒 Tentando comprar {amount}x {item_name}")
