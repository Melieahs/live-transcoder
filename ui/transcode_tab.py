from PyQt5.QtWidgets import QWidget, QFormLayout, QComboBox, QLineEdit

import config


class TranscodeTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QFormLayout(self)

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

    def set_quality(self, q):
        self.quality_combo.setCurrentText(q)

    def set_resolution(self, r):
        self.resolution_combo.setCurrentText(r)

    def set_framerate(self, f):
        self.framerate_combo.setCurrentText(f)

    def set_bitrate(self, b):
        self.bitrate_input.setText(b)
