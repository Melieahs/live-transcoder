import os
import subprocess

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QFileDialog, QListWidget, QSplitter,
    QListWidgetItem, QFrame
)
from PyQt5.QtCore import pyqtSignal, Qt

import config
import streamer


VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.ts', '.flv', '.wmv', '.m4v'}


def _scan_videos(directory):
    files = []
    try:
        for f in sorted(os.listdir(directory)):
            ext = os.path.splitext(f)[1].lower()
            if ext in VIDEO_EXTENSIONS:
                files.append(os.path.join(directory, f))
    except:
        pass
    return files


class InputTab(QWidget):
    file_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        top_bar = QHBoxLayout()
        self.input_mode = QComboBox()
        self.input_mode.addItems(config.INPUT_MODES)
        self.input_mode.currentTextChanged.connect(self._on_mode_changed)
        top_bar.addWidget(QLabel("模式:"))
        top_bar.addWidget(self.input_mode)
        top_bar.addStretch()

        self.dir_label = QLabel("目录:")
        self.dir_path = QLineEdit()
        self.dir_path.setPlaceholderText("视频目录...")
        self.dir_browse = QPushButton("浏览...")
        self.dir_browse.clicked.connect(self._browse_dir)
        top_bar.addWidget(self.dir_label)
        top_bar.addWidget(self.dir_path, 1)
        top_bar.addWidget(self.dir_browse)

        layout.addLayout(top_bar)

        splitter = QSplitter(Qt.Horizontal)

        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self._on_file_clicked)
        self.file_list.itemDoubleClicked.connect(self._on_file_double_clicked)
        splitter.addWidget(self.file_list)

        info_frame = QFrame()
        info_layout = QVBoxLayout(info_frame)
        self.file_name = QLabel("")
        self.file_name.setStyleSheet("font-weight: bold; font-size: 14px;")
        info_layout.addWidget(self.file_name)
        self.file_info = QLabel("")
        self.file_info.setStyleSheet("color: gray;")
        info_layout.addWidget(self.file_info)
        info_layout.addStretch()
        splitter.addWidget(info_frame)

        splitter.setSizes([300, 200])
        layout.addWidget(splitter, 1)

        self._current_dir = os.path.expanduser("~/Videos")
        self.dir_path.setText(self._current_dir)
        self._refresh_file_list()

    def _on_mode_changed(self, mode):
        is_file = mode == "文件"
        self.dir_label.setVisible(is_file)
        self.dir_path.setVisible(is_file)
        self.dir_browse.setVisible(is_file)
        self.file_list.setVisible(is_file)

    def _browse_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择视频目录", self._current_dir)
        if path:
            self._current_dir = path
            self.dir_path.setText(path)
            self._refresh_file_list()

    def _refresh_file_list(self):
        self.file_list.clear()
        files = _scan_videos(self._current_dir)
        for f in files:
            name = os.path.basename(f)
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, f)
            self.file_list.addItem(item)
        if files:
            self.file_list.setCurrentRow(0)
            self._show_file_info(files[0])

    def _on_file_clicked(self, item):
        path = item.data(Qt.UserRole)
        self._show_file_info(path)

    def _on_file_double_clicked(self, item):
        path = item.data(Qt.UserRole)
        self.file_selected.emit(path)

    def _show_file_info(self, path):
        name = os.path.basename(path)
        self.file_name.setText(name)
        info = streamer.get_media_info(path)
        if info["duration"]:
            self.file_info.setText(
                f"{info['width']}x{info['height']}  {info['fps']}fps  "
                f"{info['codec']}  时长 {info['duration']}s"
            )
        else:
            self.file_info.setText("")

    def show_file_info(self, path):
        self._show_file_info(path)

    def get_mode(self):
        return self.input_mode.currentText()

    def get_path(self):
        items = self.file_list.selectedItems()
        if items:
            return items[0].data(Qt.UserRole)
        return ""

    def set_mode(self, mode):
        self.input_mode.setCurrentText(mode)

    def set_path(self, path):
        if path and os.path.exists(path):
            self._current_dir = os.path.dirname(path)
            self.dir_path.setText(self._current_dir)
            self._refresh_file_list()
            for i in range(self.file_list.count()):
                item = self.file_list.item(i)
                if item.data(Qt.UserRole) == path:
                    self.file_list.setCurrentItem(item)
                    self._show_file_info(path)
                    break
