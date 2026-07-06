from PyQt5.QtWidgets import (
    QWidget, QFormLayout, QVBoxLayout, QLineEdit,
    QPushButton, QFileDialog, QGroupBox, QLabel, QHBoxLayout
)


class PlaybackTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # ---- 远程转码模式：接收回放流 ----
        g1 = QGroupBox("远程转码播放器")
        f1 = QFormLayout(g1)

        h = QHBoxLayout()
        self.stream_player = QLineEdit("mpv")
        self.stream_player.setPlaceholderText("如 mpv, ffplay")
        b1 = QPushButton("...")
        b1.clicked.connect(lambda: self._browse(self.stream_player))
        h.addWidget(self.stream_player, 1)
        h.addWidget(b1)
        f1.addRow("播放器:", h)

        self.stream_extra = QLineEdit(
            "--cache=yes --demuxer-max-bytes=300M --no-cache-pause")
        self.stream_extra.setPlaceholderText("额外参数，留空使用默认")
        f1.addRow("参数:", self.stream_extra)

        layout.addWidget(g1)

        # ---- 本地直播模式：直接播放本地文件 ----
        g2 = QGroupBox("本地解码播放器")
        f2 = QFormLayout(g2)

        h2 = QHBoxLayout()
        self.file_player = QLineEdit("ffplay")
        self.file_player.setPlaceholderText("如 ffplay, mpv")
        b2 = QPushButton("...")
        b2.clicked.connect(lambda: self._browse(self.file_player))
        h2.addWidget(self.file_player, 1)
        h2.addWidget(b2)
        f2.addRow("播放器:", h2)

        self.file_extra = QLineEdit("-autoexit")
        self.file_extra.setPlaceholderText("额外参数")
        f2.addRow("参数:", self.file_extra)

        layout.addWidget(g2)
        layout.addStretch()

    def _browse(self, line_edit):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择播放器", "/usr/bin/", "所有文件 (*)")
        if path:
            line_edit.setText(path)

    # 远程转码 → 回播流
    def get_stream_player(self):
        return self.stream_player.text().strip() or "mpv"

    def get_stream_extra_args(self):
        return self.stream_extra.text().strip()

    def set_stream_player(self, v):
        self.stream_player.setText(v)

    def set_stream_extra_args(self, v):
        self.stream_extra.setText(v)

    # 本地直播
    def get_file_player(self):
        return self.file_player.text().strip() or "ffplay"

    def get_file_extra_args(self):
        return self.file_extra.text().strip()

    def set_file_player(self, v):
        self.file_player.setText(v)

    def set_file_extra_args(self, v):
        self.file_extra.setText(v)

    # 兼容旧方法名（供 main.py 调用）
    get_remote_player = get_stream_player
    get_remote_extra_args = get_stream_extra_args
    get_local_player = get_file_player
    get_local_extra_args = get_file_extra_args
    set_remote_player = set_stream_player
    set_remote_extra_args = set_stream_extra_args
    set_local_player = set_file_player
    set_local_extra_args = set_file_extra_args
