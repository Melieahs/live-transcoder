from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QProgressBar, QTextEdit, QHBoxLayout, QPushButton


class StatusBar(QGroupBox):
    def __init__(self):
        super().__init__("状态")
        layout = QVBoxLayout(self)

        self.status_label = QLabel("未启动")
        self.status_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)


class LogPanel(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setMaximumHeight(150)


class ControlBar(QHBoxLayout):
    def __init__(self, start_slot, stop_slot, save_slot):
        super().__init__()

        self.start_btn = QPushButton("开始")
        self.start_btn.clicked.connect(start_slot)
        self.addWidget(self.start_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(stop_slot)
        self.stop_btn.setEnabled(False)
        self.addWidget(self.stop_btn)

        self.addStretch()

        self.save_btn = QPushButton("保存设置")
        self.save_btn.clicked.connect(save_slot)
        self.addWidget(self.save_btn)
