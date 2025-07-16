# logic/keyboard_controller.py
from core.input_sender import send_arrow_key

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

def walk(direction_index, *args):
    direction = DIRECTION_MAP.get(direction_index)
    if direction:
        send_arrow_key(direction)
    else:
        print(f"[keyboard_controller] Direção inválida: {direction_index}")

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

