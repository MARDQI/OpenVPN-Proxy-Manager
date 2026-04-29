BG = "#0D0D0D"
BG_PANEL = "#161616"
BG_CARD = "#0F0F0F"
ACCENT = "#3B82F6"
CYAN = "#3B82F6"
PURPLE = "#bb9af7"
GREEN = "#10B981"
YELLOW = "#F59E0B"
RED = "#EF4444"
TEXT = "#FFFFFF"
TEXT_DIM = "#888888"
BORDER = "#222222"

def get_stylesheet() -> str:
    return f'''
    QWidget {{
        background-color: {BG};
        color: {TEXT};
        font-family: "Inter", "Segoe UI", sans-serif;
        font-size: 13px;
    }}
    QPushButton {{
        background-color: {ACCENT};
        color: {TEXT};
        border-radius: 8px;
        padding: 10px 16px;
        border: none;
        font-weight: 600;
        font-size: 14px;
    }}
    QPushButton:hover {{
        background-color: #2563EB;
    }}
    QPushButton:pressed {{
        background-color: #1D4ED8;
    }}
    QPushButton#btn_disconnect {{
        background-color: {RED};
    }}
    QPushButton#btn_disconnect:hover {{
        background-color: #DC2626;
    }}
    QPushButton#btn_secondary {{
        background-color: {BG_PANEL};
        color: {TEXT};
        border: 1px solid {BORDER};
    }}
    QPushButton#btn_secondary:hover {{
        background-color: #222222;
    }}
    QPushButton#btn_icon {{
        background-color: transparent;
        color: {TEXT_DIM};
        padding: 4px;
    }}
    QPushButton#btn_icon:hover {{
        color: {TEXT};
        background-color: #222222;
        border-radius: 4px;
    }}
    QPushButton#btn_circle_plus {{
        background-color: transparent;
        color: {ACCENT};
        font-size: 24px;
        border-radius: 16px;
        padding: 0;
        min-width: 32px;
        min-height: 32px;
    }}
    QPushButton#btn_circle_plus:hover {{
        background-color: #222222;
    }}
    QLineEdit, QComboBox, QSpinBox {{
        background-color: {BG_CARD};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 10px;
        font-size: 13px;
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
        border-color: {ACCENT};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 30px;
    }}
    QTextEdit {{
        background-color: {BG_PANEL};
        color: #9CA3AF;
        font-family: "Roboto Mono", "Fira Code", monospace;
        font-size: 12px;
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 12px;
    }}
    QLabel {{
        background-color: transparent;
        font-size: 14px;
    }}
    QLabel#label_title {{
        font-size: 20px;
        font-weight: bold;
    }}
    QLabel#label_dim {{
        color: {TEXT_DIM};
        font-size: 12px;
    }}
    QScrollBar:vertical, QScrollBar:horizontal {{
        background: {BG};
        width: 8px;
        height: 8px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
        background: #333333;
        border-radius: 4px;
        min-height: 20px;
        min-width: 20px;
    }}
    QScrollBar::handle:hover {{
        background: #444444;
    }}
    QScrollBar::add-line, QScrollBar::sub-line {{
        height: 0px;
        width: 0px;
    }}
    QFrame#card {{
        background-color: {BG_PANEL};
        border-radius: 12px;
        padding: 16px;
    }}
    QListWidget {{
        background-color: transparent;
        border: none;
        outline: none;
    }}
    QListWidget::item {{
        background-color: {BG_PANEL};
        border-radius: 8px;
        margin-bottom: 8px;
    }}
    QListWidget::item:selected {{
        background-color: #1A1A1A;
        border: 1px solid {ACCENT};
    }}
    QListWidget::item:hover {{
        background-color: #222222;
    }}
    QCheckBox#switch::indicator {{
        width: 36px;
        height: 20px;
        border-radius: 10px;
        background-color: #333333;
        border: 1px solid #444;
    }}
    QCheckBox#switch::indicator:checked {{
        background-color: {ACCENT};
        border-color: {ACCENT};
    }}
    '''
