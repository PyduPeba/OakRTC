# ui/script_loader.py

import json
from PyQt6.QtWidgets import QFileDialog, QTableWidgetItem

def load_script(parent, wp_table, connection_status):
    filename, _ = QFileDialog.getOpenFileName(parent, "Selecione o script", "", "JSON Files (*.json)")
    if not filename:
        connection_status.setText("❌ Nenhum arquivo selecionado.")
        return
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        wp_table.setRowCount(0)
        for idx, coord in enumerate(data):
            wp_table.insertRow(idx)
            wp_table.setItem(idx, 0, QTableWidgetItem(str(idx + 1)))
            wp_table.setItem(idx, 1, QTableWidgetItem(coord.get("type", "Walk")))
            wp_table.setItem(idx, 2, QTableWidgetItem(coord.get("label", "")))
            wp_table.setItem(idx, 3, QTableWidgetItem(f"x:{coord['x']}, y:{coord['y']}, z:{coord['z']}"))
            wp_table.setItem(idx, 4, QTableWidgetItem(coord.get("range", "2 x 2")))
            wp_table.setItem(idx, 5, QTableWidgetItem(coord.get("action", "")))
        connection_status.setText("✅ Script carregado com sucesso.")
    except Exception as e:
        connection_status.setText(f"❌ Erro ao carregar: {e}")
