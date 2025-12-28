# Maixduino K210 口罩佩戴检测系统

基于 MaixPy 的 Maixduino-K210 端侧口罩佩戴检测，结合语音播报、舵机门闸模拟，并将检测结果上传到局域网 Web 端进行可视化。

- 三类检测：未佩戴 / 未正确佩戴 / 正确佩戴
- 实时 LCD 预览与框选
- 语音播报和 LED 状态指示
- 舵机模拟门禁
- 局域网数据上传与 ECharts 可视化

## 系统流程
<p align="center">
  <img src="https://github.com/user-attachments/assets/ebb56899-c458-4569-a607-349701ef6784" alt="系统流程图" width="780">
</p>

## 目录结构
- `Server/`：运行在 K210 上的 MaixPy 脚本、模型和资源
  - `main.py`：主流程，YOLOv2 推理、音频提示、舵机控制、HTTP 上报
  - `network_esp32.py`：通过板载 ESP32 模块联网
  - `urequests.py`：轻量 HTTP 客户端
  - `model/mask.kmodel`：YOLOv2 KPU 模型
  - `audio/`、`pics/`：语音提示和启动/异常图片
- `Web/`：PHP + MySQL 数据收集与可视化页面（依赖 `echarts.js`）

## 硬件准备
- Maixduino-K210（带 ESP32 模块）+ MaixPy 固件
- TF/SD 卡（≥ 1GB），用于模型与资源
- LCD（Maixduino 标配屏）与摄像头
- 扬声器（I2S 输出）：I2S0_WS=GPIO33，I2S0_OUT_D1=GPIO34，I2S0_SCLK=GPIO35
- 舵机（IO21，50Hz PWM），用于门闸模拟
- 板载 Boot 按键（IO16）用于触发 WiFi 连接

## SD 卡文件布局
将 `Server` 目录下文件拷贝到 SD 卡根目录，保持路径一致（MaixPy 挂载点为 `/sd`）：
```
/sd/main.py
/sd/network_esp32.py
/sd/urequests.py
/sd/model/mask.kmodel
/sd/audio/*.wav
/sd/pics/logo.jpg
/sd/pics/model_load_error.jpg
```

## 设备端配置与运行
1) 刷写 MaixPy 固件到 Maixduino，确认能访问 SD 卡、摄像头、LCD、音频、舵机。  
2) 修改 `main.py` 中的无线和服务器地址：
   - `SSID`/`PASW`：WiFi 名称和密码
   - `sendinfo()` 里的 `http://192.168.101.10/insert.php`：替换为实际 Web 服务器 IP
3) 上电后，系统会显示启动画面并播报开机音。按下 Boot 键触发 `enable_esp32()` 连接 WiFi，成功后 LED 由红转绿并播报连接成功。  
4) 摄像头实时推流到 LCD，检测到人脸后会按阈值分类并播报，对应结果：
   - 0 未佩戴：播放 `without_mask.wav`
   - 1 未正确佩戴：播放 `with_incorrect_mask.wav`
   - 2 正确佩戴：播放 `with_correct_mask.wav`，舵机短暂开门
5) 若 WiFi 已连接，会将结果 `type=0/1/2` 通过 HTTP POST 上传到服务器 `insert.php`。

## Web 端部署（局域网）
运行环境：PHP（带 mysqli）、MySQL 8+、HTTP 服务器（Apache/Nginx）。

1) 数据库初始化（默认连接信息：`192.168.101.10:3306`，用户 `root`，密码 `phpts`，库名 `mask`，可根据需要修改 `insert.php/query.php/buildlist.php` 中的配置）。
```sql
CREATE DATABASE IF NOT EXISTS mask DEFAULT CHARSET utf8mb4;
USE mask;

CREATE TABLE IF NOT EXISTS detail (
  id   INT AUTO_INCREMENT PRIMARY KEY,
  date DATE NOT NULL,
  time TIME NOT NULL,
  type TINYINT NOT NULL COMMENT '0未佩戴,1未正确佩戴,2正确佩戴'
);

CREATE TABLE IF NOT EXISTS byday (
  id     INT AUTO_INCREMENT PRIMARY KEY,
  date   DATE NOT NULL UNIQUE,
  u_mask INT DEFAULT 0,
  w_mask INT DEFAULT 0,
  mask   INT DEFAULT 0
);
```
可用每日任务生成/刷新 `byday` 统计（示例）：
```sql
INSERT INTO byday (date, u_mask, w_mask, mask)
SELECT d.date,
       SUM(type=0) AS u_mask,
       SUM(type=1) AS w_mask,
       SUM(type=2) AS mask
FROM detail d
GROUP BY d.date
ON DUPLICATE KEY UPDATE
  u_mask=VALUES(u_mask), w_mask=VALUES(w_mask), mask=VALUES(mask);
```

2) 将 `Web/` 下所有文件放到 Web 站点根目录（或子路径），确保 `echarts.js` 可被访问。  
3) 确保服务器与 K210 处于同一网段，防火墙开放 HTTP 和 MySQL。  
4) 浏览器访问 `map.html` 查看统计结果；页面会按日期下拉框查询 `query.php` 并用 ECharts 画柱状图，同时显示累计计数。

## 关键参数与调试
- 模型阈值：`main.py` 中 `kpu.init_yolo2(..., threshold=0.5, nms=0.3)`，以及各类别置信度下限（0.55）；需要调整精度/召回时可微调。  
- 锚框：`anchors = [4.09, 4.66, 1.5, 2.22, 0.62, 0.84, 2.56, 3.31, 5.03, 6.19]`，若替换模型需同步更新。  
- 舵机：默认 PWM 50Hz，IO21；开门时间通过 `servo_control(S1, 1000)` 的延时控制。  
- 音频：播放音量在 `audio_play()` 中 `player.volume(80)` 设置，必要时可调低防止失真。  
- 若模型/资源加载失败会显示 `pics/model_load_error.jpg` 并退出；确认 SD 路径正确且上电 3 秒后再尝试 WiFi（避免 SD 初始化异常）。  
- WiFi 连接需按 Boot 键触发，串口日志会输出连接状态与分配的 IP。

## 快速复现清单
- 软硬件连线确认（摄像头、LCD、舵机 IO21、I2S 音频、ESP32 天线）。  
- SD 卡按上述结构拷贝；`main.py` 配置好 WiFi 和服务器地址。  
- MySQL 初始化并放置 Web 端文件，浏览器可访问 `map.html`。  
- 上电→按 Boot 连接 WiFi→观察 LCD 检测与语音→检查服务器 `detail` 表是否收到数据→在 `map.html` 查看统计。

## 参考项目
- https://github.com/lightyLi/Face-Mask-detction-DeepLearning
