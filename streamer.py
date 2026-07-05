import subprocess
import shutil
import shlex
import re
import os
import signal


def check_ffmpeg():
    return shutil.which("ffmpeg") is not None


def check_ffplay():
    return shutil.which("ffplay") is not None


def check_ffprobe():
    return shutil.which("ffprobe") is not None


def get_media_info(filepath):
    info = {"duration": 0, "width": 0, "height": 0, "fps": 0, "codec": ""}
    if not check_ffprobe():
        return info
    try:
        proc = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams", filepath],
            capture_output=True, text=True, timeout=30
        )
        import json
        data = json.loads(proc.stdout)
        streams = data.get("streams", [])
        for s in streams:
            if s.get("codec_type") == "video":
                info["width"] = int(s.get("width", 0))
                info["height"] = int(s.get("height", 0))
                info["codec"] = s.get("codec_name", "")
                avg_fps = s.get("avg_frame_rate", "0/1")
                if "/" in avg_fps:
                    try:
                        num, den = avg_fps.split("/")
                        info["fps"] = round(float(num) / float(den))
                    except:
                        info["fps"] = 0
        fmt = data.get("format", {})
        dur = fmt.get("duration", "0")
        try:
            info["duration"] = round(float(dur))
        except:
            info["duration"] = 0
    except:
        pass
    return info


def build_sender_cmd(input_source, input_mode, send_port, encode_args, hw_accel):
    cmd = ["ffmpeg", "-y"]

    if input_source and os.path.exists(input_source):
        cmd += ["-i", input_source]

    if encode_args:
        cmd += encode_args.split()

    cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
            "-flush_packets", "1", "-f", "mpegts",
            f"tcp://0.0.0.0:{send_port}?listen"]
    return cmd


def build_play_cmd(play_port):
    return ["mpv", f"tcp://0.0.0.0:{play_port}?listen",
            "--cache=yes", "--demuxer-max-bytes=300M", "--no-cache-pause"]


def build_transcode_args(encoder, quality, resolution, framerate, bitrate):
    import config
    parts = []
    qp = config.QUALITY_PRESETS.get(quality, config.QUALITY_PRESETS["medium"])

    vf_parts = []
    if resolution and resolution != "原始":
        vf_parts.append(f"scale={resolution.replace('x', ':')}")
    if vf_parts:
        parts.extend(["-vf", ",".join(vf_parts)])
    if framerate and framerate != "原始":
        parts.extend(["-r", framerate])

    if encoder == "libx264":
        parts.extend(["-c:v", "libx264", "-preset", qp["preset"], "-crf", qp["crf"], "-tune", "zerolatency"])
    elif encoder == "libx265":
        parts.extend(["-c:v", "libx265", "-preset", qp["preset"], "-crf", qp["crf"]])
    elif encoder == "h264_nvenc":
        parts.extend(["-c:v", "h264_nvenc", "-preset", "p6", "-cq", qp["crf"]])
    elif encoder == "hevc_nvenc":
        parts.extend(["-c:v", "hevc_nvenc", "-preset", "p6", "-cq", qp["crf"]])

    if bitrate:
        parts.extend(["-b:v", bitrate])

    parts.extend(["-c:a", "aac", "-b:a", "128k"])
    return " ".join(parts)


class StreamProcess:
    def __init__(self):
        self.proc = None

    def start(self, cmd, env=None, name=""):
        self.stop()
        if isinstance(cmd, str):
            import shlex
            cmd = shlex.split(cmd)
        self._name = name
        self.proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, bufsize=1, env=env
        )

    def stop(self):
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except:
                self.proc.kill()
                self.proc.wait()
            self.proc = None

    def is_running(self):
        return self.proc is not None and self.proc.poll() is None

    def read_stderr_line(self):
        if self.proc and self.proc.stderr:
            return self.proc.stderr.readline()
        return ""
