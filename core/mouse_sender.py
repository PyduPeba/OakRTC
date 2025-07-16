# core/mouse_sender.py

import win32gui
import win32api
import win32con
import time
import ctypes
from core.Addresses import game, debug_mode

def send_click_relative(offset_x, offset_y):
    if game is None:
        print("[mouse_sender] ⚠️ Janela do jogo não carregada (game is None).")
        return

    rect = win32gui.GetWindowRect(game)
    center_x = (rect[0] + rect[2]) // 2
    center_y = (rect[1] + rect[3]) // 2

    click_x = center_x + offset_x
    click_y = center_y + offset_y

    # Converte coordenadas de tela para coordenadas de cliente
    client_point = win32gui.ScreenToClient(game, (click_x, click_y))
    cx, cy = client_point

    # Envia evento de clique apenas para a janela do jogo
    lParam = win32api.MAKELONG(cx, cy)
    win32api.PostMessage(game, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
    time.sleep(0.02)
    win32api.PostMessage(game, win32con.WM_LBUTTONUP, None, lParam)

    # Mostra visual do clique se estiver em modo debug
    if debug_mode:
        _draw_click_overlay(click_x, click_y)

def _draw_click_overlay(x, y):
    # Desenha um pequeno círculo vermelho por 0.1s no ponto clicado (overlay temporário)
    hwnd = win32gui.GetDesktopWindow()
    hdc = win32gui.GetWindowDC(hwnd)

    red_pen = win32gui.CreatePen(win32con.PS_SOLID, 2, win32api.RGB(255, 0, 0))
    prev_pen = win32gui.SelectObject(hdc, red_pen)

    radius = 6
    win32gui.Ellipse(hdc, x - radius, y - radius, x + radius, y + radius)

    win32gui.SelectObject(hdc, prev_pen)
    win32gui.DeleteObject(red_pen)
    win32gui.ReleaseDC(hwnd, hdc)

    time.sleep(0.1)

    # Opcional: pode limpar o círculo se quiser redesenhar a tela, mas geralmente não necessário
