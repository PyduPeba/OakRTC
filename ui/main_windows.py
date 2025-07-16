# ui/main_windows.py
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QHBoxLayout, QSpinBox, QLabel, QGroupBox
)
from PyQt6.QtCore import QTimer
import sys, json, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.memory_reader import MemoryReader
from core.memory_utils import read_my_wpt
from logic.waypoint_manager import WaypointManager
from core.waypoint_recorder import WaypointRecorder
from core.walker import walk_to
from logic.walker_thread import WalkerThread



class CavebotHUD(QMainWindow):
    def __init__(self):
        super().__init__()
        self.reader = MemoryReader()
        self.reader.load_client()
        self.waypoint_manager = WaypointManager()
        self.walker_thread = None
        self.recorder = WaypointRecorder()

        self.setWindowTitle("Cavebot HUD - RubinOT")
        self.setGeometry(100, 100, 1000, 600)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tabs.addTab(self.create_cavebot_tab(), "Cavebot")
        self.tabs.addTab(QWidget(), "Targeting")
        self.tabs.addTab(QWidget(), "Looting")
        self.tabs.addTab(QWidget(), "Healing")
        self.tabs.addTab(QWidget(), "Support")
        self.tabs.addTab(self.create_autorecorder_tab(), "AutoRecorder")

    def try_connect(self):
        try:
            self.reader.load_client()
            self.connection_status.setText("🟢 Cliente conectado com sucesso.")
        except Exception as e:
            self.connection_status.setText(f"🔴 Erro ao conectar: {e}")

    def create_cavebot_tab(self):
        tab = QWidget()
        layout = QHBoxLayout()

        self.wp_table = QTableWidget()
        self.wp_table.setColumnCount(6)
        self.wp_table.setHorizontalHeaderLabels(["WP", "Type", "Label", "Coordinates", "Range", "Action"])
        self.wp_table.setRowCount(0)

        connection_panel = QVBoxLayout()
        self.connection_status = QLabel("🔴 Cliente não conectado.")
        self.connect_button = QPushButton("Conectar")
        self.connect_button.clicked.connect(self.try_connect)

        connection_panel.addWidget(self.connection_status)
        connection_panel.addWidget(self.connect_button)
        layout.addLayout(connection_panel)

        layout.addWidget(self.wp_table)

        side_panel = QVBoxLayout()

        range_group = QGroupBox("Range:")
        range_layout = QHBoxLayout()
        self.range_x = QSpinBox(); self.range_x.setValue(2)
        self.range_y = QSpinBox(); self.range_y.setValue(2)
        range_layout.addWidget(QLabel("X:"))
        range_layout.addWidget(self.range_x)
        range_layout.addWidget(QLabel("Y:"))
        range_layout.addWidget(self.range_y)
        range_group.setLayout(range_layout)
        side_panel.addWidget(range_group)

        buttons = ["Walk", "Stand", "Door", "Ladder", "Use", "Rope"]
        for btn in buttons:
            b = QPushButton(btn)
            b.clicked.connect(lambda _, x=btn: self.add_waypoint(x))
            side_panel.addWidget(b)

        load_button = QPushButton("Load Caminho JSON")
        load_button.clicked.connect(self.load_path_to_table)
        side_panel.addWidget(load_button)

        start_walker_button = QPushButton("▶️ Start Walker")
        stop_walker_button = QPushButton("⏹️ Stop Walker")
        start_walker_button.clicked.connect(self.start_walker)
        stop_walker_button.clicked.connect(self.stop_walker)
        side_panel.addWidget(start_walker_button)
        side_panel.addWidget(stop_walker_button)

        layout.addLayout(side_panel)
        tab.setLayout(layout)
        return tab
    
    def start_walker(self):
        try:
            # Garante que o processo está carregado antes de iniciar o Walker
            self.reader.load_client()
        except Exception as e:
            self.connection_status.setText(f"❌ Falha ao conectar antes do walker: {e}")
            return

        # Gerar path antes de iniciar o walker
        self.path = []
        row_count = self.wp_table.rowCount()
        for i in range(row_count):
            item = self.wp_table.item(i, 3)
            if item:
                coords = item.text().replace("x:", "").replace("y:", "").replace("z:", "").replace(" ", "")
                x, y, z = map(int, coords.split(","))
                self.path.append({
                    "X": x,
                    "Y": y,
                    "Z": z,
                    "Action": 0,
                    "Direction": 9  # ou 0 se preferir sempre andar
                })

        if self.walker_thread and self.walker_thread.isRunning():
            self.connection_status.setText("🚫 Walker já está rodando.")
            return

        self.walker_thread = WalkerThread(self.path)
        self.walker_thread.start()
        self.connection_status.setText("🚶 Walker iniciado.")

    def stop_walker(self):
        if self.walker_thread and self.walker_thread.isRunning():
            self.walker_thread.stop()  # Método customizado na thread
            self.walker_thread.wait()  # Aguarda o término seguro
            self.connection_status.setText("⛔ Walker parado.")
        else:
            self.connection_status.setText("ℹ️ Walker já está parado.")

    def add_waypoint(self, wp_type):
        row = self.wp_table.rowCount()
        self.wp_table.insertRow(row)
        self.wp_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.wp_table.setItem(row, 1, QTableWidgetItem(wp_type))
        self.wp_table.setItem(row, 2, QTableWidgetItem(""))
        self.wp_table.setItem(row, 3, QTableWidgetItem("x:0, y:0, z:0"))
        self.wp_table.setItem(row, 4, QTableWidgetItem(f"{self.range_x.value()} x {self.range_y.value()}"))
        self.wp_table.setItem(row, 5, QTableWidgetItem(""))

    def create_autorecorder_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.position_label = QLabel("Posição atual: x:0 y:0 z:0")
        layout.addWidget(self.position_label)

        self.start_record_button = QPushButton("Iniciar Gravação")
        self.stop_record_button = QPushButton("Parar Gravação")
        self.save_record_button = QPushButton("Salvar Caminho")

        layout.addWidget(self.start_record_button)
        layout.addWidget(self.stop_record_button)
        layout.addWidget(self.save_record_button)

        self.start_record_button.clicked.connect(self.start_recording)
        self.stop_record_button.clicked.connect(self.stop_recording)
        self.save_record_button.clicked.connect(self.save_path_to_json)

        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self.update_position_label)
        self.position_timer.start(1000)

        tab.setLayout(layout)
        return tab

    def update_position_label(self):
        try:
            x, y, z = self.reader.get_position()
            if None in (x, y, z):
                raise ValueError("Posição inválida.")
            self.position_label.setText(f"Posição atual: x:{x} y:{y} z:{z}")
            self.recorder.record_position(x, y, z)
        except Exception as e:
            self.position_label.setText(f"Erro ao ler posição: {e}")

    def start_recording(self):
        self.recorder.start()
        self.connection_status.setText("🟢 Gravando caminho...")

    def stop_recording(self):
        self.recorder.stop()
        self.connection_status.setText("🟡 Gravação parada.")

    def save_path_to_json(self):
        if not self.recorder.get_path():
            self.connection_status.setText("⚠️ Nenhum caminho gravado.")
            return
        self.recorder.save_to_file()
        self.connection_status.setText("✅ Caminho salvo.")

    def load_path_to_table(self):
        try:
            data = self.waypoint_manager.load_path()
            self.wp_table.setRowCount(0)

            for idx, coord in enumerate(data):
                self.wp_table.insertRow(idx)
                self.wp_table.setItem(idx, 0, QTableWidgetItem(str(idx + 1)))
                self.wp_table.setItem(idx, 1, QTableWidgetItem("Walk"))
                self.wp_table.setItem(idx, 2, QTableWidgetItem(""))
                self.wp_table.setItem(idx, 3, QTableWidgetItem(f"x:{coord['x']}, y:{coord['y']}, z:{coord['z']}"))
                self.wp_table.setItem(idx, 4, QTableWidgetItem("2 x 2"))
                self.wp_table.setItem(idx, 5, QTableWidgetItem(""))
            self.connection_status.setText("✅ Caminho carregado com sucesso.")
        except Exception as e:
            self.connection_status.setText(f"❌ Erro ao carregar: {e}")

    def start_path_execution(self):
        row_count = self.wp_table.rowCount()
        if row_count == 0:
            self.connection_status.setText("⚠️ Nenhum caminho carregado.")
            return

        self.path = []
        for i in range(row_count):
            item = self.wp_table.item(i, 3)
            if item:
                try:
                    coords = item.text().replace("x:", "").replace("y:", "").replace("z:", "").replace(" ", "")
                    x, y, z = map(int, coords.split(","))
                    self.path.append((x, y, z))
                except:
                    continue

        self.current_step = 0
        self.path_timer = QTimer()
        self.path_timer.timeout.connect(self.move_to_next_waypoint)
        self.path_timer.start(1000)
        self.connection_status.setText("🚶 Iniciando caminho...")

    def move_to_next_waypoint(self):
        if self.current_step >= len(self.path):
            self.path_timer.stop()
            self.connection_status.setText("✅ Caminho concluído.")
            return

        target = self.path[self.current_step]
        target_x, target_y, target_z = target

        self.connection_status.setText(f"➡️ Indo para: x:{target_x}, y:{target_y}, z:{target_z}")
        walk_to(target_x, target_y, target_z, show_status=self.connection_status.setText)
        self.current_step += 1


def main():
    app = QApplication(sys.argv)
    window = CavebotHUD()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
