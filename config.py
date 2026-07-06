DEFAULT_REMOTE_HOST = "user@192.168.1.x"
DEFAULT_REMOTE_PASS = ""
DEFAULT_LOCAL_IP = "192.168.1.x"
DEFAULT_UDP_PORT_LOCAL = 5000
DEFAULT_UDP_PORT_REMOTE = 5001
DEFAULT_SSH_PORT = 22
REMOTE_OS_OPTIONS = ["Windows", "Linux"]
DEFAULT_REMOTE_OS = "Windows"

INPUT_MODES = ["文件", "文件夹"]
ENCODER_PRESETS = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower"]
ENCODER_OPTIONS = [
    {"label": "H.264 软件编码（兼容性佳）",     "enc": "libx264",  "hw": False},
    {"label": "H.265 软件编码（压缩率高）",     "enc": "libx265",  "hw": False},
    {"label": "H.264 NVENC（RTX 加速编码）",   "enc": "h264_nvenc", "hw": False},
    {"label": "H.265 NVENC（RTX 加速编码）",   "enc": "hevc_nvenc", "hw": False},
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
