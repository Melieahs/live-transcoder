from PyQt5.QtWidgets import (
    QWidget, QFormLayout, QComboBox, QLineEdit, QPushButton,
    QHBoxLayout, QLabel, QFileDialog
)
from PyQt5.QtCore import pyqtSignal

import config
import streamer


class InputTab(QWidget):
    file_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        layout = QFormLayout(self)

        self.input_mode = QComboBox()
        self.input_mode.addItems(config.INPUT_MODES)
        layout.addRow("输入模式:", self.input_mode)

        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText("选择视频文件...")
        self.input_browse = QPushButton("浏览...")
        self.input_browse.clicked.connect(self._browse)
        h = QHBoxLayout()
        h.addWidget(self.input_path, 1)
        h.addWidget(self.input_browse)
        layout.addRow("文件路径:", h)

        self.file_info = QLabel("")
        self.file_info.setStyleSheet("color: gray;")
        layout.addRow(self.file_info)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.mkv *.avi *.mov *.webm *.ts);;所有文件 (*)"
        )
        if path:
            self.input_path.setText(path)
            self.file_selected.emit(path)

    def show_file_info(self, path):
        info = streamer.get_media_info(path)
        if info["duration"]:
            self.file_info.setText(
                f"{info['width']}x{info['height']}  {info['fps']}fps  "
                f"{info['codec']}  时长 {info['duration']}s"
            )
        else:
            self.file_info.setText("")

    def get_mode(self):
        return self.input_mode.currentText()

    def get_path(self):
        return self.input_path.text()

    def set_mode(self, mode):
        self.input_mode.setCurrentText(mode)

    def set_path(self, path):
        self.input_path.setText(path)
