from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QProgressBar, QTextEdit, QHBoxLayout, QPushButton, QMenu
from PyQt5.QtCore import Qt


class StatusBar(QGroupBox):
    def __init__(self):
        super().__init__("状态")
        layout = QVBoxLayout(self)

        self.status_label = QLabel("未启动")
        self.status_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.status_label)

        self.detail_label = QLabel("")
        self.detail_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self.detail_label)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

    def set_detail(self, text):
        self.detail_label.setText(text)


class LogPanel(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setMaximumHeight(150)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_log_menu)

    def _show_log_menu(self, pos):
        menu = QMenu(self)
        clear_action = menu.addAction("清除日志")
        copy_action = menu.addAction("复制全部")
        action = menu.exec_(self.mapToGlobal(pos))
        if action == clear_action:
            self.clear()
        elif action == copy_action:
            from PyQt5.QtWidgets import QApplication
            QApplication.clipboard().setText(self.toPlainText())


class ControlBar(QHBoxLayout):
    def __init__(self, toggle_slot, save_slot, reset_slot=None):
        super().__init__()

        self.toggle_btn = QPushButton("开始")
        self.toggle_btn.clicked.connect(toggle_slot)
        self.toggle_btn.setToolTip("开始/停止播放 (Space)")
        self.toggle_btn.setMinimumWidth(80)
        self.addWidget(self.toggle_btn)

        self.addStretch()

        self.save_btn = QPushButton("保存设置")
        self.save_btn.clicked.connect(save_slot)
        self.save_btn.setToolTip("保存当前设置 (Ctrl+S)")
        self.addWidget(self.save_btn)

        self.reset_btn = QPushButton("恢复默认")
        self.reset_btn.setToolTip("恢复所有设置为默认值")
        if reset_slot:
            self.reset_btn.clicked.connect(reset_slot)
            self.addWidget(self.reset_btn)

    def set_streaming(self, active):
        self.toggle_btn.setText("停止" if active else "开始")
