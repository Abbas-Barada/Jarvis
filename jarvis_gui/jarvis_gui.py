import sys

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QFrame
)

from PySide6.QtGui import QFont

app = QApplication(sys.argv)
app.setFont(QFont("JetBrains Mono", 10))

window = QWidget()
window.setStyleSheet("""
QWidget {
    background-color: #1e1e1e;
    color: white;
    font-size: 12pt;
}

QTextEdit {
    background-color: #111111;
    border: 1px solid #444;
    font-family: JetBrains Mono;
}

QLabel {
    padding: 3px;
}
""")
window.setWindowTitle("Jarvis")
window.resize(900, 600)

layout = QVBoxLayout()

title = QLabel("JARVIS")
title.setStyleSheet("""
font-size: 28px;
font-weight: bold;
padding-bottom: 5px;
""")

layout.addWidget(title)
status = QLabel("🟢 READY")
folder = QLabel("📁 Folder: None")
command = QLabel("🎤 Command: None")

status.setStyleSheet("font-size: 18px; font-weight: bold;")
folder.setStyleSheet("font-size: 14px;")
command.setStyleSheet("font-size: 14px;")

log = QTextEdit()
log.append("Jarvis started")
log.append("Model: Gemma 3 4B")
log.append("Press F8 to talk")
log.setReadOnly(True)

layout.addWidget(status)
layout.addWidget(folder)
layout.addWidget(command)
layout.addWidget(log)

window.setLayout(layout)

window.show()

sys.exit(app.exec())
