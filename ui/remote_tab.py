from PyQt5.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QSpinBox, QPushButton, QCheckBox, QLabel,
    QHBoxLayout, QComboBox
)
from PyQt5.QtCore import pyqtSignal, Qt

import config


class RemoteTab(QWidget):
    check_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        layout = QFormLayout(self)

        self.remote_enable = QCheckBox("启用远程转码")
        self.remote_enable.setChecked(True)
        layout.addRow(self.remote_enable)

        self.remote_os = QComboBox()
        self.remote_os.addItems(config.REMOTE_OS_OPTIONS)
        self.remote_os.setCurrentText(config.DEFAULT_REMOTE_OS)
        layout.addRow("远程系统:", self.remote_os)

        self.remote_host = QLineEdit(config.DEFAULT_REMOTE_HOST)
        layout.addRow("远程主机:", self.remote_host)

        self.remote_pass = QLineEdit(config.DEFAULT_REMOTE_PASS)
        self.remote_pass.setEchoMode(QLineEdit.Password)
        layout.addRow("远程密码:", self.remote_pass)

        self.ssh_port = QSpinBox()
        self.ssh_port.setRange(1, 65535)
        self.ssh_port.setValue(config.DEFAULT_SSH_PORT)
        layout.addRow("SSH端口:", self.ssh_port)

        self.ffmpeg_env = QLineEdit("")
        self.ffmpeg_env.setPlaceholderText("如 LIBVA_DRIVER_NAME=iHD")
        layout.addRow("远程环境变量:", self.ffmpeg_env)

        self.remote_listen_port = QSpinBox()
        self.remote_listen_port.setRange(1024, 65535)
        self.remote_listen_port.setValue(config.DEFAULT_UDP_PORT_REMOTE)
        layout.addRow("隧道端口:", self.remote_listen_port)

        self.local_play_port = QSpinBox()
        self.local_play_port.setRange(1024, 65535)
        self.local_play_port.setValue(6000)
        layout.addRow("播放端口:", self.local_play_port)

        btn_row = QHBoxLayout()
        self.remote_check_btn = QPushButton("测试远程连接")
        self.remote_check_btn.clicked.connect(self.check_clicked.emit)
        btn_row.addWidget(self.remote_check_btn)

        self.status_indicator = QLabel("  ●")
        self.status_indicator.setToolTip("连接状态")
        btn_row.addWidget(self.status_indicator)
        btn_row.addStretch()
        layout.addRow(btn_row)

        self._set_status("untested")

    def _set_status(self, state):
        colors = {
            "untested": "gray",
            "testing": "#f0ad4e",
            "ok": "#5cb85c",
            "fail": "#d9534f",
        }
        color = colors.get(state, "gray")
        self.status_indicator.setStyleSheet(
            f"color: {color}; font-size: 18px; font-weight: bold;"
        )

    def get_remote_os(self):
        return self.remote_os.currentText()

    def get_host(self):
        return self.remote_host.text()

    def get_pass(self):
        return self.remote_pass.text()

    def get_ssh_port(self):
        return self.ssh_port.value()

    def get_tunnel_port(self):
        return self.remote_listen_port.value()

    def get_play_port(self):
        return self.local_play_port.value()

    def is_enabled(self):
        return self.remote_enable.isChecked()

    def set_remote_os(self, os_name):
        self.remote_os.setCurrentText(os_name)

    def set_host(self, h):
        self.remote_host.setText(h)

    def set_pass(self, p):
        self.remote_pass.setText(p)

    def set_ssh_port(self, p):
        self.ssh_port.setValue(p)

    def get_ffmpeg_env(self):
        return self.ffmpeg_env.text().strip()

    def set_ffmpeg_env(self, v):
        self.ffmpeg_env.setText(v)

    def set_tunnel_port(self, p):
        self.remote_listen_port.setValue(p)

    def set_play_port(self, p):
        self.local_play_port.setValue(p)

    def set_enabled(self, e):
        self.remote_enable.setChecked(e)

    def set_check_btn_state(self, enabled, text):
        self.remote_check_btn.setEnabled(enabled)
        self.remote_check_btn.setText(text)
        if "测试中" in text:
            self._set_status("testing")

    def set_connection_status(self, ok):
        self._set_status("ok" if ok else "fail")
