# Untitled - By: tenom - 周日 10月 30 2022

import os, sys
import sensor, image, time, lcd, time # 此版本中_thread不能用
import KPU as kpu
import audio   # 创建audio对象
import _thread
from Maix import I2S, GPIO   # 创建I2S对象(用于处理音频对象)
from fpioa_manager import fm
from machine import I2C  # 创建I2C用来处理测温对象
from machine import Timer,PWM # 舵机相关模块
from board import board_info


# =========全局参数=================
# 当前模式
state = 1
wifi_state = 0
# 检测结果音频列表[未佩戴口罩，未正确佩戴口罩，正确佩戴口罩]
audio_list = ["/sd/audio/without_mask.wav", "/sd/audio/with_incorrect_mask.wav", "/sd/audio/with_correct_mask.wav"]
# 系统启动音频
start_audio = '/sd/audio/start.wav'
# 三类标签
labels = ["without_mask", "with_incorrect_mask", "with_correct_mask"]
# 三类标注框,对应三类标签,[红,黄,绿]
rectangle_colors = [(255, 0, 0), (255, 255, 0), (0, 255, 0)]
# 锚点参数,由训练模型生成
#anchors = [0.4624, 0.6407, 1.0504, 1.4755, 1.5644, 2.7494, 2.7246, 3.2987, 4.4157, 4.42]
anchors = [4.09, 4.66, 1.5, 2.22, 0.62, 0.84, 2.56, 3.31, 5.03, 6.19]
# 模型存放地址
model_addr="/sd/model/mask.kmodel"

count_sum = [0,0,0] #累积
recognition_number = 10    # 确定身份需要识别的次数
offset = 3  # 偏移量，值越小，识别越严格
# 系统启动图片地址
start_background = "pics/logo.jpg"
# 模型加载失败图片地址
model_load_error = "/sd/pics/model_load_error.jpg"
#wifi
SSID = "wifi name"
PASW = "wifi password"
#wifi相关音频地址
wifi_audio = ["/sd/audio/wifi_connecting.wav","/sd/audio/wifi_connected.wav","/sd/audio/wifi_fail.wav"]



# =========设备初始化================
#led灯点亮:wifi连接未连接红灯,成功绿灯
def led_on():
    if wifi_state == 0:
        fm.register(board_info.LED_R,fm.fpioa.GPIO0)
        led_r=GPIO(GPIO.GPIO0,GPIO.OUT)
        time.sleep_ms(200)
        led_r.value(0)
    else:
        fm.unregister(board_info.LED_R)#注销引脚映射
        fm.register(board_info.LED_G,fm.fpioa.GPIO0)
        led_g=GPIO(GPIO.GPIO0,GPIO.OUT)
        time.sleep_ms(200)
        led_g.value(0)

def display_init():
    # lcd初始化
    lcd.init(type=1)
    lcd.clear(lcd.WHITE)
    #lcd.rotation(1)  # 屏幕旋转

def camera_init():
    # 摄像头初始化
    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)  # 像素格式彩色RGB
    sensor.set_framesize(sensor.QVGA)  # 设置帧的大小为QVGA（320*240）
    sensor.set_windowing((224,224))  # 设置窗口ROI：在要处理的图像中提取出的要处理的区域。
    sensor.set_hmirror(0)   # 设置摄像头水平镜像：enable: 1 表示开启水平镜像 0 表示关闭水平镜像
    sensor.set_vflip(0)   # 设置摄像头垂直翻转：enable: 1 表示开启垂直翻转 0 表示关闭垂直翻转
    sensor.run(0)  # 图像捕捉功能：enable: 1 表示开始抓取图像 0 表示停止抓取图像

def motor_init():
    # 舵机模块初始化
    tim = Timer(Timer.TIMER0, Timer.CHANNEL0, mode=Timer.MODE_PWM)
    # PWM 通过定时器配置，接到 IO21 引脚
    global S1
    S1 = PWM(tim, freq=50, duty=0, pin=21)
    # 舵机复位,角度为0
    S1.duty((0+90)/180*10+2.5)
    # 延迟缓冲
    time.sleep(1)

# ==音频模块初始化==
def audio_init():
    # 注册I2S引脚
    fm.register(34, fm.fpioa.I2S0_OUT_D1, force=True)
    fm.register(35, fm.fpioa.I2S0_SCLK, force=True)
    fm.register(33, fm.fpioa.I2S0_WS, force=True)
    # 初始化I2S
    global wav_dev
    wav_dev = I2S(I2S.DEVICE_0)
    wav_dev.channel_config(wav_dev.CHANNEL_1, I2S.TRANSMITTER,
                            resolution = I2S.RESOLUTION_16_BIT,
                            cycles = I2S.SCLK_CYCLES_32,
                            align_mode = I2S.RIGHT_JUSTIFYING_MODE)

def enable_esp32():
    from network_esp32 import wifi
    if wifi.isconnected() == False:
        for i in range(5):
            try:
                # Running within 3 seconds of power-up can cause an SD load error
                # wifi.reset(is_hard=False)
                wifi.reset(is_hard=True)
                print('try AT connect wifi...')
                wifi.connect(SSID, PASW)
                if wifi.isconnected():
                    global wifi_state
                    wifi_state = 1
                    led_on()
                    lcd.draw_string(0, 224, wifi.ifconfig()[2])
                    audio_play(wifi_audio[1])
                    break
            except Exception as e:
                print(e)
                audio_play(wifi_audio[2])
    print('network state:', wifi.isconnected(), wifi.ifconfig())#ifconfig打印三串数据

# =============定义控制函数======================
# 音频函数
def audio_play(audio_addr):
    # 构造 Audio 对象,参数需标明关键字
    player = audio.Audio(path=audio_addr)
    # 播放音量
    player.volume(80)
    # 预处理音频对象,在播放之前需要对音频文件进行解析,参数:用于播放的I2S设备
    wav_info = player.play_process(wav_dev)
    # 根据 audio 信息配置 I2S 对象
    wav_dev.set_sample_rate(wav_info[1])
    # loop to play audio
    while True:
        ret = player.play()
        # 格式不支持播放
        if ret == None:
            print("format error")
            break
        # 播放结束(1为正在播放)
        elif ret == 0:
            break
    time.sleep_ms(100)  # 结束后延时100ms,否则有刺耳的声音
    # 播放结束,回收底层分配的资源
    player.finish()


# 加载单张图片
def display_signal_pic(pic_addr):
    img = image.Image(pic_addr, copy_to_fb=True)
    lcd.display(img)


# 画框并标注度
def display_rectangle_str(position, label, color, scale, img):
    img.draw_rectangle(position, color=color, thickness=4)   # 画框
    img.draw_string(position[0], position[1], label, scale=scale, color=color)  #标明类别


# 加载模型
def load_model(model_addr, anchors):
    task = None  #清空
    task = kpu.load(model_addr)   #加载sd卡中的kmodel模型
    kpu.init_yolo2(task, 0.5, 0.3, 5, anchors) # threshold:[0,1], nms_value: [0, 1]初始化yolov2网络，识别可信概率为0.5（50%）
    return task

# 舵机开门-延时-关门
def servo_control(servo,wait):
    angle = -90
    servo.duty((angle+90)/180*10+2.5)
    time.sleep_ms(wait)
    angle = 0
    servo.duty((angle+90)/180*10+2.5)

def key_init():
    # Boot按键初始化
    # 注册IO,Boot key-->IO16,K210高速GPIO才有外部中断
    fm.register(16,fm.fpioa.GPIOHS0)
    # 初始化按键IO
    global KEY
    KEY = GPIO(GPIO.GPIOHS0,GPIO.IN,GPIO.PULL_UP)

def key_irq(KEY):
    global wifi_state
    # 按键消抖
    time.sleep_ms(100)
    if(KEY.value()==0):
        if(wifi_state == 0):
            #state = not state
            audio_play(wifi_audio[0])
            enable_esp32()
            # 摄像头开始拍摄
            #sensor.run(1)
        else:
            #state = not state
            print("wifi already connected")
            # 摄像头停止拍摄
            #sensor.run(0)

def sendinfo(whichtype):
    if wifi_state == 1:
        import urequests
        headers = {
            'User-Agent': 'Maixpy',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        response = urequests.post("http://192.168.101.10/insert.php", headers=headers, data="type="+whichtype)
        #print(response.text)
        return response.text
    else:
        return "wifi not connected"


def drawConfidenceText(image, rol, classid, value):
    text = ""
    _confidence = int(value * 100)

    if classid == 2:
        text = 'mask: ' + str(_confidence) + '%'
    elif classid == 1:
        text = 'wrong_mask: ' + str(_confidence) + '%'
    else:
        text = 'no_mask: ' + str(_confidence) + '%'

    image.draw_string(rol[0], rol[1], text, color=rectangle_colors[classid], scale=1.5)


def final_decide(img,totalRes,itemROL,classID,confidence):
    img.draw_rectangle(itemROL, rectangle_colors[classID], tickness=3)
    if totalRes == 1:
        drawConfidenceText(img, (0, 0), classID, confidence)
        global count_sum
        count_sum[classID] += 1
        if count_sum[classID] == 10:
            #确认佩戴口罩
            for i in range(3):
                count_sum[i] = 0
            return True
    return False




def mask_recognize(task,img):
    objects = kpu.run_yolo2(task, img)
    print(objects)
    #识别到头像
    if objects:
        totalRes = len(objects)
        for item in objects:
            #置信度
            confidence = float(item.value())
            #标注框位置
            itemROL = item.rect()
            #模型所属类别,映射
            if item.classid() == 0:
                classID = 0
                print("0-0")
            elif item.classid() == 1:
                classID = 2
                print("1-2")
            else:
                classID = 1
                print("2-1")

            if confidence < 0.5:
                #绘制矩形,位置,颜色,线条粗细
                a = img.draw_rectangle(itemROL, color=(40,20,206), tickness=3)
                continue
            #有口罩
            if classID == 2 and confidence > 0.55:
                if final_decide(img,totalRes,itemROL,classID,confidence):
                    #print('==before2==')
                    #无法正常使用多线程
                    #try:
                        ##_thread.start_new_thread(audio_play,(audio_list[classID],))
                        #print("success")
                    #except:
                        #print("error")

                    #print('==after2==')
                    text2 = sendinfo("2")
                    print(text2)
                    lcd.draw_string(0, 224, text2)
                    audio_play(audio_list[classID])
                    servo_control(S1,1000)
                    #_thread.start_new_thread(servo_control,(S1,3000,))
                break
            #未正确佩戴
            elif classID == 1 and confidence > 0.55:
                if final_decide(img,totalRes,itemROL,classID,confidence):
                    print('==before1==')
                    text1 = sendinfo("1")
                    print(text1)
                    lcd.draw_string(0, 224, text1)
                    audio_play(audio_list[classID])

                break
            #无口罩
            elif classID == 0 and confidence > 0.55:
                if final_decide(img,totalRes,itemROL,classID,confidence):
                    #print('==before0==')
                    text0 = sendinfo("0")
                    print(text0)
                    lcd.draw_string(0, 224, text0)
                    audio_play(audio_list[classID])

                break



def func(name):
    a = 1
    while 1:

        print("hello {}".format(name))
        time.sleep(1)



# =========流程控制函数===========
# 启动
def start_up():
    led_on()
    # 显示屏初始化
    display_init()
    # 摄像头初始化
    camera_init()
    # 播放器初始化
    audio_init()
    # 舵机初始化
    motor_init()
    #try:
        #_thread.start_new_thread(func,("1",))
        #print("success")
    #except:
        #print("error")
    # 启动背景图展示
    display_signal_pic(start_background)
    # 播放启动音乐
    audio_play(start_audio)

    # 按键初始化
    key_init()
    # 下降沿触发中断
    KEY.irq(key_irq,GPIO.IRQ_FALLING)



# ==========正式控制流程=============
# 启动
start_up()



# 加载模型
try:
    task = load_model(model_addr, anchors)
except:
    display_signal_pic(model_load_error)
    #看门狗,使系统复位
    #from machine import WDT
    #wdt0 = WDT(id=0, timeout=5000)

    time.sleep_ms(3000)
    # 退出程序
    sys.exit()

# state_flag = []   # 状态标志列表
# state_sum = 0  # 状态和
# check_sum = 0  # 记录每次判断的状态和，将清零前的最后一次用作状态的判断
# flag = True
while state:
    # 摄像头抓取图像
    sensor.run(1)
    img = sensor.snapshot()
    #img = img.resize(224, 224)
    #img.pix_to_ai()
    mask_recognize(task,img)
    lcd.display(img)



