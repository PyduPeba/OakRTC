# components/hud_log_widget.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit
from PyQt6.QtGui import QTextCursor

class HUDLogWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Walker Debug HUD")
        self.setFixedWidth(300)
        layout = QVBoxLayout(self)
        self.label_coords = QLabel("Posição atual: -")
        self.label_target = QLabel("Próximo destino: -")
        self.label_status = QLabel("Status: Parado")
        self.label_distance = QLabel("Distância: -")
        self.label_action = QLabel("Ação: -")
        self.text_log = QTextEdit()
        self.text_log.setReadOnly(True)
        layout.addWidget(self.label_coords)
        layout.addWidget(self.label_target)
        layout.addWidget(self.label_status)
        layout.addWidget(self.label_distance)
        layout.addWidget(self.label_action)
        layout.addWidget(self.text_log)
        self.max_log_lines = 100
    
    def append(self, text):
        self.text_log.append(text)

    def clear(self):
        self.text_log.clear()

    def update_status(self, curr, target, status, distance, action):
        self.label_coords.setText(f"Posição atual: {curr}")
        self.label_target.setText(f"Próximo: {target}")
        self.label_status.setText(f"Status: {status}")
        self.label_distance.setText(f"Distância: {distance}")
        self.label_action.setText(f"Ação: {action}")

    def log(self, msg):
        # Limite de 100 linhas
        lines = self.text_log.toPlainText().split('\n')
        if len(lines) >= 100:
            lines = lines[-99:]  # mantém as últimas 99
        lines.append(msg)
        self.text_log.setPlainText('\n'.join(lines))
        self.text_log.moveCursor(QTextCursor.MoveOperation.End)

    def set_position(self, x, y, z):
        self.label_coords.setText(f"Posição atual: {x}, {y}, {z}")

    def set_target(self, x, y, z):
        self.label_target.setText(f"Próximo destino: {x}, {y}, {z}")

    def set_status(self, status):
        self.label_status.setText(f"Status: {status}")

    def set_distance(self, dist):
        self.label_distance.setText(f"Distância: {dist}")

    def set_action(self, action):
        self.label_action.setText(f"Ação: {action}")