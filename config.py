DEFAULT_REMOTE_HOST = "cyu@192.168.1.30"
DEFAULT_REMOTE_PASS = "201807"
DEFAULT_LOCAL_IP = "192.168.1.100"
DEFAULT_UDP_PORT_LOCAL = 5000
DEFAULT_UDP_PORT_REMOTE = 5001

INPUT_MODES = ["文件", "桌面录制", "摄像头"]
ENCODER_PRESETS = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower"]
ENCODER_OPTIONS = [
    {"label": "H.264 软件编码（兼容性佳）",     "enc": "libx264",  "hw": False},
    {"label": "H.264 VAAPI（Intel 核显加速）",  "enc": "h264_vaapi", "hw": True},
    {"label": "H.265 软件编码（压缩率高）",     "enc": "libx265",  "hw": False},
    {"label": "H.265 VAAPI（Intel 核显加速）",  "enc": "hevc_vaapi", "hw": True},
]

TRANSCODE_QUALITY = ["lossless", "veryhigh", "high", "medium", "low", "verylow"]

QUALITY_PRESETS = {
    "lossless": {"crf": "0",  "preset": "ultrafast"},
    "veryhigh": {"crf": "15", "preset": "veryfast"},
    "high":     {"crf": "20", "preset": "veryfast"},
    "medium":   {"crf": "25", "preset": "veryfast"},
    "low":      {"crf": "30", "preset": "veryfast"},
    "verylow":  {"crf": "35", "preset": "ultrafast"},
}

RESOLUTIONS = ["原始", "3840x2160", "2560x1440", "1920x1080", "1280x720", "854x480"]
FRAMERATES = ["原始", "60", "30", "24", "15", "10"]
