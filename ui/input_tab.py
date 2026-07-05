import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QFileDialog, QListWidget, QSplitter,
    QListWidgetItem, QFrame, QTreeWidget, QTreeWidgetItem,
    QAbstractItemView
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


def _scan_subdirs(directory):
    dirs = []
    try:
        for f in sorted(os.listdir(directory)):
            full = os.path.join(directory, f)
            if os.path.isdir(full):
                dirs.append(full)
    except:
        pass
    return dirs


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

        self.dir_label = QLabel("路径:")
        self.dir_path = QLineEdit()
        self.dir_path.setPlaceholderText("视频目录...")
        self.dir_path.setReadOnly(True)
        self.dir_browse = QPushButton("浏览...")
        self.dir_browse.clicked.connect(self._browse_dir)
        self.dir_up = QPushButton("⬆")
        self.dir_up.setToolTip("上级目录")
        self.dir_up.clicked.connect(self._go_up)
        self.file_browse = QPushButton("选择文件...")
        self.file_browse.clicked.connect(self._browse_file)
        top_bar.addWidget(self.dir_label)
        top_bar.addWidget(self.dir_path, 1)
        top_bar.addWidget(self.dir_up)
        top_bar.addWidget(self.dir_browse)
        top_bar.addWidget(self.file_browse)

        layout.addLayout(top_bar)

        splitter = QSplitter(Qt.Horizontal)

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        splitter.addWidget(self.list_widget)

        info_frame = QFrame()
        info_layout = QVBoxLayout(info_frame)
        self.item_name = QLabel("")
        self.item_name.setStyleSheet("font-weight: bold; font-size: 14px;")
        info_layout.addWidget(self.item_name)
        self.item_info = QLabel("")
        self.item_info.setStyleSheet("color: gray;")
        info_layout.addWidget(self.item_info)
        info_layout.addStretch()
        splitter.addWidget(info_frame)

        splitter.setSizes([300, 200])
        layout.addWidget(splitter, 1)

        self._current_dir = os.path.expanduser("~/Videos")
        self.dir_path.setText(self._current_dir)
        self._refresh_list()

    def _on_mode_changed(self, mode):
        is_folder = mode == "文件夹"
        self.dir_label.setVisible(is_folder)
        self.dir_path.setVisible(is_folder)
        self.dir_up.setVisible(is_folder)
        self.dir_browse.setVisible(is_folder)
        self.file_browse.setVisible(not is_folder)
        self.list_widget.setVisible(True)
        self._refresh_list()

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.mkv *.avi *.mov *.webm *.ts);;所有文件 (*)"
        )
        if path:
            self._current_dir = os.path.dirname(path)
            self.dir_path.setText(self._current_dir)
            self._refresh_list()
            self.file_selected.emit(path)

    def _go_up(self):
        parent = os.path.dirname(self._current_dir)
        if parent and parent != self._current_dir:
            self._current_dir = parent
            self.dir_path.setText(parent)
            self._refresh_list()

    def _browse_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择目录", self._current_dir)
        if path:
            self._current_dir = path
            self.dir_path.setText(path)
            self._refresh_list()

    def _refresh_list(self):
        self.list_widget.clear()
        mode = self.input_mode.currentText()

        if mode == "文件夹":
            for d in _scan_subdirs(self._current_dir):
                name = os.path.basename(d)
                item = QListWidgetItem("📁 " + name)
                item.setData(Qt.UserRole, d)
                item.setData(Qt.UserRole + 1, "dir")
                self.list_widget.addItem(item)

        for f in _scan_videos(self._current_dir):
            name = os.path.basename(f)
            item = QListWidgetItem("🎬 " + name)
            item.setData(Qt.UserRole, f)
            item.setData(Qt.UserRole + 1, "file")
            self.list_widget.addItem(item)

    def _on_item_clicked(self, item):
        path = item.data(Qt.UserRole)
        kind = item.data(Qt.UserRole + 1)
        if kind == "file":
            self._show_file_info(path)
        else:
            self.item_name.setText(os.path.basename(path))
            self.item_info.setText("文件夹 - 双击进入")

    def _on_item_double_clicked(self, item):
        path = item.data(Qt.UserRole)
        kind = item.data(Qt.UserRole + 1)
        mode = self.input_mode.currentText()
        if kind == "dir" and mode == "文件夹":
            self._current_dir = path
            self.dir_path.setText(path)
            self._refresh_list()
        elif kind == "file":
            self.file_selected.emit(path)

    def _show_file_info(self, path):
        name = os.path.basename(path)
        self.item_name.setText(name)
        info = streamer.get_media_info(path)
        if info["duration"]:
            self.item_info.setText(
                f"{info['width']}x{info['height']}  {info['fps']}fps  "
                f"{info['codec']}  时长 {info['duration']}s"
            )
        else:
            self.item_info.setText("")

    def show_file_info(self, path):
        self._show_file_info(path)

    def get_mode(self):
        return self.input_mode.currentText()

    def get_path(self):
        items = self.list_widget.selectedItems()
        if items:
            path = items[0].data(Qt.UserRole)
            kind = items[0].data(Qt.UserRole + 1)
            if kind == "file":
                return path
        return ""

    def set_mode(self, mode):
        self.input_mode.setCurrentText(mode)

    def set_path(self, path):
        if path and os.path.exists(path):
            self._current_dir = os.path.dirname(path)
            self.dir_path.setText(self._current_dir)
            self._refresh_list()
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item.data(Qt.UserRole) == path:
                    self.list_widget.setCurrentItem(item)
                    self._show_file_info(path)
                    break
