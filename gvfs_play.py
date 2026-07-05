import subprocess, time, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import streamer

HOST = os.environ.get('GVFS_HOST', 'user@192.168.1.x')
PASS = os.environ.get('GVFS_PASS', '')
LOCAL_IP = os.environ.get('GVFS_LOCAL_IP', '192.168.1.5')
SRC = os.environ.get('GVFS_SRC', '')
TUNNEL_PORT = os.environ.get('GVFS_TUNNEL_PORT', '5001')
PLAY_PORT = os.environ.get('GVFS_PLAY_PORT', '6000')
SSH_PORT = os.environ.get('GVFS_SSH_PORT', '22')

encoder = os.environ.get('GVFS_ENCODER', 'libx264')
quality = os.environ.get('GVFS_QUALITY', 'low')
resolution = os.environ.get('GVFS_RESOLUTION', '1920x1080')
framerate = os.environ.get('GVFS_FRAMERATE', '60')
bitrate = os.environ.get('GVFS_BITRATE', '')

transcode_args = streamer.build_transcode_args(encoder, quality, resolution, framerate, bitrate)

port_flag = f" -p {SSH_PORT}" if SSH_PORT != "22" else ""

subprocess.run(
    f'sshpass -p \'{PASS}\' ssh{port_flag} {HOST} "taskkill /f /im ffmpeg.exe"',
    shell=True, capture_output=True, timeout=5)
time.sleep(1)

local = subprocess.Popen(['ffmpeg','-y','-i',SRC,
    '-c:v','copy','-c:a','aac','-b:a','128k',
    '-flush_packets','1','-f','mpegts',f'tcp://0.0.0.0:{TUNNEL_PORT}?listen'],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

mpv_p = subprocess.Popen(['mpv',f'tcp://0.0.0.0:{PLAY_PORT}?listen',
    '--cache=yes','--demuxer-max-bytes=300M','--no-cache-pause'],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

remote = subprocess.Popen(
    f'sshpass -p \'{PASS}\' ssh{port_flag} {HOST} '
    f'"ffmpeg -y -f mpegts -i tcp://{LOCAL_IP}:{TUNNEL_PORT} '
    f'{transcode_args} '
    f'-f mpegts tcp://{LOCAL_IP}:{PLAY_PORT}"',
    shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

local.wait()
