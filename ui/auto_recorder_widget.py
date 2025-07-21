from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QGroupBox, QHBoxLayout, QFrame, QTextEdit, QFileDialog
)
from PyQt6.QtCore import QTimer, QTime, Qt
from core.waypoint_recorder import WaypointRecorder
from core.memory_reader import MemoryReader


class AutoRecorderWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.recorder = WaypointRecorder()
        self.reader = MemoryReader()
        self.reader.load_client()
        self.elapsed_time = QTime(0, 0, 0)

        self.setup_ui()
        self.setup_timer()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Botões (ajustado)
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)  # <-- Alinha à esquerda
        button_layout.setSpacing(10)

        self.btn_gravar = QPushButton("🔴 Gravar")
        self.btn_gravar.setFixedWidth(80)
        self.btn_gravar.clicked.connect(self.start_recording)
        button_layout.addWidget(self.btn_gravar)

        self.btn_stop = QPushButton("⏹️ Stop")
        self.btn_stop.setFixedWidth(80)
        self.btn_stop.clicked.connect(self.stop_recording)
        button_layout.addWidget(self.btn_stop)

        self.btn_save = QPushButton("💾 Salvar")
        self.btn_save.setFixedWidth(80)
        self.btn_save.clicked.connect(self.save_path_to_json)
        button_layout.addWidget(self.btn_save)

        layout.addLayout(button_layout)

        # Status Box
        self.status_box = QGroupBox("ℹ️ Status da Gravação")
        status_layout = QVBoxLayout()

        self.status_msg = QLabel("• Sistema pronto para gravação")
        status_layout.addWidget(self.status_msg)

        self.instructions = QTextEdit(
            "📋 Instruções:\n• Clique em 'Grava' para iniciar a gravação\n"
            "• Use 'Stop' para pausar ou parar\n"
            "• Pressione 'Salve' para salvar o caminho"
        )
        self.instructions.setReadOnly(True)
        self.instructions.setFixedHeight(80)
        status_layout.addWidget(self.instructions)

        self.position_label = QLabel("📍 Posição: x:0 y:0 z:0")
        self.duration_label = QLabel("⏱️ Duração: 00:00")
        self.size_label = QLabel("📦 Tamanho: 0 pontos")

        status_layout.addWidget(self.position_label)
        status_layout.addWidget(self.duration_label)
        status_layout.addWidget(self.size_label)

        self.status_box.setLayout(status_layout)
        layout.addWidget(self.status_box)

        self.setLayout(layout)

    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(800)

    def update_status(self):
        try:
            x, y, z = self.reader.get_position()
            self.position_label.setText(f"📍 Posição: x:{x} y:{y} z:{z}")
            self.recorder.record_position(x, y, z)

            # tempo
            if self.recorder.recording:
                self.elapsed_time = self.elapsed_time.addSecs(1)
                self.duration_label.setText(f"⏱️ Duração: {self.elapsed_time.toString('mm:ss')}")
                self.size_label.setText(f"📦 Tamanho: {len(self.recorder.get_path())} pontos")

        except:
            self.position_label.setText("⚠️ Erro ao ler posição")

    def start_recording(self):
        self.recorder.start()
        self.elapsed_time = QTime(0, 0, 0)
        self.status_msg.setText("🟢 Gravando caminho...")

    def stop_recording(self):
        self.recorder.stop()
        self.status_msg.setText("🟡 Gravação parada.")

    def save_path_to_json(self):
        if not self.recorder.get_path():
            self.status_msg.setText("⚠️ Nenhum caminho gravado.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar Caminho", "", "JSON Files (*.json)"
        )
        if file_path:
            self.recorder.save_to_file(file_path)
            self.status_msg.setText(f"✅ Caminho salvo em: {file_path}")
