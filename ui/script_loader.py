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
            wp_table.setItem(idx, 0, QTableWidgetItem(str(coord.get("WP", idx + 1))))
            wp_table.setItem(idx, 1, QTableWidgetItem(coord.get("Type", "Walk")))
            wp_table.setItem(idx, 2, QTableWidgetItem(coord.get("Label", "")))
            wp_table.setItem(idx, 3, QTableWidgetItem(f"x:{coord['X']}, y:{coord['Y']}, z:{coord['Z']}"))
            wp_table.setItem(idx, 4, QTableWidgetItem(f"{coord.get('RangeX', 0)} x {coord.get('RangeY', 0)}"))
            wp_table.setItem(idx, 5, QTableWidgetItem(str(coord.get("Action", ""))))
            if coord.get("Type", "").lower() == "action" and "script" in coord:
                parent.script_textedit.setPlainText(coord["script"])

        connection_status.setText("✅ Script carregado com sucesso.")
    except Exception as e:
        connection_status.setText(f"❌ Erro ao carregar: {e}")

