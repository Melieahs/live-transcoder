from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt


def _make_dark_palette():
    p = QPalette()
    p.setColor(QPalette.Window,          QColor(45, 45, 45))
    p.setColor(QPalette.WindowText,      Qt.white)
    p.setColor(QPalette.Base,            QColor(30, 30, 30))
    p.setColor(QPalette.AlternateBase,   QColor(45, 45, 45))
    p.setColor(QPalette.ToolTipBase,     Qt.white)
    p.setColor(QPalette.ToolTipText,     Qt.white)
    p.setColor(QPalette.Text,            Qt.white)
    p.setColor(QPalette.Button,          QColor(53, 53, 53))
    p.setColor(QPalette.ButtonText,      Qt.white)
    p.setColor(QPalette.BrightText,      Qt.red)
    p.setColor(QPalette.Link,            QColor(66, 133, 244))
    p.setColor(QPalette.Highlight,       QColor(66, 133, 244))
    p.setColor(QPalette.HighlightedText, Qt.black)
    p.setColor(QPalette.Disabled, QPalette.Text,       QColor(127, 127, 127))
    p.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
    return p


DARK_PALETTE = _make_dark_palette()


def apply_dark_theme(app):
    app.setStyle("Fusion")
    app.setPalette(DARK_PALETTE)
    app.setStyleSheet("""
        QToolTip { color: #ffffff; background-color: #353535; border: 1px solid #555; }
        QStatusBar { border-top: 1px solid #555; }
        QGroupBox { border: 1px solid #555; border-radius: 4px; margin-top: 8px; padding-top: 12px; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
        QListWidget::item:selected { background-color: #4285f4; }
        QTreeWidget::item:selected { background-color: #4285f4; }
    """)
