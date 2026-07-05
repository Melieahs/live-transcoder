import subprocess, time, os

HOST = os.environ.get('GVFS_HOST', 'cyu@192.168.1.30')
PASS = os.environ.get('GVFS_PASS', '201807')
LOCAL_IP = os.environ.get('GVFS_LOCAL_IP', '192.168.1.5')
SRC = os.environ.get('GVFS_SRC', '')

subprocess.run(f'sshpass -p \'{PASS}\' ssh {HOST} "taskkill /f /im ffmpeg.exe"', shell=True, capture_output=True, timeout=5)
time.sleep(1)

local = subprocess.Popen(['ffmpeg','-y','-i',SRC,
    '-c:v','copy','-c:a','aac','-b:a','128k',
    '-flush_packets','1','-f','mpegts','tcp://0.0.0.0:5001?listen'],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2)

mpv_p = subprocess.Popen(['mpv','tcp://0.0.0.0:6000?listen',
    '--cache=yes','--demuxer-max-bytes=300M','--no-cache-pause'],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)

remote = subprocess.Popen(
    f'sshpass -p \'{PASS}\' ssh {HOST} '
    f'"ffmpeg -y -f mpegts -i tcp://{LOCAL_IP}:5001 '
    f'-vf scale=1920:1080 -r 60 '
    f'-c:v libx264 -preset veryfast -crf 25 -tune zerolatency '
    f'-c:a aac -b:a 128k '
    f'-f mpegts tcp://{LOCAL_IP}:6000"',
    shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
time.sleep(5)

print('local:', local.poll() is None, flush=True)
print('mpv:', mpv_p.poll() is None, flush=True)
print('remote:', remote.poll() is None, flush=True)
if remote.poll() is not None:
    _, err = remote.communicate(timeout=2)
    print('remote err:', err[-400:], flush=True)

subprocess.run(f'sshpass -p \'{PASS}\' ssh {HOST} "taskkill /f /im ffmpeg.exe"', shell=True, capture_output=True)
local.terminate(); mpv_p.terminate()
local.wait(); mpv_p.wait()
print('done', flush=True)
