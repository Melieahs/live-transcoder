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


def ensure_remote_ffmpeg(host, password, ssh_port=22, remote_os="Windows"):
    if remote_os == "Linux":
        check_cmd = "which ffmpeg || echo NOT_FOUND"
    else:
        check_cmd = "where ffmpeg 2>nul || echo NOT_FOUND"
    port_flag = f" -p {ssh_port}" if ssh_port != 22 else ""
    result = _ssh(
        f"sshpass -p '{password}' ssh{port_flag} {host} \"{check_cmd}\""
    )
    return "NOT_FOUND" not in result.stdout and result.returncode == 0


def get_remote_host_ip(host):
    match = re.search(r"@([\d.]+)", host)
    return match.group(1) if match else host


def start_remote_ffmpeg(host, password, tunnel_port, transcode_args,
                        return_port, target_ip, ssh_port=22, remote_os="Windows",
                        remote_env="", pre_input_args=""):
    port_flag = f" -p {ssh_port}" if ssh_port != 22 else ""
    env_prefix = f"{remote_env} " if remote_env else ""
    remote_cmd = (
        f"{env_prefix}ffmpeg -y {pre_input_args} "
        f"-f mpegts -i tcp://{target_ip}:{tunnel_port} "
        f"{transcode_args} "
        f"-f mpegts tcp://{target_ip}:{return_port}"
    )
    quoted = remote_cmd.replace('"', '\\"')
    proc = _ssh_popen(f"sshpass -p '{password}' ssh{port_flag} {host} \"{quoted}\"")
    return proc


def start_ssh_tunnel(host, password, local_port, remote_port, direction="R",
                     ssh_port=22, remote_os="Windows"):
    port_flag = f" -p {ssh_port}" if ssh_port != 22 else ""
    if direction == "R":
        tunnel_arg = f"-R {remote_port}:127.0.0.1:{local_port}"
    else:
        tunnel_arg = f"-L {local_port}:127.0.0.1:{remote_port}"
    proc = _ssh_popen(f"sshpass -p '{password}' ssh{port_flag} {tunnel_arg} -N {host}")
    return proc


def stop_remote_processes(host, password, process_name="ffmpeg",
                          ssh_port=22, remote_os="Windows"):
    port_flag = f" -p {ssh_port}" if ssh_port != 22 else ""
    if remote_os == "Linux":
        kill_cmd = f"pkill -f {process_name} 2>/dev/null; true"
    else:
        kill_cmd = f"taskkill /f /im {process_name}.exe 2>nul"
    _ssh(f"sshpass -p '{password}' ssh{port_flag} {host} \"{kill_cmd}\"")
    time.sleep(1)
