from PyQt5.QtWidgets import QWidget, QFormLayout, QComboBox, QLineEdit
from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtCore import QRegularExpression

import config
import streamer


def _build_encoder_items():
    items = []
    for opt in config.ENCODER_OPTIONS:
        tag = "HW" if "nvenc" in opt["enc"] else "SW"
        items.append((f"[{tag}] {opt['label']}", opt))
    return items


class TranscodeTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QFormLayout(self)

        self.encoder_combo = QComboBox()
        for label, opt in _build_encoder_items():
            self.encoder_combo.addItem(label, opt)
        self.encoder_combo.currentIndexChanged.connect(self._invalidate_cached_args)
        layout.addRow("编码器:", self.encoder_combo)

        self.quality_combo = QComboBox()
        self.quality_combo.addItems(config.TRANSCODE_QUALITY)
        self.quality_combo.setCurrentText("low")
        self.quality_combo.currentTextChanged.connect(self._invalidate_cached_args)
        layout.addRow("画质:", self.quality_combo)

        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(config.RESOLUTIONS)
        self.resolution_combo.currentTextChanged.connect(self._invalidate_cached_args)
        layout.addRow("分辨率:", self.resolution_combo)

        self.framerate_combo = QComboBox()
        self.framerate_combo.addItems(config.FRAMERATES)
        self.framerate_combo.currentTextChanged.connect(self._invalidate_cached_args)
        layout.addRow("帧率:", self.framerate_combo)

        self.bitrate_input = QLineEdit()
        self.bitrate_input.setPlaceholderText("如 5M 或留空使用 CRF")
        bitrate_regex = QRegularExpression(r"^\d+[kKmMgG]?$")
        self.bitrate_input.setValidator(
            QRegularExpressionValidator(bitrate_regex, self.bitrate_input)
        )
        self.bitrate_input.textChanged.connect(self._invalidate_cached_args)
        layout.addRow("码率(选填):", self.bitrate_input)

        self._cached_args = None

    def _invalidate_cached_args(self):
        self._cached_args = None

    def get_args(self):
        if self._cached_args is None:
            self._cached_args = streamer.build_transcode_args(
                self.get_encoder(),
                self.get_quality(),
                self.get_resolution(),
                self.get_framerate(),
                self.get_bitrate(),
            )
        return self._cached_args

    def get_encoder(self):
        data = self.encoder_combo.currentData()
        return data["enc"] if data else "libx264"

    def get_quality(self):
        return self.quality_combo.currentText()

    def get_resolution(self):
        return self.resolution_combo.currentText()

    def get_framerate(self):
        return self.framerate_combo.currentText()

    def get_bitrate(self):
        return self.bitrate_input.text().strip()

    def set_encoder_index(self, idx):
        self.encoder_combo.setCurrentIndex(idx)
        self._invalidate_cached_args()

    def set_quality(self, q):
        self.quality_combo.setCurrentText(q)

    def set_resolution(self, r):
        self.resolution_combo.setCurrentText(r)

    def set_framerate(self, f):
        self.framerate_combo.setCurrentText(f)

    def set_bitrate(self, b):
        self.bitrate_input.setText(b)
