from PyQt5.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QSpinBox, QPushButton, QCheckBox
)
from PyQt5.QtCore import pyqtSignal

import config


class RemoteTab(QWidget):
    check_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        layout = QFormLayout(self)

        self.remote_enable = QCheckBox("启用远程转码")
        self.remote_enable.setChecked(True)
        layout.addRow(self.remote_enable)

        self.remote_host = QLineEdit(config.DEFAULT_REMOTE_HOST)
        layout.addRow("远程主机:", self.remote_host)

        self.remote_pass = QLineEdit(config.DEFAULT_REMOTE_PASS)
        self.remote_pass.setEchoMode(QLineEdit.Password)
        layout.addRow("远程密码:", self.remote_pass)

        self.remote_listen_port = QSpinBox()
        self.remote_listen_port.setRange(1024, 65535)
        self.remote_listen_port.setValue(config.DEFAULT_UDP_PORT_REMOTE)
        layout.addRow("隧道端口:", self.remote_listen_port)

        self.local_play_port = QSpinBox()
        self.local_play_port.setRange(1024, 65535)
        self.local_play_port.setValue(6000)
        layout.addRow("播放端口:", self.local_play_port)

        self.remote_check_btn = QPushButton("测试远程连接")
        self.remote_check_btn.clicked.connect(self.check_clicked.emit)
        layout.addRow(self.remote_check_btn)

    def get_host(self):
        return self.remote_host.text()

    def get_pass(self):
        return self.remote_pass.text()

    def get_tunnel_port(self):
        return self.remote_listen_port.value()

    def get_play_port(self):
        return self.local_play_port.value()

    def is_enabled(self):
        return self.remote_enable.isChecked()

    def set_host(self, h):
        self.remote_host.setText(h)

    def set_pass(self, p):
        self.remote_pass.setText(p)

    def set_tunnel_port(self, p):
        self.remote_listen_port.setValue(p)

    def set_play_port(self, p):
        self.local_play_port.setValue(p)

    def set_enabled(self, e):
        self.remote_enable.setChecked(e)

    def set_check_btn_state(self, enabled, text):
        self.remote_check_btn.setEnabled(enabled)
        self.remote_check_btn.setText(text)
