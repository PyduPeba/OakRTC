# ui/main_windows.py
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QHBoxLayout, QSpinBox, QLabel, QGroupBox, QTextEdit, QComboBox, QFileDialog
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
from core.action_executor import handle_action
from logic.walker_thread import WalkerThread

from components.hud_log_widget import HUDLogWidget

from ui.script_loader import load_script
from ui.settings_widget import SettingsWidget
from ui.auto_recorder_widget import AutoRecorderWidget



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
        self.character_center = (0, 0)

        self.setWindowTitle("Cavebot HUD - Oak BOT")
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
        self.auto_recorder_tab = AutoRecorderWidget()
        self.tabs.addTab(self.auto_recorder_tab, "AutoRecorder")
        self.settings_widget = SettingsWidget()
        self.tabs.addTab(self.settings_widget, "Settings")


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

        #Editor Basico
        self.script_editor_group = QGroupBox("Editor de Script")
        self.script_editor_layout = QVBoxLayout()

        self.script_label = QLabel("Digite seu script:")
        self.script_textedit = QTextEdit()
        self.script_textedit.setPlaceholderText(
            "Exemplo:\nif $posz == 8 then\n  say 'hi'\n  wait 1000\n  say 'trade'\nend"
        )

        self.script_editor_layout.addWidget(self.script_label)
        self.script_editor_layout.addWidget(self.script_textedit)
        self.script_editor_group.setLayout(self.script_editor_layout)

        main_layout.addWidget(self.script_editor_group)

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

        self.direction_combo = QComboBox()
        self.direction_combo.addItems([
            "Center", "North", "South", "East", "West",
            "Northeast", "Northwest", "Southeast", "Southwest"
        ])
        side_panel.addWidget(QLabel("Direction:"))
        side_panel.addWidget(self.direction_combo)

        # Botões de waypoint (igual print)
        for label in ["Walk", "Stand", "Door", "Ladder", "Use", "Rope", "Shovel", "Machete", "Other tool", "Action"]:
            btn = QPushButton(label)
            if label == "Stand":
                btn.clicked.connect(self.handle_stand)
            else:
                btn.clicked.connect(lambda _, l=label: self.add_waypoint(l))
            btn.setFixedHeight(30)
            side_panel.addWidget(btn)

        load_button = QPushButton("Load Script")
        load_button.clicked.connect(lambda: load_script(self, self.wp_table, self.connection_status))
        load_button.setToolTip("Carrega um script JSON de waypoints.")
        load_button.setFixedHeight(30)
        side_panel.addWidget(load_button)

        save_button = QPushButton("Save Script")
        save_button.setFixedHeight(30)
        save_button.clicked.connect(self.save_script)
        side_panel.addWidget(save_button)

        self.btn_test_script = QPushButton("▶️ Testar Script")
        self.btn_test_script.setFixedHeight(30)
        self.script_editor_layout.addWidget(self.btn_test_script)
        self.btn_test_script.clicked.connect(self.testar_script_manual)


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
        character_center = self.settings_widget.character_center
        self.walker_thread = WalkerThread(
        self.path,
        hud_log=self.hud_log,
        character_center=character_center
        )

        # self.walker_thread = WalkerThread(self.path)
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
        x, y, z = self.reader.get_position()
        if None in (x, y, z) or (x, y, z) == (0, 0, 0):
            self.connection_status.setText("❌ Posição inválida! Verifique a conexão com o cliente.")
            return
        row = self.wp_table.rowCount()
        self.wp_table.insertRow(row)
        self.wp_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.wp_table.setItem(row, 1, QTableWidgetItem("Walk"))
        self.wp_table.setItem(row, 2, QTableWidgetItem(""))  # Sem direção específica para walk
        self.wp_table.setItem(row, 3, QTableWidgetItem(f"x:{x}, y:{y}, z:{z}"))
        self.wp_table.setItem(row, 4, QTableWidgetItem(f"{self.range_x.value()} x {self.range_y.value()}"))
        self.wp_table.setItem(row, 5, QTableWidgetItem(""))
        self.connection_status.setText(f"🟢 Waypoint 'Walk' adicionado em x:{x}, y:{y}, z:{z}")

    def testar_script_manual(self):
        script = self.script_textedit.toPlainText().strip()
        if not script:
            self.connection_status.setText("❌ Nenhum script para testar.")
            return
        try:
            reader = MemoryReader()
            reader.load_client()
            handle_action(script.splitlines(), reader=reader)
            self.connection_status.setText("✅ Script executado.")
        except Exception as e:
            self.connection_status.setText(f"❌ Erro ao executar: {e}")


    def handle_stand(self):
        direction = self.direction_combo.currentText()
        x, y, z = self.reader.get_position()
        if None in (x, y, z) or (x, y, z) == (0, 0, 0):
            self.connection_status.setText("❌ Posição inválida! Verifique a conexão com o cliente.")
            return
        row = self.wp_table.rowCount()
        self.wp_table.insertRow(row)
        self.wp_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.wp_table.setItem(row, 1, QTableWidgetItem("Stand"))
        self.wp_table.setItem(row, 2, QTableWidgetItem(direction))
        self.wp_table.setItem(row, 3, QTableWidgetItem(f"x:{x}, y:{y}, z:{z}"))
        self.wp_table.setItem(row, 4, QTableWidgetItem(f"{self.range_x.value()} x {self.range_y.value()}"))
        self.wp_table.setItem(row, 5, QTableWidgetItem(""))
        self.connection_status.setText(f"🟢 Waypoint 'Stand' ({direction}) adicionado em x:{x}, y:{y}, z:{z}")




    def save_script(self):
        path = []
        for i in range(self.wp_table.rowCount()):
            coord_item = self.wp_table.item(i, 3)
            if coord_item:
                try:
                    coords = coord_item.text().replace("x:", "").replace("y:", "").replace("z:", "").replace(" ", "")
                    x, y, z = map(int, coords.split(","))

                    item = self.wp_table.item(i, 1)
                    item_type = item.text() if item is not None else "Walk"

                    item = self.wp_table.item(i, 2)
                    label = item.text() if item is not None else ""

                    item = self.wp_table.item(i, 4)
                    range_val = item.text() if item is not None else "0 x 0"

                    item = self.wp_table.item(i, 5)
                    action = item.text() if item is not None else ""


                    script = self.script_textedit.toPlainText() if item_type.lower() == "action" else ""
                    path.append({
                        "x": x,
                        "y": y,
                        "z": z,
                        "type": item_type,
                        "label": label,
                        "range": range_val,
                        "action": action,
                        "script": script
                    })
                except Exception as e:
                    print(f"Erro ao ler linha {i}: {e}")

        if not path:
            self.connection_status.setText("⚠️ Nenhum waypoint para salvar.")
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Salvar Script", "", "JSON Files (*.json)")
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(path, f, indent=4)
            self.connection_status.setText("✅ Script salvo com sucesso.")

    # def load_path_to_table(self):
    #     try:
    #         data = self.waypoint_manager.load_path()
    #         self.wp_table.setRowCount(0)

    #         for idx, coord in enumerate(data):
    #             self.wp_table.insertRow(idx)
    #             self.wp_table.setItem(idx, 0, QTableWidgetItem(str(idx + 1)))
    #             self.wp_table.setItem(idx, 1, QTableWidgetItem("Walk"))
    #             self.wp_table.setItem(idx, 2, QTableWidgetItem(""))
    #             self.wp_table.setItem(idx, 3, QTableWidgetItem(f"x:{coord['x']}, y:{coord['y']}, z:{coord['z']}"))
    #             self.wp_table.setItem(idx, 4, QTableWidgetItem("2 x 2"))
    #             self.wp_table.setItem(idx, 5, QTableWidgetItem(""))
    #         self.connection_status.setText("✅ Caminho carregado com sucesso.")
    #     except Exception as e:
    #         self.connection_status.setText(f"❌ Erro ao carregar: {e}")

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

    def create_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Botão para setar o centro do personagem
        self.set_character_button = QPushButton("Set Character (Clique onde está seu personagem)")
        self.set_character_button.clicked.connect(self.set_character_center)
        layout.addWidget(self.set_character_button)

        # Label para mostrar coordenada
        self.center_label = QLabel("Centro do personagem: Não definido")
        layout.addWidget(self.center_label)

        # Botão load/save configs
        buttons = QHBoxLayout()
        self.load_settings_button = QPushButton("Load Config")
        self.save_settings_button = QPushButton("Save Config")
        self.load_settings_button.clicked.connect(self.load_screen_settings)
        self.save_settings_button.clicked.connect(self.save_screen_settings)
        buttons.addWidget(self.load_settings_button)
        buttons.addWidget(self.save_settings_button)
        layout.addLayout(buttons)

        tab.setLayout(layout)
        return tab
    
    

    def save_screen_settings(self):
        data = {'character_center': self.character_center}
        with open("screen_settings.json", "w") as f:
            json.dump(data, f)
        self.center_label.setText(f"Configuração salva! {self.character_center}")

    def load_screen_settings(self):
        if os.path.exists("screen_settings.json"):
            with open("screen_settings.json", "r") as f:
                data = json.load(f)
            self.character_center = tuple(data.get('character_center', (0,0)))
            self.center_label.setText(f"Configuração carregada: {self.character_center}")
        else:
            self.center_label.setText("Nenhuma configuração encontrada.")





def main():
    app = QApplication(sys.argv)
    window = CavebotHUD()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
