# ui/stand_widget.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QComboBox

class StandWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.stand_direction = QComboBox()
        self.stand_direction.addItems([
            "Center", "North", "South", "East", "West",
            "Northeast", "Northwest", "Southeast", "Southwest"
        ])

        self.stand_button = QPushButton("Stand")
        self.stand_button.clicked.connect(self.on_stand_clicked)

        layout = QVBoxLayout()
        layout.addWidget(self.stand_direction)
        layout.addWidget(self.stand_button)
        self.setLayout(layout)

    def on_stand_clicked(self):
        direction = self.stand_direction.currentText()
        parent = self.parent()
        if parent and hasattr(parent, "executar_stand"):
            parent.executar_stand(direction)  # Exemplo: chama função do MainWindow

