# 更新日志

## v1.0 (2026-07-05)

首次可用版本。实现远程实时转码 + 本地播放。

### 架构
- **直连方案**：去掉 SSH 隧道，远程 ffmpeg 通过 TCP 直连本机 IP，减少加密传输开销
- 传输链路：本地推流 → `tcp://0.0.0.0:5001?listen` → 远程连接拉流 → 转码 → `tcp://本机IP:6000` → 本地 mpv 播放

### 性能优化
- **推流端 `-c copy`**：仅 remux 不编解码，本地 CPU 近零负载
- **去掉 `-re` 限制**：推流端全速发送，不受源文件帧率限制
- **`-flush_packets 1`**：降低 TCP 传输缓冲延迟
- **远程 `-tune zerolatency`**：降低编码端延迟
- **mpv `--cache=yes --demuxer-max-bytes=300M --no-cache-pause`**：大缓存 + 不暂停，容忍远程编码速度波动

### 诊断结论
- 瓶颈在远程 4K→4K 转码（3840x2160@72fps 数据量过大）
- 降分辨率到 1920x1080 后可流畅播放（远程编码压力降低 4 倍）
- 推荐 GUI 设置：分辨率 1920x1080，画质 low 或 medium

### 分支记录
- `master` / `v1.0` / `v1.1` / `v1.2` — 稳定版
- `dev` — 开发分支
- `netdev` — 网络位置功能（smbclient）
- `gvfs-fix` / `gvfs-fix-v2` — GVFS 挂载 SMB 播放修复

## v1.1 (2026-07-05)

### UI 重构
- UI 拆分为独立文件：`ui/input_tab.py`、`ui/transcode_tab.py`、`ui/remote_tab.py`、`ui/widgets.py`
- 文件列表 + 信息面板，双击文件自动播放
- 新增文件夹模式，支持子目录浏览和上级按钮
- 移除已废弃的桌面录制/摄像头模式

### 编码器
- VAAPI 编码器替换为 NVENC（适配远程 Windows RTX4050）
- 去掉本机 `hw_accel` 逻辑（推流已 `-c copy`，无需硬件加速）

## v1.2 (2026-07-05)

### GVFS 支持
- 通过 GVFS 挂载的 SMB 网络位置可直接播放
- 检测到 GVFS 路径时自动调用独立脚本 `gvfs_play.py` 处理
- 支持文件夹模式浏览 GVFS 挂载点

### 兼容性修复
- 推流端音频重编码为 AAC（解决部分文件 `Encryption initialization data` 导致 mpegts 封装失败）
- NVENC 编码前加 `format=yuv420p`，兼容 10bit H.265 源文件
- 修复 NVENC 时 `-vf` 被覆盖导致分辨率设置失效的问题

### 体验优化
- 记住最后浏览的目录，重启自动恢复
- GVFS 路径走独立子进程，避免 `StreamProcess` stderr 缓冲区满导致的异常
