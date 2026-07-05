import sys
import os
import json
import threading
import time
import subprocess

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget
from PyQt5.QtCore import pyqtSignal, QObject

from ui.input_tab import InputTab
from ui.transcode_tab import TranscodeTab
from ui.remote_tab import RemoteTab
from ui.widgets import StatusBar, LogPanel, ControlBar

import config
import streamer
import remote


class LogSignals(QObject):
    log_line = pyqtSignal(str)
    status_msg = pyqtSignal(str)
    error_msg = pyqtSignal(str)
    remote_result = pyqtSignal(bool)
    stream_ended = pyqtSignal()

    def __init__(self):
        super().__init__()


SETTINGS_FILE = os.path.expanduser("~/.live_transcoder_settings.json")


class LiveTranscoderWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live Transcoder - 实时远程转码播放")
        self.setMinimumSize(760, 700)

        self.sender_proc = streamer.StreamProcess()
        self.play_proc = streamer.StreamProcess()
        self.remote_proc = None
        self._pending_path = None
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

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.input_tab = InputTab()
        self.transcode_tab = TranscodeTab()
        self.remote_tab = RemoteTab()

        self.tabs.addTab(self.input_tab, "输入源")
        self.tabs.addTab(self.transcode_tab, "转码设置")
        self.tabs.addTab(self.remote_tab, "远程主机")

        self.input_tab.input_mode.currentTextChanged.connect(self._on_input_mode_changed)
        self.input_tab.file_selected.connect(self._on_file_selected)
        self.remote_tab.check_clicked.connect(self._check_remote)

        self.status_bar = StatusBar()
        main_layout.addWidget(self.status_bar)

        self.log_panel = LogPanel()
        main_layout.addWidget(self.log_panel)

        self.control_bar = ControlBar(self._toggle_stream, self._stop_all, self._save_settings)
        main_layout.addLayout(self.control_bar)

    def _on_input_mode_changed(self, mode):
        pass

    def _on_file_selected(self, path):
        self.input_tab.show_file_info(path)
        self._pending_path = path
        self._start_stream()

    def _check_remote(self):
        host = self.remote_tab.get_host()
        password = self.remote_tab.get_pass()

        if not remote.check_sshpass():
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "错误", "本地未安装 sshpass\n请运行: sudo pacman -S sshpass")
            return

        self._log(f"测试连接 {host} ...")
        self.remote_tab.set_check_btn_state(False, "测试中...")

        def do_check():
            ok = remote.ensure_remote_ffmpeg(host, password)
            self.signals.remote_result.emit(ok)

        threading.Thread(target=do_check, daemon=True).start()

    def _on_remote_check_result(self, ok):
        from PyQt5.QtWidgets import QMessageBox
        self.remote_tab.set_check_btn_state(True, "测试远程连接")
        if ok:
            self._log("远程连接成功，ffmpeg 可用")
            QMessageBox.information(self, "成功", "远程主机连接正常，ffmpeg 可用")
        else:
            self._log("远程连接失败，请检查主机地址/密码/ffmpeg")
            QMessageBox.critical(self, "失败", "无法连接远程主机或 ffmpeg 未安装")

    def _build_transcode_args(self):
        return streamer.build_transcode_args(
            self.transcode_tab.get_encoder(),
            self.transcode_tab.get_quality(),
            self.transcode_tab.get_resolution(),
            self.transcode_tab.get_framerate(),
            self.transcode_tab.get_bitrate(),
        )

    def _toggle_stream(self):
        if self.is_streaming:
            self._stop_all()
            return
        self._start_stream()

    def _start_stream(self):
        from PyQt5.QtWidgets import QMessageBox

        mode = self.input_tab.get_mode()
        file_path = self._pending_path
        if not file_path:
            QMessageBox.warning(self, "提示", "请选择输入文件")
            return

        if not streamer.check_ffmpeg():
            QMessageBox.critical(self, "错误", "未找到 ffmpeg")
            return

        remote_enabled = self.remote_tab.is_enabled()
        if remote_enabled and not remote.check_sshpass():
            QMessageBox.critical(self, "错误", "未安装 sshpass\n请运行: sudo pacman -S sshpass")
            return

        self.is_streaming = True
        self.control_bar.start_btn.setText("停止")
        self.control_bar.stop_btn.setEnabled(True)
        self.status_bar.progress.setVisible(True)
        self.status_bar.progress.setRange(0, 0)
        self.status_bar.status_label.setText("启动中...")

        threading.Thread(target=self._stream_thread, args=(remote_enabled,), daemon=True).start()

    def _stream_thread(self, remote_enabled):
        try:
            tunnel_port = self.remote_tab.get_tunnel_port()
            play_port = self.remote_tab.get_play_port()

            if remote_enabled:
                host = self.remote_tab.get_host()
                password = self.remote_tab.get_pass()
                transcode_args = self._build_transcode_args()

                self._log("清理远程残留进程...")
                remote.stop_remote_processes(host, password)
                time.sleep(1)

                target_ip = remote.get_remote_host_ip(host)
                local_ip = "192.168.1.5"

                self._log(f"启动本地推流 (监听 {tunnel_port})...")
                file_path = self._pending_path
                self._pending_path = None
                sender_cmd = streamer.build_sender_cmd(
                    file_path, self.input_tab.get_mode(),
                    tunnel_port, "", ""
                )
                self._log(f"推流命令: {' '.join(sender_cmd)}")

                is_gvfs = "/gvfs/" in file_path
                if is_gvfs:
                    self._log(f"GVFS路径: {file_path}")
                    self._log("启动外部播放脚本...")
                    script_path = os.path.join(os.path.dirname(__file__), "gvfs_play.py")
                    env = os.environ.copy()
                    env['GVFS_SRC'] = file_path
                    env['GVFS_ENCODER'] = self.transcode_tab.get_encoder()
                    env['GVFS_QUALITY'] = self.transcode_tab.get_quality()
                    env['GVFS_RESOLUTION'] = self.transcode_tab.get_resolution()
                    env['GVFS_FRAMERATE'] = self.transcode_tab.get_framerate()
                    env['GVFS_BITRATE'] = self.transcode_tab.get_bitrate()
                    self._gvfs_proc = subprocess.Popen(
                        ["python3", script_path], env=env,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    self._gvfs_proc.wait()

                else:
                    self.sender_proc.start(sender_cmd)
                    time.sleep(2)

                    self._log(f"启动本地播放 (监听 {play_port})...")
                    play_cmd = streamer.build_play_cmd(play_port)
                    self._log(f"播放命令: {' '.join(play_cmd)}")
                    self.play_proc.start(play_cmd)
                    time.sleep(1)

                    self._log(f"启动远程 ffmpeg (直连本机 {local_ip})...")
                    self.remote_proc = remote.start_remote_ffmpeg(
                        host, password, tunnel_port, transcode_args, play_port, local_ip
                    )
                    time.sleep(5)

                    self._update_status("正在实时转码播放中...")
                    self.sender_proc.proc.wait()
            else:
                self._log("本地模式: 直接播放源文件")
                play_cmd = ["ffplay", "-autoexit", self.input_tab.get_path()]
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

        for attr in ['_sender_proc', '_play_proc']:
            p = getattr(self, attr, None)
            if p:
                p.terminate()
                try: p.wait(timeout=3)
                except: p.kill()
                setattr(self, attr, None)

        if self.remote_proc:
            try:
                host = self.remote_tab.get_host()
                password = self.remote_tab.get_pass()
                remote.stop_remote_processes(host, password)
            except:
                pass
            self.remote_proc = None

        if hasattr(self, '_gvfs_proc') and self._gvfs_proc:
            self._gvfs_proc.terminate()
            try: self._gvfs_proc.wait(timeout=3)
            except: self._gvfs_proc.kill()
            self._gvfs_proc = None

        self.status_bar.progress.setVisible(False)
        self.control_bar.start_btn.setText("开始")
        self.control_bar.stop_btn.setEnabled(False)
        self.status_bar.status_label.setText("已停止")

    def _on_stream_end(self):
        self.status_bar.progress.setVisible(False)
        self.control_bar.start_btn.setText("开始")
        self.control_bar.stop_btn.setEnabled(False)
        self.status_bar.status_label.setText("已结束")
        self._log("流已结束")

    def _show_error_dialog(self, msg):
        self._log(f"错误: {msg}")

    def _on_error(self, msg):
        if threading.current_thread() is threading.main_thread():
            self._show_error_dialog(msg)
        else:
            self.signals.error_msg.emit(msg)

    def _append_log(self, text):
        self.log_panel.append(text)

    def _set_status(self, text):
        self.status_bar.status_label.setText(text)

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
            "remote_host": self.remote_tab.get_host(),
            "remote_pass": self.remote_tab.get_pass(),
            "remote_listen_port": self.remote_tab.get_tunnel_port(),
            "local_play_port": self.remote_tab.get_play_port(),
            "encoder_index": self.transcode_tab.encoder_combo.currentIndex(),
            "quality": self.transcode_tab.get_quality(),
            "resolution": self.transcode_tab.get_resolution(),
            "framerate": self.transcode_tab.get_framerate(),
            "bitrate": self.transcode_tab.get_bitrate(),
            "remote_enable": self.remote_tab.is_enabled(),
            "input_mode": self.input_tab.get_mode(),
            "input_path": self.input_tab.get_path(),
            "last_dir": self.input_tab._current_dir,
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
            self.remote_tab.set_host(settings.get("remote_host", config.DEFAULT_REMOTE_HOST))
            self.remote_tab.set_pass(settings.get("remote_pass", config.DEFAULT_REMOTE_PASS))
            self.remote_tab.set_tunnel_port(settings.get("remote_listen_port", config.DEFAULT_UDP_PORT_REMOTE))
            self.remote_tab.set_play_port(settings.get("local_play_port", 6000))
            self.transcode_tab.set_encoder_index(settings.get("encoder_index", 0))
            self.transcode_tab.set_quality(settings.get("quality", "low"))
            self.transcode_tab.set_resolution(settings.get("resolution", "1920x1080"))
            self.transcode_tab.set_framerate(settings.get("framerate", "原始"))
            self.transcode_tab.set_bitrate(settings.get("bitrate", ""))
            self.remote_tab.set_enabled(settings.get("remote_enable", True))
            self.input_tab.set_mode(settings.get("input_mode", "文件"))
            self.input_tab.set_path(settings.get("input_path", ""))
            if hasattr(self.input_tab, 'network_input'):
                self.input_tab.network_input.setText(settings.get("network_url", ""))
            last_dir = settings.get("last_dir", "")
            if last_dir and os.path.isdir(last_dir):
                self.input_tab._current_dir = last_dir
                self.input_tab.dir_path.setText(last_dir)
                self.input_tab._refresh_list()
            if self.input_tab.get_path():
                self.input_tab.show_file_info(self.input_tab.get_path())
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
