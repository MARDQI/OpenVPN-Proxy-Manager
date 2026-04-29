BG = "#1a1b2e"
BG_PANEL = "#16213e"
BG_CARD = "#0f3460"
ACCENT = "#e94560"
CYAN = "#7dcfff"
PURPLE = "#bb9af7"
GREEN = "#9ece6a"
YELLOW = "#e0af68"
RED = "#f7768e"
TEXT = "#c0caf5"
TEXT_DIM = "#565f89"
BORDER = "#2a2b3d"

def get_stylesheet() -> str:
    return f'''
    QWidget {{
        background-color: {BG};
        color: {TEXT};
        font-family: "JetBrains Mono", "Fira Code", monospace;
        font-size: 13px;
    }}
    QPushButton {{
        background-color: {BG_CARD};
        color: {TEXT};
        border-radius: 8px;
        padding: 8px 16px;
        border: 1px solid {BORDER};
    }}
    QPushButton:hover {{
        background-color: {PURPLE};
        color: {BG};
    }}
    QPushButton:pressed {{
        background-color: {ACCENT};
    }}
    QPushButton#btn_connect {{
        background-color: {GREEN};
        color: {BG};
        font-weight: bold;
    }}
    QPushButton#btn_connect[state="connected"] {{
        background-color: {RED};
        color: {BG};
    }}
    QPushButton#btn_connect[state="connecting"] {{
        background-color: {YELLOW};
        color: {BG};
    }}
    QLineEdit, QComboBox, QSpinBox {{
        background-color: {BG_PANEL};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 6px;
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
        border-color: {CYAN};
    }}
    QTextEdit {{
        background-color: {BG_PANEL};
        color: {TEXT_DIM};
        font-size: 11px;
        border: 1px solid {BORDER};
        border-radius: 6px;
    }}
    QLabel#label_status {{
        font-size: 12px;
        font-weight: bold;
    }}
    QScrollBar:vertical {{
        background: {BG_PANEL};
        width: 6px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {BG_CARD};
        border-radius: 3px;
        min-height: 20px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QCheckBox {{
        color: {TEXT};
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 3px;
        border: 1px solid {BORDER};
        background: {BG_PANEL};
    }}
    QCheckBox::indicator:checked {{
        background: {CYAN};
    }}
    QFrame#card {{
        background-color: {BG_CARD};
        border-radius: 12px;
        border: 1px solid {BORDER};
    }}
    QListWidget {{
        background-color: {BG_PANEL};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 4px;
    }}
    QListWidget::item {{
        padding: 8px;
        border-radius: 4px;
    }}
    QListWidget::item:selected {{
        background-color: {BG_CARD};
        color: {CYAN};
    }}
    '''