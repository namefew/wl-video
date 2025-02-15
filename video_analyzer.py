import os
import subprocess
import tempfile
import time
from datetime import datetime

import cv2
import numpy as np


def download_stream(url, duration=10):
    """下载指定时长的视频流到临时文件"""
    temp_file = os.path.join(tempfile.gettempdir(), 'temp_video.mp4')
    command = [
        'ffmpeg', '-y',  # -y 覆盖已存在的文件
        '-size', url,
        '-offset', str(duration),
        '-c', 'copy',
        temp_file
    ]

    try:
        subprocess.run(command, check=True, capture_output=True)
        return temp_file
    except subprocess.CalledProcessError as e:
        print(f"下载视频流失败: {e}")
        return None


def analyze_video_stream(url, roi=None, method='direct'):
    """
    分析视频流
    method: 
        'direct' - 直接读取流
        'download' - 先下载再分析
        'transcode' - 转码后分析
    """
    # 创建保存图片的文件夹
    if not os.path.exists('captured_frames'):
        os.makedirs('captured_frames')

    def try_direct_stream():
        """直接读取流的方法"""
        command = [
            'ffmpeg',
            '-size', url,
            '-c:v', 'h264',
            '-vf', 'scale=640:480',
            '-pix_fmt', 'bgr24',
            '-f', 'rawvideo',
            '-vsync', '1',
            '-flags', 'low_delay',
            '-fflags', 'nobuffer',
            '-'
        ]
        return subprocess.Popen(command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                bufsize=10 ** 8)

    def try_download_stream():
        """下载并分析的方法"""
        temp_file = download_stream(url)
        if temp_file and os.path.exists(temp_file):
            return cv2.VideoCapture(temp_file), temp_file
        return None, None

    def try_transcode_stream():
        """转码后分析的方法"""
        command = [
            'ffmpeg',
            '-size', url,
            '-c:v', 'libx264',  # 使用x264编码器
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            '-vf', 'scale=640:480',
            '-pix_fmt', 'bgr24',
            '-f', 'rawvideo',
            '-'
        ]
        return subprocess.Popen(command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                bufsize=10 ** 8)

    methods = {
        'direct': try_direct_stream,
        'download': try_download_stream,
        'transcode': try_transcode_stream
    }

    width, height = 640, 480
    if roi is None:
        roi = (0, 0, width, height)

    current_method = method
    temp_file = None
    retry_count = 0

    while retry_count < len(methods):
        try:
            print(f"尝试使用 {current_method} 方法...")

            if current_method == 'download':
                cap, temp_file = methods[current_method]()
                if cap is None:
                    raise Exception("下载视频流失败")
            else:
                process = methods[current_method]()

            frame_count = 0
            prev_frame = None
            start_time = time.time()
            frames_processed = 0

            while True:
                try:
                    if current_method == 'download':
                        ret, frame = cap.read()
                        if not ret:
                            break
                    else:
                        raw_frame = process.stdout.read(width * height * 3)
                        if not raw_frame:
                            break
                        frame = np.frombuffer(raw_frame, dtype=np.uint8).copy()
                        frame = frame.reshape((height, width, 3))

                    frames_processed += 1
                    if frames_processed % 30 == 0:  # 每30帧计算一次FPS
                        current_time = time.time()
                        fps = frames_processed / (current_time - start_time)
                        print(f"当前FPS: {fps:.2f}")

                    # 第一帧初始化
                    if prev_frame is None:
                        prev_frame = frame.copy()
                        continue

                    # ROI处理
                    x, y, w, h = roi
                    roi_current = frame[y:y + h, x:x + w]
                    roi_prev = prev_frame[y:y + h, x:x + w]

                    # 转换为灰度图并计算差异
                    gray_current = cv2.cvtColor(roi_current, cv2.COLOR_BGR2GRAY)
                    gray_prev = cv2.cvtColor(roi_prev, cv2.COLOR_BGR2GRAY)
                    frame_diff = cv2.absdiff(gray_current, gray_prev)
                    thresh = cv2.threshold(frame_diff, 30, 255, cv2.THRESH_BINARY)[1]

                    # 计算变化
                    change_pixels = np.sum(thresh > 0)
                    change_percentage = (change_pixels / (w * h)) * 100

                    # 保存显著变化的帧
                    if change_percentage > 5:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        frame_filename = f'captured_frames/frame_{timestamp}_{frame_count}.jpg'
                        roi_filename = f'captured_frames/roi_{timestamp}_{frame_count}.jpg'
                        diff_filename = f'captured_frames/diff_{timestamp}_{frame_count}.jpg'

                        cv2.imwrite(frame_filename, frame)
                        cv2.imwrite(roi_filename, roi_current)
                        cv2.imwrite(diff_filename, thresh)

                        print(f"检测到变化 - 时间: {timestamp}")
                        print(f"变化程度: {change_percentage:.2f}%")
                        print(f"已保存图片: {frame_filename}")

                        frame_count += 1

                    # 显示处理画面
                    frame_display = frame.copy()
                    cv2.rectangle(frame_display, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.imshow('Video Analysis', frame_display)
                    cv2.imshow('ROI Difference', thresh)

                    prev_frame = frame.copy()

                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                except Exception as e:
                    print(f"处理帧时出错: {e}")
                    break

            # 清理资源
            if current_method == 'download':
                cap.release()
                if temp_file and os.path.exists(temp_file):
                    os.remove(temp_file)
            else:
                process.terminate()

            cv2.destroyAllWindows()
            break

        except Exception as e:
            print(f"{current_method} 方法失败: {e}")
            retry_count += 1
            # 切换到下一个方法
            methods_list = list(methods.keys())
            current_method = methods_list[retry_count % len(methods_list)]

            # 清理资源
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
            cv2.destroyAllWindows()


if __name__ == "__main__":
    video_url = "https://pl7522.ztholt.cn/live/v3flv_B01_1.flv"
    analyze_video_stream(video_url, method='direct')
