import sys
import time
import threading
import queue
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QTextEdit,
    QVBoxLayout, QHBoxLayout, QPushButton,
    QFrame, QSizePolicy, QScrollArea
)
from PySide6.QtGui import QFont, QColor, QTextCursor, QIcon, QKeySequence, QShortcut
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QThread


# ── Signal bridge (thread-safe UI updates) ────────────────────────────────────

class Bridge(QObject):
    log_signal      = Signal(str, str)   # (message, level)
    status_signal   = Signal(str)        # "LISTENING" | "RECORDING" | "THINKING" | "SPEAKING"
    folder_signal   = Signal(str)
    command_signal  = Signal(str)
    jarvis_signal   = Signal(str)


bridge = Bridge()


# ── Colour palette ─────────────────────────────────────────────────────────────

BG         = "#0d0f12"
BG2        = "#13161b"
BG3        = "#1c2028"
ACCENT     = "#00d4aa"        # teal
ACCENT2    = "#0099ff"        # blue
MUTED      = "#4a5568"
TEXT       = "#e2e8f0"
TEXT2      = "#718096"
RED        = "#fc8181"
AMBER      = "#f6ad55"
GREEN      = "#68d391"


STATUS_COLORS = {
    "READY":      (ACCENT,  "●"),
    "LISTENING":  (ACCENT,  "◉"),
    "RECORDING":  (RED,     "⏺"),
    "THINKING":   (AMBER,   "⟳"),
    "SPEAKING":   (ACCENT2, "▶"),
    "OFFLINE":    (MUTED,   "○"),
}


# ── Main window ────────────────────────────────────────────────────────────────

class JarvisWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("JARVIS")
        self.resize(960, 680)
        self.setMinimumSize(720, 480)
        self._apply_stylesheet()
        self._build_ui()
        self._connect_signals()
        self._start_clock()

    # ── Stylesheet ─────────────────────────────────────────────────────────────

    def _apply_stylesheet(self):
        self.setStyleSheet(f"""
        QWidget {{
            background: {BG};
            color: {TEXT};
            font-family: "JetBrains Mono", "Cascadia Code", "Fira Code", monospace;
            font-size: 11pt;
        }}
        QScrollBar:vertical {{
            background: {BG2};
            width: 6px;
            border-radius: 3px;
        }}
        QScrollBar::handle:vertical {{
            background: {MUTED};
            border-radius: 3px;
            min-height: 20px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QTextEdit {{
            background: {BG2};
            border: 1px solid {BG3};
            border-radius: 6px;
            padding: 8px;
            color: {TEXT};
            selection-background-color: {ACCENT};
        }}
        QPushButton {{
            background: {BG3};
            border: 1px solid {MUTED};
            border-radius: 5px;
            padding: 6px 14px;
            color: {TEXT};
            font-family: "JetBrains Mono", monospace;
            font-size: 10pt;
        }}
        QPushButton:hover {{
            background: #252b36;
            border-color: {ACCENT};
            color: {ACCENT};
        }}
        QPushButton:pressed {{
            background: {BG};
        }}
        QLabel {{
            background: transparent;
        }}
        """)

    # ── UI layout ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top bar ────────────────────────────────────────────────────────────
        topbar = QFrame()
        topbar.setFixedHeight(56)
        topbar.setStyleSheet(f"""
            QFrame {{ background: {BG2}; border-bottom: 1px solid {BG3}; }}
        """)
        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel("JARVIS")
        title.setStyleSheet(f"""
            font-size: 20pt;
            font-weight: bold;
            letter-spacing: 6px;
            color: {ACCENT};
        """)
        tb_layout.addWidget(title)
        tb_layout.addStretch()

        self.clock_label = QLabel()
        self.clock_label.setStyleSheet(f"color: {TEXT2}; font-size: 10pt;")
        tb_layout.addWidget(self.clock_label)

        root.addWidget(topbar)

        # ── Body ───────────────────────────────────────────────────────────────
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        # Left sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(f"background: {BG2}; border-right: 1px solid {BG3};")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(16, 20, 16, 20)
        sb_layout.setSpacing(20)

        # Status indicator
        self.status_dot  = QLabel("●")
        self.status_text = QLabel("READY")
        self.status_dot.setStyleSheet(f"color: {ACCENT}; font-size: 16pt;")
        self.status_text.setStyleSheet(f"color: {ACCENT}; font-size: 11pt; font-weight: bold; letter-spacing: 2px;")

        status_row = QHBoxLayout()
        status_row.addWidget(self.status_dot)
        status_row.addWidget(self.status_text)
        status_row.addStretch()
        sb_layout.addLayout(status_row)

        # Divider
        sb_layout.addWidget(self._divider())

        # Info labels
        self._folder_label  = self._info_label("📁 FOLDER", "none")
        self._command_label = self._info_label("🎤 LAST CMD", "—")

        sb_layout.addWidget(self._folder_label[0])
        sb_layout.addWidget(self._folder_label[1])
        sb_layout.addWidget(self._command_label[0])
        sb_layout.addWidget(self._command_label[1])

        sb_layout.addWidget(self._divider())

        # Hotkey legend
        for key, action in [("F8", "Talk"), ("F9", "Clear memory"), ("F10", "Exit")]:
            row = QHBoxLayout()
            k = QLabel(key)
            k.setStyleSheet(f"""
                color: {BG};
                background: {ACCENT};
                border-radius: 3px;
                padding: 1px 6px;
                font-size: 9pt;
                font-weight: bold;
            """)
            k.setFixedWidth(32)
            k.setAlignment(Qt.AlignmentFlag.AlignCenter)
            a = QLabel(action)
            a.setStyleSheet(f"color: {TEXT2}; font-size: 10pt;")
            row.addWidget(k)
            row.addSpacing(8)
            row.addWidget(a)
            row.addStretch()
            sb_layout.addLayout(row)

        sb_layout.addStretch()

        # Action buttons
        self.btn_clear = QPushButton("Clear memory")
        self.btn_clear.clicked.connect(self._on_clear_memory)
        sb_layout.addWidget(self.btn_clear)

        self.btn_clear_log = QPushButton("Clear log")
        self.btn_clear_log.clicked.connect(self._clear_log)
        sb_layout.addWidget(self.btn_clear_log)

        body.addWidget(sidebar)

        # Right — log pane
        right = QFrame()
        right.setStyleSheet(f"background: {BG};")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(16, 16, 16, 12)
        right_layout.setSpacing(8)

        log_header = QLabel("OUTPUT LOG")
        log_header.setStyleSheet(f"color: {TEXT2}; font-size: 9pt; letter-spacing: 2px;")
        right_layout.addWidget(log_header)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        right_layout.addWidget(self.log)

        # Bottom status bar
        statusbar = QFrame()
        statusbar.setFixedHeight(32)
        statusbar.setStyleSheet(f"background: {BG2}; border-top: 1px solid {BG3};")
        sb2 = QHBoxLayout(statusbar)
        sb2.setContentsMargins(16, 0, 16, 0)

        self.bottom_status = QLabel("Ready. Press F8 to talk.")
        self.bottom_status.setStyleSheet(f"color: {TEXT2}; font-size: 9pt;")
        sb2.addWidget(self.bottom_status)
        sb2.addStretch()

        right_layout.addWidget(statusbar)
        body.addWidget(right, stretch=1)
        root.addLayout(body, stretch=1)

        # Initial log entries
        self._append_log("system", "Jarvis online.")
        self._append_log("system", "Press F8 to start talking.")

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color: {BG3};")
        return line

    def _info_label(self, caption, value):
        cap = QLabel(caption)
        cap.setStyleSheet(f"color: {TEXT2}; font-size: 8pt; letter-spacing: 1px;")
        val = QLabel(value)
        val.setStyleSheet(f"color: {TEXT}; font-size: 9pt;")
        val.setWordWrap(True)
        return cap, val

    # ── Signal connections ─────────────────────────────────────────────────────

    def _connect_signals(self):
        bridge.log_signal.connect(self._append_log)
        bridge.status_signal.connect(self._set_status)
        bridge.folder_signal.connect(self._set_folder)
        bridge.command_signal.connect(self._set_command)

    # ── Clock ──────────────────────────────────────────────────────────────────

    def _start_clock(self):
        self._tick()
        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(1000)

    def _tick(self):
        self.clock_label.setText(datetime.now().strftime("%H:%M:%S  %a %d %b %Y"))

    # ── Slot handlers ──────────────────────────────────────────────────────────

    def _set_status(self, status: str):
        color, dot = STATUS_COLORS.get(status, (MUTED, "○"))
        self.status_dot.setText(dot)
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 16pt;")
        self.status_text.setText(status)
        self.status_text.setStyleSheet(
            f"color: {color}; font-size: 11pt; font-weight: bold; letter-spacing: 2px;"
        )
        self.bottom_status.setText({
            "READY":     "Ready. Press F8 to talk.",
            "LISTENING": "Listening for F8...",
            "RECORDING": "Recording — press F8 to stop.",
            "THINKING":  "Processing your request...",
            "SPEAKING":  "Speaking...",
        }.get(status, status))

    def _set_folder(self, path: str):
        short = path if len(path) < 28 else "…" + path[-26:]
        self._folder_label[1].setText(short)
        self._folder_label[1].setToolTip(path)

    def _set_command(self, cmd: str):
        short = cmd if len(cmd) < 28 else cmd[:25] + "…"
        self._command_label[1].setText(short)
        self._command_label[1].setToolTip(cmd)

    def _append_log(self, level: str, message: str):
        """level: 'user' | 'jarvis' | 'system' | 'error'"""
        ts = datetime.now().strftime("%H:%M:%S")

        colors = {
            "user":   (ACCENT2,  "YOU"),
            "jarvis": (ACCENT,   "JARVIS"),
            "system": (MUTED,    "SYS"),
            "error":  (RED,      "ERR"),
        }
        col, tag = colors.get(level, (TEXT2, level.upper()))

        cursor = self.log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log.setTextCursor(cursor)

        # Timestamp + tag
        self.log.setTextColor(QColor(MUTED))
        self.log.insertPlainText(f"\n{ts}  ")

        self.log.setTextColor(QColor(col))
        self.log.insertPlainText(f"[{tag}]  ")

        self.log.setTextColor(QColor(TEXT))
        self.log.insertPlainText(message)

        self.log.moveCursor(QTextCursor.MoveOperation.End)

    def _clear_log(self):
        self.log.clear()
        self._append_log("system", "Log cleared.")

    def _on_clear_memory(self):
        # This emits to jarvis_main via monkey-patching — see integration note
        bridge.log_signal.emit("system", "Memory cleared.")
        if _memory_clear_cb:
            _memory_clear_cb()


# ── Public API (called from jarvis_main.py) ───────────────────────────────────

_memory_clear_cb = None

def set_status(status: str):
    """Call from jarvis_main: 'READY' | 'RECORDING' | 'THINKING' | 'SPEAKING'"""
    bridge.status_signal.emit(status)

def log(level: str, message: str):
    """level: 'user' | 'jarvis' | 'system' | 'error'"""
    bridge.log_signal.emit(level, message)

def set_folder(path: str):
    bridge.folder_signal.emit(path or "none")

def set_command(cmd: str):
    bridge.command_signal.emit(cmd)

def set_memory_clear_callback(fn):
    global _memory_clear_cb
    _memory_clear_cb = fn


# ── Entry point (standalone / dev preview) ────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)

    win = JarvisWindow()
    win.show()

    # Demo log entries for preview
    QTimer.singleShot(800,  lambda: bridge.log_signal.emit("system",  "Whisper model loaded."))
    QTimer.singleShot(1200, lambda: bridge.status_signal.emit("LISTENING"))
    QTimer.singleShot(2200, lambda: bridge.log_signal.emit("user",    "open spotify"))
    QTimer.singleShot(2400, lambda: bridge.status_signal.emit("THINKING"))
    QTimer.singleShot(3000, lambda: bridge.log_signal.emit("jarvis",  "Opening Spotify"))
    QTimer.singleShot(3100, lambda: bridge.status_signal.emit("SPEAKING"))
    QTimer.singleShot(3800, lambda: bridge.status_signal.emit("READY"))
    QTimer.singleShot(4500, lambda: bridge.log_signal.emit("user",    "what's the weather?"))
    QTimer.singleShot(4700, lambda: bridge.status_signal.emit("THINKING"))
    QTimer.singleShot(5500, lambda: bridge.log_signal.emit("jarvis",  "Düsseldorf: partly cloudy, 17°C, wind 12 km/h."))
    QTimer.singleShot(5600, lambda: bridge.status_signal.emit("SPEAKING"))
    QTimer.singleShot(6400, lambda: bridge.status_signal.emit("READY"))
    QTimer.singleShot(6500, lambda: bridge.folder_signal.emit("C:/Users/Abbas/Projects/robotics"))

    sys.exit(app.exec())