# ui/settings_widget.py
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QListWidget, QLineEdit, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer
import win32api, json, os

class SettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.character_center = (0, 0)

        main_layout = QHBoxLayout()

        # Environment (botões principais)
        env_group = QGroupBox("Environment")
        env_layout = QVBoxLayout()

        self.set_character_btn = QPushButton("Set Character")
        self.set_character_btn.clicked.connect(self.prepare_capture)
        self.lbl_center = QLabel("Character center: Not set")

        env_layout.addWidget(self.set_character_btn)
        env_layout.addWidget(self.lbl_center)

        env_group.setLayout(env_layout)

        # Save/Load Profiles
        profiles_group = QGroupBox("Save/Load Profiles")
        profiles_layout = QVBoxLayout()

        self.profile_list = QListWidget()
        self.load_profiles()

        self.profile_name = QLineEdit()
        self.profile_name.setPlaceholderText("Profile name")

        buttons_layout = QHBoxLayout()
        self.save_profile_btn = QPushButton("Save Profile")
        self.load_profile_btn = QPushButton("Load Profile")

        self.save_profile_btn.clicked.connect(self.save_profile)
        self.load_profile_btn.clicked.connect(self.load_selected_profile)

        buttons_layout.addWidget(self.save_profile_btn)
        buttons_layout.addWidget(self.load_profile_btn)

        profiles_layout.addWidget(self.profile_list)
        profiles_layout.addWidget(self.profile_name)
        profiles_layout.addLayout(buttons_layout)

        profiles_group.setLayout(profiles_layout)

        # Adicionar grupos ao layout principal
        main_layout.addWidget(env_group)
        main_layout.addWidget(profiles_group)

        self.setLayout(main_layout)

        # Timer para captura externa
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_click)

    def prepare_capture(self):
        self.set_character_btn.setText("Click your character now (game client)")
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.timer.start(100)

    def check_click(self):
        if win32api.GetAsyncKeyState(0x01) & 0x8000:
            x, y = win32api.GetCursorPos()
            self.character_center = (x, y)
            self.lbl_center.setText(f"Character center: {self.character_center}")
            self.set_character_btn.setText("Set Character")
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.timer.stop()

    def save_profile(self):
        profile = {
            'character_center': self.character_center
        }
        name = self.profile_name.text()
        if name:
            if not os.path.exists("profiles"):
                os.makedirs("profiles")
            with open(f"profiles/{name}.json", "w") as file:
                json.dump(profile, file)
            self.load_profiles()
            self.profile_name.clear()

    def load_profiles(self):
        self.profile_list.clear()
        if not os.path.exists("profiles"):
            os.makedirs("profiles")
        for file in os.listdir("profiles"):
            if file.endswith('.json'):
                self.profile_list.addItem(file.replace('.json', ''))

    def load_selected_profile(self):
        selected_item = self.profile_list.currentItem()
        if selected_item:
            name = selected_item.text()
            with open(f"profiles/{name}.json", "r") as file:
                profile = json.load(file)
            self.character_center = tuple(profile.get('character_center', (0, 0)))
            self.lbl_center.setText(f"Character center: {self.character_center}")
