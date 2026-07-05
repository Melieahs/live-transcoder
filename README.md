# Live Transcoder - 实时远程转码播放

利用远程主机（Windows）的 GPU 算力，将本地视频实时转码后回传播放。

## 原理

```
本地 ffmpeg -i 源文件 -c:v copy -c:a aac → tcp://0.0.0.0:5001?listen
                                          ↓（等待远程连接）
远程 ffmpeg 接收 tcp://本机IP:5001
  → 解码 → 转码（分辨率/帧率/编码器可调）
  → tcp://本机IP:6000
                   ↓
本地 mpv 播放 tcp://0.0.0.0:6000?listen
```

所有 TCP 连接均为**远程出站到本机**，避免防火墙阻挡。

## 功能

- 支持本地文件、文件夹浏览、GVFS 挂载的 SMB 网络位置
- 远程编码器：H.264/H.265 软件编码、NVENC 硬件加速
- 可调参数：分辨率、帧率、画质、码率
- 自动记忆设置和最后目录
- 文件夹模式支持子目录浏览、双击进入

## 依赖

**本机（Linux）：**
- Python 3 + PyQt5
- ffmpeg / ffplay / mpv
- sshpass

**远程（Windows）：**
- SSH 服务端（OpenSSH Server）
- ffmpeg（建议 gyan.dev 完整版，含 NVENC）

## 使用

```bash
cd ~/Workspace/live_transcoder
python3 main.py
```

1. 选择视频文件（或文件夹模式浏览）
2. 设置远程主机地址和密码
3. 选择编码器和转码参数
4. 点击"开始"或双击文件

## 分支

- `master` — 稳定版（v1.0 / v1.1 / v1.2）
- `dev` — 开发分支
- `netdev` — 网络位置功能（smbclient）

## 版本历史

参见 [CHANGELOG.md](CHANGELOG.md)
