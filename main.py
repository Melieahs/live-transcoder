import sys
import os
import json
import re
import threading
import time

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QGroupBox, QLabel, QLineEdit, QComboBox, QSpinBox,
    QPushButton, QCheckBox, QTextEdit, QFileDialog, QMessageBox,
    QTabWidget, QSlider, QProgressBar, QFrame
)
from PyQt5.QtCore import Qt, QTimer, QMetaObject, pyqtSignal, Q_ARG, QObject


class LogSignals(QObject):
    log_line = pyqtSignal(str)
    status_msg = pyqtSignal(str)
    error_msg = pyqtSignal(str)
    remote_result = pyqtSignal(bool)
    stream_ended = pyqtSignal()

    def __init__(self):
        super().__init__()


import config
import streamer
import remote


SETTINGS_FILE = os.path.expanduser("~/.live_transcoder_settings.json")


class LiveTranscoderWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live Transcoder - 实时远程转码播放")
        self.setMinimumSize(760, 700)

        self.sender_proc = streamer.StreamProcess()
        self.play_proc = streamer.StreamProcess()
        self.remote_proc = None
        self.is_streaming = False

        self.signals = LogSignals()
        self.signals.log_line.connect(self._append_log)
        self.signals.status_msg.connect(self._set_status)
        self.signals.error_msg.connect(self._show_error_dialog)
        self.signals.remote_result.connect(self._on_remote_check_result)
        self.signals.stream_ended.connect(self._on_stream_end)

        self._build_ui()
        self._load_settings()
        self._log("就绪")

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        tabs = QTabWidget()
        main_layout.addWidget(tabs)

        tabs.addTab(self._build_input_tab(), "输入源")
        tabs.addTab(self._build_transcode_tab(), "转码设置")
        tabs.addTab(self._build_remote_tab(), "远程主机")

        self._build_status_bar(main_layout)
        self._build_log(main_layout)
        self._build_control_bar(main_layout)

    def _build_input_tab(self):
        w = QWidget()
        layout = QFormLayout(w)

        self.input_mode = QComboBox()
        self.input_mode.addItems(config.INPUT_MODES)
        self.input_mode.currentTextChanged.connect(self._on_input_mode_changed)
        layout.addRow("输入模式:", self.input_mode)

        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText("选择视频文件...")
        self.input_browse = QPushButton("浏览...")
        self.input_browse.clicked.connect(self._browse_input)
        h = QHBoxLayout()
        h.addWidget(self.input_path, 1)
        h.addWidget(self.input_browse)
        layout.addRow("文件路径:", h)

        self.file_info = QLabel("")
        self.file_info.setStyleSheet("color: gray;")
        layout.addRow(self.file_info)

        return w

    def _build_transcode_tab(self):
        w = QWidget()
        layout = QFormLayout(w)

        self.encoder_combo = QComboBox()
        for opt in config.ENCODER_OPTIONS:
            self.encoder_combo.addItem(opt["label"], opt)
        layout.addRow("编码器:", self.encoder_combo)

        self.quality_combo = QComboBox()
        self.quality_combo.addItems(config.TRANSCODE_QUALITY)
        self.quality_combo.setCurrentText("low")
        layout.addRow("画质:", self.quality_combo)

        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(config.RESOLUTIONS)
        layout.addRow("分辨率:", self.resolution_combo)

        self.framerate_combo = QComboBox()
        self.framerate_combo.addItems(config.FRAMERATES)
        layout.addRow("帧率:", self.framerate_combo)

        self.bitrate_input = QLineEdit()
        self.bitrate_input.setPlaceholderText("如 5M 或留空使用 CRF")
        layout.addRow("码率(选填):", self.bitrate_input)

        return w

    def _build_remote_tab(self):
        w = QWidget()
        layout = QFormLayout(w)

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
        self.remote_check_btn.clicked.connect(self._check_remote)
        layout.addRow(self.remote_check_btn)

        return w

    def _build_status_bar(self, parent):
        gb = QGroupBox("状态")
        layout = QVBoxLayout(gb)

        self.status_label = QLabel("未启动")
        self.status_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        parent.addWidget(gb)

    def _build_log(self, parent):
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(150)
        parent.addWidget(self.log_output)

    def _build_control_bar(self, parent):
        h = QHBoxLayout()

        self.start_btn = QPushButton("开始")
        self.start_btn.clicked.connect(self._toggle_stream)
        h.addWidget(self.start_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self._stop_all)
        self.stop_btn.setEnabled(False)
        h.addWidget(self.stop_btn)

        h.addStretch()

        self.save_btn = QPushButton("保存设置")
        self.save_btn.clicked.connect(self._save_settings)
        h.addWidget(self.save_btn)

        parent.addLayout(h)

    def _on_input_mode_changed(self, mode):
        is_file = mode == "文件"
        self.input_path.setEnabled(is_file)
        self.input_browse.setEnabled(is_file)

    def _browse_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.mkv *.avi *.mov *.webm *.ts);;所有文件 (*)"
        )
        if path:
            self.input_path.setText(path)
            self._show_file_info(path)

    def _show_file_info(self, path):
        info = streamer.get_media_info(path)
        if info["duration"]:
            self.file_info.setText(
                f"{info['width']}x{info['height']}  {info['fps']}fps  "
                f"{info['codec']}  时长 {info['duration']}s"
            )
        else:
            self.file_info.setText("")

    def _check_remote(self):
        host = self.remote_host.text()
        password = self.remote_pass.text()

        if not remote.check_sshpass():
            QMessageBox.critical(self, "错误", "本地未安装 sshpass\n请运行: sudo pacman -S sshpass")
            return

        self._log(f"测试连接 {host} ...")
        self.remote_check_btn.setEnabled(False)
        self.remote_check_btn.setText("测试中...")

        def do_check():
            ok = remote.ensure_remote_ffmpeg(host, password)
            self.signals.remote_result.emit(ok)

        threading.Thread(target=do_check, daemon=True).start()

    def _on_remote_check_result(self, ok):
        self.remote_check_btn.setEnabled(True)
        self.remote_check_btn.setText("测试远程连接")
        if ok:
            self._log("远程连接成功，ffmpeg 可用")
            QMessageBox.information(self, "成功", "远程主机连接正常，ffmpeg 可用")
        else:
            self._log("远程连接失败，请检查主机地址/密码/ffmpeg")
            QMessageBox.critical(self, "失败", "无法连接远程主机或 ffmpeg 未安装")

    def _build_transcode_args(self):
        encoder_data = self.encoder_combo.currentData()
        encoder = encoder_data["enc"] if encoder_data else "libx264"
        quality = self.quality_combo.currentText()
        resolution = self.resolution_combo.currentText()
        framerate = self.framerate_combo.currentText()
        bitrate = self.bitrate_input.text().strip()
        return streamer.build_transcode_args(encoder, quality, resolution, framerate, bitrate)

    def _toggle_stream(self):
        if self.is_streaming:
            self._stop_all()
            return
        self._start_stream()

    def _start_stream(self):
        mode = self.input_mode.currentText()
        if mode == "文件" and not self.input_path.text():
            QMessageBox.warning(self, "提示", "请选择输入文件")
            return

        if not streamer.check_ffmpeg():
            QMessageBox.critical(self, "错误", "未找到 ffmpeg")
            return

        remote_enabled = self.remote_enable.isChecked()
        if remote_enabled and not remote.check_sshpass():
            QMessageBox.critical(self, "错误", "未安装 sshpass\n请运行: sudo pacman -S sshpass")
            return

        self.is_streaming = True
        self.start_btn.setText("停止")
        self.stop_btn.setEnabled(True)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.status_label.setText("启动中...")

        threading.Thread(target=self._stream_thread, args=(remote_enabled,), daemon=True).start()

    def _stream_thread(self, remote_enabled):
        try:
            tunnel_port = self.remote_listen_port.value()
            play_port = self.local_play_port.value()

            if remote_enabled:
                host = self.remote_host.text()
                password = self.remote_pass.text()
                transcode_args = self._build_transcode_args()

                self._log("清理远程残留进程...")
                remote.stop_remote_processes(host, password)
                time.sleep(1)

                target_ip = remote.get_remote_host_ip(host)
                local_ip = "192.168.1.5"

                self._log(f"启动本地推流 (监听 {tunnel_port})...")
                sender_cmd = streamer.build_sender_cmd(
                    self.input_path.text(), self.input_mode.currentText(),
                    tunnel_port, "", ""
                )
                self._log(f"推流命令: {' '.join(sender_cmd)}")
                self.sender_proc.start(sender_cmd)
                time.sleep(1)

                self._log(f"启动本地播放 (监听 {play_port})...")
                play_cmd = streamer.build_play_cmd(play_port)
                self._log(f"播放命令: {' '.join(play_cmd)}")
                self.play_proc.start(play_cmd)
                time.sleep(1)

                self._log(f"启动远程 ffmpeg (直连本机 {local_ip})...")
                self.remote_proc = remote.start_remote_ffmpeg(
                    host, password, tunnel_port, transcode_args, play_port, local_ip
                )
                time.sleep(3)

                self._update_status("正在实时转码播放中...")
                self.sender_proc.proc.wait()
            else:
                self._log("本地模式: 直接播放源文件")
                play_cmd = ["ffplay", "-autoexit", self.input_path.text()]
                self.play_proc.start(play_cmd)
                self._update_status("本地播放中...")
                self.play_proc.proc.wait()

        except Exception as e:
            self.signals.error_msg.emit(str(e))
        finally:
            if self.is_streaming:
                self.signals.stream_ended.emit()

    def _stop_all(self):
        self._log("正在停止所有进程...")
        self.is_streaming = False

        self.sender_proc.stop()
        self.play_proc.stop()

        if self.remote_proc:
            try:
                host = self.remote_host.text()
                password = self.remote_pass.text()
                remote.stop_remote_processes(host, password)
            except:
                pass
            self.remote_proc = None

        self.progress.setVisible(False)
        self.start_btn.setText("开始")
        self.stop_btn.setEnabled(False)
        self.status_label.setText("已停止")

    def _on_stream_end(self):
        self.progress.setVisible(False)
        self.start_btn.setText("开始")
        self.stop_btn.setEnabled(False)
        self.status_label.setText("已结束")
        self._log("流已结束")

    def _show_error_dialog(self, msg):
        self._log(f"错误: {msg}")

    def _on_error(self, msg):
        if threading.current_thread() is threading.main_thread():
            self._show_error_dialog(msg)
        else:
            self.signals.error_msg.emit(msg)

    def _append_log(self, text):
        self.log_output.append(text)

    def _set_status(self, text):
        self.status_label.setText(text)

    def _log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        text = f"[{timestamp}] {msg}"
        if threading.current_thread() is threading.main_thread():
            self._append_log(text)
        else:
            self.signals.log_line.emit(text)

    def _update_status(self, text):
        if threading.current_thread() is threading.main_thread():
            self._set_status(text)
        else:
            self.signals.status_msg.emit(text)

    def _save_settings(self):
        settings = {
            "remote_host": self.remote_host.text(),
            "remote_pass": self.remote_pass.text(),
            "remote_listen_port": self.remote_listen_port.value(),
            "local_play_port": self.local_play_port.value(),
            "encoder_index": self.encoder_combo.currentIndex(),
            "quality": self.quality_combo.currentText(),
            "resolution": self.resolution_combo.currentText(),
            "framerate": self.framerate_combo.currentText(),
            "bitrate": self.bitrate_input.text(),
            "remote_enable": self.remote_enable.isChecked(),
            "input_mode": self.input_mode.currentText(),
            "input_path": self.input_path.text(),
        }
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(settings, f, indent=2)
            self._log("设置已保存")
        except Exception as e:
            self._log(f"保存设置失败: {e}")

    def _load_settings(self):
        if not os.path.exists(SETTINGS_FILE):
            return
        try:
            with open(SETTINGS_FILE) as f:
                settings = json.load(f)
            self.remote_host.setText(settings.get("remote_host", config.DEFAULT_REMOTE_HOST))
            self.remote_pass.setText(settings.get("remote_pass", config.DEFAULT_REMOTE_PASS))
            self.remote_listen_port.setValue(settings.get("remote_listen_port", config.DEFAULT_UDP_PORT_REMOTE))
            self.local_play_port.setValue(settings.get("local_play_port", 6000))
            self.encoder_combo.setCurrentIndex(settings.get("encoder_index", 0))
            self.quality_combo.setCurrentText(settings.get("quality", "low"))
            self.resolution_combo.setCurrentText(settings.get("resolution", "1920x1080"))
            self.framerate_combo.setCurrentText(settings.get("framerate", "原始"))
            self.bitrate_input.setText(settings.get("bitrate", ""))
            self.remote_enable.setChecked(settings.get("remote_enable", True))
            self.input_mode.setCurrentText(settings.get("input_mode", "文件"))
            self.input_path.setText(settings.get("input_path", ""))
            if self.input_path.text():
                self._show_file_info(self.input_path.text())
            self._log("设置已加载")
        except Exception as e:
            self._log(f"加载设置失败: {e}")

    def closeEvent(self, event):
        self._stop_all()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = LiveTranscoderWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
