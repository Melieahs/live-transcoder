import os
import threading

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QFileDialog, QListWidget, QSplitter,
    QListWidgetItem, QAbstractItemView, QMenu
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
    except (PermissionError, FileNotFoundError, OSError):
        pass
    return files


def _scan_subdirs(directory):
    dirs = []
    try:
        for f in sorted(os.listdir(directory)):
            full = os.path.join(directory, f)
            if os.path.isdir(full):
                dirs.append(full)
    except (PermissionError, FileNotFoundError, OSError):
        pass
    return dirs


class InputTab(QWidget):
    file_selected = pyqtSignal(str)

    def __init__(self, right_panel):
        super().__init__()
        self.right_panel = right_panel
        self._dir_cache = {}

        self.setAcceptDrops(True)

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
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        splitter.addWidget(self.list_widget)

        splitter.addWidget(self.right_panel)

        splitter.setSizes([280, 220])
        layout.addWidget(splitter, 1)

        self._current_dir = os.path.expanduser("~/Videos")
        self.dir_path.setText(self._current_dir)
        self._apply_mode_visibility()
        self._refresh_list()

    def _apply_mode_visibility(self):
        mode = self.input_mode.currentText()
        is_folder = mode == "文件夹"
        self.dir_label.setVisible(is_folder)
        self.dir_path.setVisible(is_folder)
        self.dir_up.setVisible(is_folder)
        self.dir_browse.setVisible(is_folder)
        self.file_browse.setVisible(not is_folder)

    def _on_mode_changed(self, mode):
        self._apply_mode_visibility()
        self._refresh_list()

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.mkv *.avi *.mov *.webm *.ts *.flv *.wmv *.m4v);;所有文件 (*)"
        )
        if path:
            self._current_dir = os.path.dirname(path)
            self.dir_path.setText(self._current_dir)
            self._refresh_list()
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item.data(Qt.UserRole) == path:
                    self.list_widget.setCurrentItem(item)
                    break
            self.right_panel.add_dir_history(self._current_dir)
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
            self.right_panel.add_dir_history(path)

    def _refresh_list(self):
        self.list_widget.clear()
        mode = self.input_mode.currentText()

        if mode == "文件夹":
            dirs = _scan_subdirs_cached(self, self._current_dir)
            for d in dirs:
                name = os.path.basename(d)
                item = QListWidgetItem("📁 " + name)
                item.setData(Qt.UserRole, d)
                item.setData(Qt.UserRole + 1, "dir")
                self.list_widget.addItem(item)

        files = _scan_videos_cached(self, self._current_dir)
        for f in files:
            name = os.path.basename(f)
            item = QListWidgetItem("🎬 " + name)
            item.setData(Qt.UserRole, f)
            item.setData(Qt.UserRole + 1, "file")
            self.list_widget.addItem(item)

    def _on_item_clicked(self, item):
        path = item.data(Qt.UserRole)
        kind = item.data(Qt.UserRole + 1)
        if kind == "file":
            self._show_file_info_async(path)
        else:
            self.right_panel.set_file_info(os.path.basename(path), "文件夹 - 双击进入")

    def _on_item_double_clicked(self, item):
        path = item.data(Qt.UserRole)
        kind = item.data(Qt.UserRole + 1)
        mode = self.input_mode.currentText()
        if kind == "dir" and mode == "文件夹":
            self._current_dir = path
            self.dir_path.setText(path)
            self.right_panel.add_dir_history(path)
            self._refresh_list()
        elif kind == "file":
            self.list_widget.setCurrentItem(item)
            self.file_selected.emit(path)

    def _show_file_info_async(self, path):
        name = os.path.basename(path)
        self.right_panel.set_loading(name)

        def worker():
            info = streamer.get_media_info(path)
            text = ""
            if info.get("duration"):
                text = (
                    f"{info['width']}x{info['height']}  "
                    f"{info['fps']}fps  "
                    f"{info['codec']}  时长 {info['duration']}s"
                )
            else:
                text = "无法读取媒体信息"
            self.right_panel.set_file_info(name, text)

        threading.Thread(target=worker, daemon=True).start()

    def show_file_info(self, path):
        self._show_file_info_async(path)

    def _show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item:
            return
        path = item.data(Qt.UserRole)
        kind = item.data(Qt.UserRole + 1)
        menu = QMenu(self)
        if kind == "file":
            play_action = menu.addAction("▶ 播放")
            queue_action = menu.addAction("+ 添加到队列")
        if kind == "dir":
            open_action = menu.addAction("进入文件夹")
        menu.addSeparator()
        queue_all_action = menu.addAction("加入全部到队列")

        action = menu.exec_(self.list_widget.mapToGlobal(pos))

        if kind == "file" and action == play_action:
            self.file_selected.emit(path)
        elif kind == "file" and action == queue_action:
            self.right_panel.add_to_queue(path)
        elif kind == "dir" and action == open_action:
            self._current_dir = path
            self.dir_path.setText(path)
            self.right_panel.add_dir_history(path)
            self._refresh_list()
        elif action == queue_all_action:
            for i in range(self.list_widget.count()):
                it = self.list_widget.item(i)
                if it.data(Qt.UserRole + 1) == "file":
                    self.right_panel.add_to_queue(it.data(Qt.UserRole))

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
                    self._show_file_info_async(path)
                    break

    def _invalidate_dir_cache(self, directory=None):
        if directory is None:
            self._dir_cache.clear()
        else:
            self._dir_cache.pop(directory, None)
            self._dir_cache.pop(directory + "::dirs", None)

    def navigate_to(self, path):
        if os.path.isdir(path):
            self._current_dir = path
            self.dir_path.setText(path)
            self._invalidate_dir_cache(path)
            self._refresh_list()
            self.right_panel.add_dir_history(path)

    # --- 拖拽支持 ---
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isdir(path):
                self._current_dir = path
                self.dir_path.setText(path)
                self._invalidate_dir_cache(path)
                self._refresh_list()
                self.right_panel.add_dir_history(path)
            elif os.path.splitext(path)[1].lower() in VIDEO_EXTENSIONS:
                self.right_panel.add_to_queue(path)


# --- 目录扫描缓存 ---
def _scan_videos_cached(tab, directory):
    try:
        mtime = os.path.getmtime(directory)
    except OSError:
        return _scan_videos(directory)
    cache = tab._dir_cache
    if directory in cache:
        cached_mtime, cached_files = cache[directory]
        if cached_mtime == mtime:
            return cached_files
    files = _scan_videos(directory)
    cache[directory] = (mtime, files)
    return files


def _scan_subdirs_cached(tab, directory):
    try:
        mtime = os.path.getmtime(directory)
    except OSError:
        return _scan_subdirs(directory)
    cache = tab._dir_cache
    key = directory + "::dirs"
    if key in cache:
        cached_mtime, cached_dirs = cache[key]
        if cached_mtime == mtime:
            return cached_dirs
    dirs = _scan_subdirs(directory)
    cache[key] = (mtime, dirs)
    return dirs
