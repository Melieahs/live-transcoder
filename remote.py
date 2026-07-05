import subprocess
import shutil
import re
import time


def check_sshpass():
    return shutil.which("sshpass") is not None


def _ssh(cmd_str, timeout=30):
    return subprocess.run(
        cmd_str, shell=True, capture_output=True, text=True, timeout=timeout, errors="replace"
    )


def _ssh_popen(cmd_str):
    return subprocess.Popen(
        cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1, errors="replace"
    )


def ensure_remote_ffmpeg(host, password):
    result = _ssh(f"sshpass -p '{password}' ssh {host} \"where ffmpeg 2>nul || echo NOT_FOUND\"")
    return "NOT_FOUND" not in result.stdout and result.returncode == 0


def get_remote_host_ip(host):
    match = re.search(r"@([\d.]+)", host)
    return match.group(1) if match else host


def start_remote_ffmpeg(host, password, tunnel_port, transcode_args, return_port):
    remote_cmd = (
        f"ffmpeg -y -f mpegts -i tcp://127.0.0.1:{tunnel_port} "
        f"{transcode_args} "
        f"-f mpegts tcp://127.0.0.1:{return_port}"
    )
    quoted = remote_cmd.replace('"', '\\"')
    proc = _ssh_popen(f"sshpass -p '{password}' ssh {host} \"{quoted}\"")
    return proc


def start_ssh_tunnel(host, password, local_port, remote_port, direction="R"):
    if direction == "R":
        tunnel_arg = f"-R {remote_port}:127.0.0.1:{local_port}"
    else:
        tunnel_arg = f"-L {local_port}:127.0.0.1:{remote_port}"
    proc = _ssh_popen(f"sshpass -p '{password}' ssh {tunnel_arg} -N {host}")
    return proc


def stop_remote_processes(host, password, process_name="ffmpeg"):
    _ssh(f"sshpass -p '{password}' ssh {host} \"taskkill /f /im {process_name}.exe 2>nul\"")
    time.sleep(1)
