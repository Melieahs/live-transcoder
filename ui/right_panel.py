import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QHBoxLayout, QFrame
)
from PyQt5.QtCore import pyqtSignal, Qt


class RightPanel(QWidget):
    file_selected = pyqtSignal(str)
    dir_selected = pyqtSignal(str)
    queue_updated = pyqtSignal(list)

    def __init__(self):
        super().__init__()

        self._play_history = []
        self._dir_history = []
        self._play_queue = []
        self._queue_item_paths = set()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # ---- 文件信息 ----
        info_tab = QFrame()
        info_layout = QVBoxLayout(info_tab)
        self.item_name = QLabel("")
        self.item_name.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.item_name.setWordWrap(True)
        info_layout.addWidget(self.item_name)
        self.item_info = QLabel("")
        self.item_info.setStyleSheet("color: gray;")
        self.item_info.setWordWrap(True)
        info_layout.addWidget(self.item_info)
        info_layout.addStretch()
        self.tabs.addTab(info_tab, "文件信息")

        # ---- 播放历史 ----
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        his_top = QHBoxLayout()
        his_top.addWidget(QLabel("播放历史"))
        his_top.addStretch()
        self.clear_history_btn = QPushButton("清空")
        self.clear_history_btn.clicked.connect(self._clear_history)
        his_top.addWidget(self.clear_history_btn)
        history_layout.addLayout(his_top)

        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self._on_history_clicked)
        self.history_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self._history_menu)
        history_layout.addWidget(self.history_list)
        self.tabs.addTab(history_tab, "播放历史")

        # ---- 文件夹历史 ----
        dir_tab = QWidget()
        dir_layout = QVBoxLayout(dir_tab)
        dir_top = QHBoxLayout()
        dir_top.addWidget(QLabel("文件夹历史"))
        dir_top.addStretch()
        self.clear_dir_btn = QPushButton("清空")
        self.clear_dir_btn.clicked.connect(self._clear_dir_history)
        dir_top.addWidget(self.clear_dir_btn)
        dir_layout.addLayout(dir_top)

        self.dir_list = QListWidget()
        self.dir_list.itemDoubleClicked.connect(self._on_dir_clicked)
        self.dir_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.dir_list.customContextMenuRequested.connect(self._dir_menu)
        dir_layout.addWidget(self.dir_list)
        self.tabs.addTab(dir_tab, "文件夹历史")

        # ---- 播放队列 ----
        queue_tab = QWidget()
        queue_layout = QVBoxLayout(queue_tab)
        q_top = QHBoxLayout()
        q_top.addWidget(QLabel("播放队列"))
        q_top.addStretch()
        self.clear_queue_btn = QPushButton("清空")
        self.clear_queue_btn.clicked.connect(self.clear_queue)
        q_top.addWidget(self.clear_queue_btn)
        queue_layout.addLayout(q_top)

        self.queue_list = QListWidget()
        self.queue_list.setDragDropMode(self.queue_list.InternalMove)
        self.queue_list.model().rowsMoved.connect(self._on_queue_reorder)
        self.queue_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.queue_list.customContextMenuRequested.connect(self._queue_menu)
        queue_layout.addWidget(self.queue_list)
        self.tabs.addTab(queue_tab, "播放队列")

    # ---------- 媒体信息 ----------
    def set_file_info(self, name, info_text):
        self.item_name.setText(name)
        self.item_info.setText(info_text)

    def set_loading(self, name):
        self.item_name.setText(name)
        self.item_info.setText("加载中...")

    # ---------- 播放历史 ----------
    def add_history(self, path):
        if path in self._play_history:
            self._play_history.remove(path)
        self._play_history.insert(0, path)
        if len(self._play_history) > 50:
            self._play_history = self._play_history[:50]
        self._refresh_history_list()

    def _refresh_history_list(self):
        self.history_list.clear()
        for p in self._play_history:
            item = QListWidgetItem(os.path.basename(p))
            item.setData(Qt.UserRole, p)
            item.setToolTip(p)
            self.history_list.addItem(item)

    def _on_history_clicked(self, item):
        path = item.data(Qt.UserRole)
        self.file_selected.emit(path)

    def _history_menu(self, pos):
        item = self.history_list.itemAt(pos)
        if not item:
            return
        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        play_action = menu.addAction("播放")
        queue_action = menu.addAction("加入队列")
        action = menu.exec_(self.history_list.mapToGlobal(pos))
        path = item.data(Qt.UserRole)
        if action == play_action:
            self.file_selected.emit(path)
        elif action == queue_action:
            self._add_to_queue(path)

    def _clear_history(self):
        self._play_history.clear()
        self.history_list.clear()

    # ---------- 文件夹历史 ----------
    def add_dir_history(self, path):
        if path in self._dir_history:
            self._dir_history.remove(path)
        self._dir_history.insert(0, path)
        if len(self._dir_history) > 20:
            self._dir_history = self._dir_history[:20]
        self._refresh_dir_list()

    def _refresh_dir_list(self):
        self.dir_list.clear()
        for p in self._dir_history:
            item = QListWidgetItem(os.path.basename(p) or p)
            item.setData(Qt.UserRole, p)
            item.setToolTip(p)
            self.dir_list.addItem(item)

    def _on_dir_clicked(self, item):
        path = item.data(Qt.UserRole)
        self.dir_selected.emit(path)
        self.add_dir_history(path)

    def _dir_menu(self, pos):
        item = self.dir_list.itemAt(pos)
        if not item:
            return
        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        open_action = menu.addAction("打开")
        action = menu.exec_(self.dir_list.mapToGlobal(pos))
        if action == open_action:
            path = item.data(Qt.UserRole)
            self.dir_selected.emit(path)

    def _clear_dir_history(self):
        self._dir_history.clear()
        self.dir_list.clear()

    # ---------- 播放队列 ----------
    def _add_to_queue(self, path):
        if path in self._queue_item_paths:
            return
        self._queue_item_paths.add(path)
        self._play_queue.append(path)
        qi = QListWidgetItem(os.path.basename(path))
        qi.setData(Qt.UserRole, path)
        qi.setToolTip(path)
        self.queue_list.addItem(qi)
        self.queue_updated.emit(list(self._play_queue))

    def pop_queue(self):
        if not self._play_queue:
            return None
        path = self._play_queue.pop(0)
        self._queue_item_paths.discard(path)
        if self.queue_list.count() > 0:
            self.queue_list.takeItem(0)
        self.queue_updated.emit(list(self._play_queue))
        return path

    def clear_queue(self):
        self._play_queue.clear()
        self._queue_item_paths.clear()
        self.queue_list.clear()
        self.queue_updated.emit([])

    def has_queue(self):
        return len(self._play_queue) > 0

    def add_to_queue(self, path):
        self._add_to_queue(path)

    def dump_state(self):
        return {
            "play_history": list(self._play_history),
            "dir_history": list(self._dir_history),
            "play_queue": list(self._play_queue),
        }

    def restore_state(self, state):
        if state.get("play_history"):
            for p in state["play_history"]:
                if p not in self._play_history:
                    self._play_history.append(p)
            self._play_history = self._play_history[:50]
            self._refresh_history_list()
        if state.get("dir_history"):
            for p in state["dir_history"]:
                if p not in self._dir_history:
                    self._dir_history.append(p)
            self._dir_history = self._dir_history[:20]
            self._refresh_dir_list()
        if state.get("play_queue"):
            for p in state["play_queue"]:
                self._add_to_queue(p)

    def _on_queue_reorder(self):
        new_order = []
        for i in range(self.queue_list.count()):
            item = self.queue_list.item(i)
            p = item.data(Qt.UserRole)
            if p:
                new_order.append(p)
        self._play_queue = new_order

    def _queue_menu(self, pos):
        item = self.queue_list.itemAt(pos)
        if not item:
            return
        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        remove_action = menu.addAction("移除")
        clear_action = menu.addAction("清空队列")
        action = menu.exec_(self.queue_list.mapToGlobal(pos))
        if action == remove_action:
            row = self.queue_list.row(item)
            self.queue_list.takeItem(row)
            if row < len(self._play_queue):
                path = self._play_queue.pop(row)
                self._queue_item_paths.discard(path)
            self.queue_updated.emit(list(self._play_queue))
        elif action == clear_action:
            self.clear_queue()
