import os
import numpy as np
import cv2
import threading
from concurrent.futures import ThreadPoolExecutor
from logger import LogManager
from stream_manager import bt

logger = LogManager.setup()

# 配置参数
REGIONS = [(486, 924, 94, 96),  # (x,y,width,height)
           (724, 924, 94, 96)]

OUTPUT_DIR = "captured_images"
# 初始化输出目录
os.makedirs(OUTPUT_DIR, exist_ok=True)

def callback(*args):
    """流回调函数"""
    if args[0] == "video" and args[1]:
        data = args[1].get('data')
        if data:
            try:
                # 将数据发送给处理器
                logger.debug(f"写入 {len(data)} bytes 到解码器")
            except Exception as e:
                logger.error(f"数据处理失败: {str(e)}")
        else:
            logger.warning("收到空视频数据")

# 将 status 定义为全局变量
global status
status = 0

# 创建线程池
executor = ThreadPoolExecutor(max_workers=5)  # 根据需要调整 max_workers

def on_image_ready(event):
    """使用OpenCV实时显示截取区域"""
    global status  # 声明 status 为全局变量

    # 遍历每个帧的截取区域
    for idx, frame_images in enumerate(event['images']):
        if len(frame_images) != 2:
            logger.warning(f"帧 {idx} 的截取区域数量不正确: {len(frame_images)}")
            continue

        white_ratio0 = get_white_ratio(frame_images[0])
        white_ratio1 = get_white_ratio(frame_images[1])

        if status != 1 and 0.008 < white_ratio0 <= 0.028 and 0.008 < white_ratio1 <= 0.028:
            executor.submit(showImages, frame_images)
            status = 1
        elif status != 2 and 0.028 < white_ratio0 <= 0.6 and 0.028 < white_ratio1 <= 0.6:
            executor.submit(showImages, frame_images)
            status = 2
        elif status != 0 and (0.6 < white_ratio0 and 0.6 < white_ratio1 or white_ratio0 <= 0.008 and white_ratio1 <= 0.008):
            executor.submit(showImages, frame_images)
            status = 0

def showImages(frame_images):
    """使用OpenCV实时显示截取区域"""
    # 创建两个窗口，并设置为可调整大小
    cv2.namedWindow('Region 1', cv2.WINDOW_NORMAL)
    cv2.namedWindow('Region 2', cv2.WINDOW_NORMAL)

    # 设置窗口初始位置和大小（可选）
    cv2.moveWindow('Region 1', 100, 100)  # 窗口1的位置 (x=100, y=100)
    cv2.moveWindow('Region 2', 600, 100)  # 窗口2的位置 (x=600, y=100)
    # cv2.resizeWindow('Region 1', 400, 300)  # 窗口1的大小 (width=400, height=300)
    # cv2.resizeWindow('Region 2', 400, 300)  # 窗口2的大小 (width=400, height=300)

    for region_idx, img in enumerate(frame_images):
        if img is not None and img.size > 0:
            # 自动调整窗口大小
            h, w = img.shape[:2]
            cv2.resizeWindow(f'Region {region_idx + 1}', w, h)

            # 显示图像（BGR格式直接显示）
            cv2.imshow(f'Region {region_idx + 1}', img)

    # 按ESC键退出
    if cv2.waitKey(1) == 27:
        cv2.destroyAllWindows()

def get_white_ratio(image, threshold=200):
    """检查图片中是否包含超过指定比例的白色像素"""
    if not isinstance(image, np.ndarray) or image.ndim not in [2, 3]:
        logger.warning("图像数据无效，无法计算白像素比例")
        return 0.0

    if image.ndim == 3:
        gray = np.mean(image, axis=2)  # 更快地转换为灰度图
    else:
        gray = image  # 图像已经是灰度图

    white_pixels = np.count_nonzero(gray > threshold)
    total_pixels = gray.size
    return white_pixels / total_pixels

if __name__ == "__main__":
    logger.info("启动流媒体处理器...")
    stream_manager = bt(data_callback=None, logger=logger, regions=REGIONS, image_callback=on_image_ready)
    # 开始拉流
    stream_manager.direct_stream_reader('https://pl2079.gslxqy.com/live/v2flv_L01_2.flv')
    # stream_manager.direct_stream_reader('https://pl2079.gslxqy.com/live/v2flv_L01_2_l.flv')
