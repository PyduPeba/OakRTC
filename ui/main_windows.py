# ui/main_windows.py
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QHBoxLayout, QSpinBox, QLabel, QGroupBox, QTextEdit
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QShortcut, QKeySequence
import sys, json, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.memory_reader import MemoryReader
from core.memory_utils import read_my_wpt
from logic.waypoint_manager import WaypointManager
from core.waypoint_recorder import WaypointRecorder
from core.walker import walk_to
from logic.walker_thread import WalkerThread

from components.hud_log_widget import HUDLogWidget



class CavebotHUD(QMainWindow):
    def __init__(self):
        super().__init__()
        self.reader = MemoryReader()
        self.reader.load_client()
        self.hud_log = QTextEdit()  # seu widget de HUD de logs
        self.hud_log.setReadOnly(True)
        self.waypoint_manager = WaypointManager()
        self.walker_thread = None
        self.path = []
        self.recorder = WaypointRecorder()

        self.setWindowTitle("Cavebot HUD - RubinOT")
        self.setGeometry(100, 100, 1000, 600)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.hud_log = HUDLogWidget()
        self.tab_cavebot = self.create_cavebot_tab()
        self.tabs.addTab(self.tab_cavebot, "Cavebot")
        self.tabs.addTab(QWidget(), "Targeting")
        self.tabs.addTab(QWidget(), "Looting")
        self.tabs.addTab(QWidget(), "Healing")
        self.tabs.addTab(QWidget(), "Support")
        self.tabs.addTab(self.create_autorecorder_tab(), "AutoRecorder")

    def keyPressEvent(self, event):
        if self.tabs.currentWidget() == self.tab_cavebot:
            if event.key() == Qt.Key.Key_Delete:
                self.delete_selected_waypoint()
        super().keyPressEvent(event)

    def try_connect(self):
        try:
            self.reader.load_client()
            self.connection_status.setText("🟢 Cliente conectado com sucesso.")
        except Exception as e:
            self.connection_status.setText(f"🔴 Erro ao conectar: {e}")

    def create_cavebot_tab(self):
        tab = QWidget()
        main_layout = QHBoxLayout(tab)

        # Tabela central
        self.wp_table = QTableWidget()
        self.wp_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.wp_table.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
        self.wp_table.setColumnCount(6)
        self.wp_table.setHorizontalHeaderLabels(["WP", "Type", "Label", "Coordinates", "Range", "Action"])
        self.wp_table.setRowCount(0)
        self.wp_table.setMinimumWidth(500)
        main_layout.addWidget(self.wp_table, 3)

        connection_panel = QVBoxLayout()
        self.connection_status = QLabel("🔴 Cliente não conectado.")
        self.connect_button = QPushButton("Conectar")
        self.connect_button.clicked.connect(self.try_connect)
        connection_panel.addWidget(self.connection_status)
        connection_panel.addWidget(self.connect_button)
        main_layout.addLayout(connection_panel)

        main_layout.addWidget(self.wp_table)

        # Painel lateral direito (Botões + Range)
        side_panel = QVBoxLayout()
        # Range
        range_box = QHBoxLayout()
        self.range_x = QSpinBox()
        self.range_y = QSpinBox()
        range_box.addWidget(QLabel("Range:"))
        range_box.addWidget(self.range_x)
        range_box.addWidget(QLabel("x"))
        range_box.addWidget(self.range_y)
        side_panel.addLayout(range_box)

        # Botões de waypoint (igual print)
        for label in ["Walk", "Stand", "Door", "Ladder", "Use", "Rope", "Shovel", "Machete", "Other tool", "Action"]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, l=label: self.add_waypoint(l))
            btn.setFixedHeight(30)
            side_panel.addWidget(btn)

        load_button = QPushButton("Load Caminho JSON")
        load_button.clicked.connect(self.load_path_to_table)
        load_button.setFixedHeight(30)
        side_panel.addWidget(load_button)

        # Botões especiais: Show HUD, Start/Stop
        self.btn_show_hud = QPushButton("Show HUD")
        self.btn_show_hud.setFixedHeight(30)
        self.btn_show_hud.clicked.connect(self.hud_log.show)
        side_panel.addWidget(self.btn_show_hud)
        start_walker_button = QPushButton("▶️ Start Walker")
        stop_walker_button = QPushButton("⏹️ Stop Walker")
        start_walker_button.setFixedHeight(30)
        stop_walker_button.setFixedHeight(30)
        start_walker_button.clicked.connect(self.start_walker)
        stop_walker_button.clicked.connect(self.stop_walker)
        side_panel.addWidget(start_walker_button)
        side_panel.addWidget(stop_walker_button)
        self.btn_delete_wpt = QPushButton("🗑️ Deletar Waypoint")
        self.btn_delete_wpt.setFixedHeight(30)
        self.btn_delete_wpt.clicked.connect(self.delete_selected_waypoint)
        side_panel.addWidget(self.btn_delete_wpt)

        # Painel botões do HUD
        side_panel_widget = QWidget()
        side_panel_widget.setLayout(side_panel)
        side_panel_widget.setMaximumWidth(220)  # Ou ajuste para o valor desejado
        side_panel_widget.setMinimumWidth(180)  # Evita que fique muito fino

        main_layout.addWidget(side_panel_widget)


        # main_layout.addLayout(side_panel, 1)

        self.hud_log.hide()
        return tab
    
    # Método para logar do walker para HUD
    def walker_log(self, message):
        self.hud_log.append(message)
    
    def start_walker(self):
        # Aqui você gera ou lê os waypoints da tabela
        self.path = self.collect_waypoints_from_table()  # Implemente conforme seu projeto!

        # Antes de criar nova thread, pare a anterior se necessário
        if self.walker_thread and self.walker_thread.isRunning():
            self.hud_log.append("[HUD] 🚫 Walker já está rodando!")
            return

        self.walker_thread = WalkerThread(self.path)
        self.walker_thread.log_signal.connect(self.hud_log.log)
        self.walker_thread.status_signal.connect(self.hud_log.set_status)  # <- Aqui conecta!
        self.walker_thread.start()
        self.hud_log.log("[HUD] 🚶 Walker iniciado.")

    def collect_waypoints_from_table(self):
        # Aqui você extrai os dados da tabela e retorna uma lista de dicts [{X:...,Y:...,Z:...,Action:...,Direction:...}, ...]
        waypoints = []
        row_count = self.wp_table.rowCount()
        for i in range(row_count):
            item = self.wp_table.item(i, 3)
            if item:
                coords = item.text().replace("x:", "").replace("y:", "").replace("z:", "").replace(" ", "")
                x, y, z = map(int, coords.split(","))
                waypoints.append({
                    "X": x,
                    "Y": y,
                    "Z": z,
                    "Action": 0,
                    "Direction": 9
                })
        return waypoints

    def stop_walker(self):
        if self.walker_thread and self.walker_thread.isRunning():
            self.walker_thread.stop()
            self.hud_log.append("[HUD] 🛑 Walker parado.")
        else:
            self.hud_log.append("[HUD] Walker não está rodando.")

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

    def delete_selected_waypoint(self):
        selected = self.wp_table.selectedItems()
        if not selected:
            self.connection_status.setText("⚠️ Selecione um waypoint para deletar.")
            return

        # Pega a linha do primeiro item selecionado (só funciona para seleção única ou múltipla simples)
        rows = set()
        for item in selected:
            rows.add(item.row())
        # Remove da maior para menor, para não dar problema nos índices
        for row in sorted(rows, reverse=True):
            self.wp_table.removeRow(row)
        self.connection_status.setText("🗑️ Waypoint(s) deletado(s).")



def main():
    app = QApplication(sys.argv)
    window = CavebotHUD()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
