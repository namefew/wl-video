import asyncio
import shutil
from datetime import datetime
import os
import socket
from concurrent.futures import ThreadPoolExecutor
import cv2
import numpy as np
import logging
import time
from typing import List, Tuple, Callable, Optional

from PIL import Image

from poker_cnn_classifier import PokerImageClassifier, Poker
from poker_cnn_classifier_3class import PokerImageClassifier3Class


class RegionCaptureProcessor:
    def __init__(self,
                 regions: List[Tuple[int, int, int, int]],
                 on_image_ready: Optional[Callable[[dict], None]] = None,
                 logger: Optional[logging.Logger] = None,confidence_threshold=0.99,
                 table_data = None):
        self.regions = regions
        self.on_image_ready = on_image_ready
        self.logger = logger or logging.getLogger(__name__)
        self.frame_count = 0
        self._first_frame_saved = False
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.cnn = PokerImageClassifier()  # 每个子进程独立初始化 PokerImageClassifier
        self.cnn_3 = PokerImageClassifier3Class()

        self.has_seen_card_back = [False, False]
        self.first_card_back_time = [None, None]
        self.recongnize_cnt = 0
        self.last_white_ratio = [0,0]
        self.status = [0, 0]  # 0: 未看到卡牌背面, 1: 看到卡牌背面, 2: 看到卡牌正面
        self.confidence_threshold = confidence_threshold

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.to_be_save_images = []
        self.table_data = table_data
        self.websocket_client = None

    def _get_red_ratio(self, image, lower_red1=(0, 100, 100), upper_red1=(10, 255, 255),
                       lower_red2=(160, 100, 100), upper_red2=(180, 255, 255)):
        """统计红色像素占比（HSV颜色空间）"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        # 定义红色在HSV中的两个范围（色相环首尾）
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = cv2.bitwise_or(mask1, mask2)
        return np.count_nonzero(red_mask) / red_mask.size
    def _get_white_ratio(self, image, threshold=200):
        """检查图片中是否包含超过指定比例的白色像素"""
        # gray = np.mean(image, axis=2)  # 更快地转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        white_pixels = np.count_nonzero(gray > threshold)
        total_pixels = gray.size
        return white_pixels / total_pixels


    def _detect_image_with_index(self, args):
        image, index = args
        # 将BGR转换为RGB格式
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # 将numpy数组转换为PIL Image
        pil_image = Image.fromarray(image_rgb)
        predicted_class, confidence = self.cnn.detect_image(pil_image)
        return index, predicted_class, confidence

    def _detect_image_with_background(self, args):
        image, index = args
        # 将BGR转换为RGB格式
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # 将numpy数组转换为PIL Image
        pil_image = Image.fromarray(image_rgb)
        predicted_class, confidence = self.cnn_3.detect_image(pil_image)
        return index, predicted_class, confidence

    def detect_images(self, image1, image2):
        futures = [self.executor.submit(self._detect_image_with_index, (img, idx)) for idx, img in enumerate([image1, image2])]
        results = [future.result() for future in futures]
        index1, predicted_class1, confidence1 = results[0]
        index2, predicted_class2, confidence2 = results[1]
        return predicted_class1, confidence1, predicted_class2, confidence2

    def detect_images_background(self, image1, image2):
        futures = [self.executor.submit(self._detect_image_with_background, (img, idx)) for idx, img in
                   enumerate([image1, image2])]
        results = [future.result() for future in futures]
        index1, predicted_class1, confidence1 = results[0]
        index2, predicted_class2, confidence2 = results[1]
        return predicted_class1, confidence1, predicted_class2, confidence2

    def stop(self):
        self.executor.shutdown(wait=True)

    def process_frames(self, frames: List[np.ndarray]) -> List[List[np.ndarray]]:
        """
        批量处理帧集合，返回所有区域的子图像列表
        :param frames: 输入帧列表
        :return: 每个帧对应的子图像列表，结构为 [[frame1_regions], [frame2_regions], ...]
        """
        if not self._first_frame_saved:
            self._save_first_frame_validation(frames[:1])
            self._first_frame_saved = True
        all_sub_images = []

        for frame in frames:
            sub_imgs = self._capture_regions(frame)
            all_sub_images.append(sub_imgs)
        self.frame_count += len(frames)
        card1,card2 = self._handle_images(all_sub_images)
        if not card1:
            card1 = "?" if self.status[0]==1 else ""
        if not card2:
            card2 = "?" if self.status[1]==1 else ""
        self._trigger_callback(all_sub_images,[card1,card2])
        return all_sub_images

    def check_card_background(self, status, white_ratio1, white_ratio2, image1, image2):
        red_ration1 = self._get_red_ratio(image1)
        red_ration2 = self._get_red_ratio(image2)
        if red_ration1>0.20 and red_ration2>0.20 and white_ratio1<=0.063 and white_ratio2<=0.063:
            if status[0]!=1 and status[1]!=1:
                b1, c1, b2, c2 = self.detect_images_background(image1, image2)
                if c1>0.95 and b1==1 and c2>0.95 and b2==1:
                    self.first_card_back_time[0] = time.time()
                    self.has_seen_card_back[0] = True
                    self.logger.info(f"牌1 卡牌背面 {white_ratio1:.4f}  置信度:{c1:.4f}")

                    self.first_card_back_time[1] = time.time()
                    self.has_seen_card_back[1] = True
                    self.logger.info(f"牌2 卡牌背面 {white_ratio2:.4f}  置信度:{c2:.4f}")

                    status[0]=1
                    status[1]=1
                    # self.update_image_callback(image1, image2, None, None)
        else:
            if white_ratio1 <= 0.01:
                if status[0] != 0:
                    status[0] = 0
                    self.logger.info(f"牌1 无牌 {white_ratio1:.4f}")
            elif 0.60 <= white_ratio1:
                if status[0] != 2:
                    status[0] = 2
                    self.logger.info(f"牌1 其他背面 {white_ratio2:.4f}")

            if 0.063 < white_ratio1 < 0.60:
                if status[0] != 3:
                    status[0] = 3
                    # 卡牌正面
                    self.logger.info(f"牌1 卡牌正面 {white_ratio1:.4f}")

            if white_ratio2 <= 0.01:
                if status[1] != 0:
                    status[1] = 0
                    self.logger.info(f"牌2 无牌 {white_ratio2:.4f}")
            # elif 0.008 < white_ratio2 <= 0.025:
            #     if status[1] != 1:
            #         status[1] = 1

            elif 0.60 <= white_ratio2:
                if status[1] != 2:
                    status[1] = 2
                    self.logger.info(f"牌2 其他背面 {white_ratio2:.4f}")

            if 0.063 < white_ratio2 < 0.60:
                if status[1] != 3:
                    status[1] = 3
                    # 卡牌正面
                    self.logger.info(f"牌2 卡牌正面 {white_ratio2:.4f}")

        # if old_status0!=1 and status[0]==1 and old_status1!=1 and status[1]==1:

        card_front1 = 0.063 <= white_ratio1 < 0.60 and white_ratio1>red_ration1
        card_front2 = 0.063 <= white_ratio2 < 0.60 and white_ratio2>red_ration2

        return card_front1,card_front2


    def _capture_regions(self, frame: np.ndarray) -> List[np.ndarray]:
        """执行多区域截取"""
        sub_images = []
        for (x, y, w, h) in self.regions:
            validated_coords = self._validate_coordinates(frame, x, y, w, h)
            sub_img = self._crop_image(frame, *validated_coords)
            sub_images.append(sub_img)
        return sub_images

    def _validate_coordinates(self, 
                             frame: np.ndarray,
                             x: int, 
                             y: int, 
                             w: int, 
                             h: int) -> Tuple[int, int, int, int]:
        """验证并修正坐标范围"""
        height, width = frame.shape[:2]
        x = max(0, min(x, width - 1))
        y = max(0, min(y, height - 1))
        w = min(w, width - x)
        h = min(h, height - y)
        return (x, y, w, h)

    def _crop_image(self, 
                   frame: np.ndarray, 
                   x: int, 
                   y: int, 
                   w: int, 
                   h: int) -> np.ndarray:
        """执行图像截取操作"""
        return frame[y:y+h, x:x+w]

    def _save_first_frame_validation(self, sub_imgs: List[np.ndarray]):
        """保存首帧验证数据"""
        subfolder_path, formatted_time = self.get_sub_folder()
        self.logger.info(f"图片保存路径: {subfolder_path}")
        if not os.access(subfolder_path, os.W_OK):
            self.logger.error(f"没有写权限: {subfolder_path}")
            return
        total, used, free = shutil.disk_usage(subfolder_path)
        self.logger.info(
            f"磁盘空间: 总共 {total // (2 ** 30)} GB, 已用 {used // (2 ** 30)} GB, 剩余 {free // (2 ** 30)} GB")
        if free < 100 * 2 ** 20:  # 检查剩余空间是否小于 100 MB
            self.logger.error(f"磁盘空间不足: {subfolder_path}")
            return
        for i, img in enumerate(sub_imgs):
            path = os.path.join('images', f'{self.table_data["name"].replace(" ", "-")}-{self.table_data["table_id"]}', f'FF_{formatted_time}.jpg')
            pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            pil_img.save(path)  # 使用PIL库保存可避免OpenCV路径问题
            self.logger.info(f"首帧验证图像已保存:{path}")
    def _trigger_callback(self, all_sub_images: List[List[np.ndarray]],labels:List):
        """触发图像就绪回调"""
        if self.on_image_ready:
            self.on_image_ready({
                'timestamp': time.time(),
                'frame_count': self.frame_count,
                'images': all_sub_images,
                'labels':labels
            })

    @property
    def region_count(self) -> int:
        """获取配置的区域数量"""
        return len(self.crop_regions)

    def _handle_images(self, all_sub_images: List[List[np.ndarray]]):
        """处理图像数据"""
        start_time = time.time()
        if all_sub_images:
            idx = len(all_sub_images)-1
            while(idx>=0):
                sub_images = all_sub_images[idx]
                idx-=1
                image1, image2 = sub_images[0], sub_images[1]
                white_ratio1 = self._get_white_ratio(image1)
                white_ratio2 = self._get_white_ratio(image2)
                card_front1, card_front2 = self.check_card_background(self.status, white_ratio1, white_ratio2, image1,
                                                                      image2)
                if not card_front1 or not card_front2:
                    return "",""
                # 检查是否满足所有条件
                if (self.has_seen_card_back[0] and self.has_seen_card_back[1]
                        and self.first_card_back_time[1] is not None
                        and self.first_card_back_time[0] is not None
                ):
                    # 使用 ImageProcessor 处理图像识别
                    if self.recongnize_cnt > 10 and abs(self.last_white_ratio[0] - white_ratio1) < 0.01 and abs(
                            self.last_white_ratio[1] - white_ratio2) < 0.01:
                        continue;
                    if abs(self.last_white_ratio[0] - white_ratio1) >= 0.01 or abs(
                            self.last_white_ratio[1] - white_ratio2) >= 0.01:
                        self.recongnize_cnt = 0;
                    predicted_class1, confidence1, predicted_class2, confidence2 = self.detect_images(
                        image1, image2)
                    poker1 = Poker(predicted_class1)
                    poker2 = Poker(predicted_class2)

                    if confidence1 >= self.confidence_threshold and confidence2 >= self.confidence_threshold:
                        self.recongnize_cnt = 0
                        self.last_white_ratio = [white_ratio1, white_ratio2]
                        self.logger.info(f"牌1: {poker1.card} [{confidence1:.4f}]  - 牌2: {poker2.card} [{confidence2:.4f}] ")
                        # self.logger.info(f"识别图耗时: {(detection_time - start_time) * 1000:.2f} 毫秒")
                        # self.logger.info(f"总处理耗时: {(time.time() - start_time) * 1000:.2f} 毫秒")
                        if time.time() - self.first_card_back_time[0] < 26.0 and time.time()-self.first_card_back_time[1] < 26:
                            self.take_action(poker1, poker2)
                        else:
                            self.logger.warning("时间太长，不广播消息")
                        # self.update_image_callback(image1, image2, poker1, poker2)
                        # 重置状态变量
                        self.has_seen_card_back = [False, False]
                        self.first_card_back_time = [None, None]
                        self.save_images(poker1,poker2)
                        return poker1.card, poker2.card
                    else:
                        self.recongnize_cnt += 1
                        self.last_white_ratio = [white_ratio1, white_ratio2]
                        self.logger.info(f"识别失败，置信度不够 牌1: {poker1.card} [{confidence1:.4f}]{white_ratio1:.4F}  - 牌2: {poker2.card} [{confidence2:.4f}]{white_ratio2:.4F}  ")
                        self.to_be_save_images.append(sub_images)
                        # self.update_image_callback(image1, image2, poker1, poker2)
                else:
                    self.first_card_back_time = [None, None]
                    self.has_seen_card_back = [False, False]
                    return "",""
        return "", ""

    def take_action(self, poker1: Poker, poker2: Poker):
        self.send_broadcast_message(poker1.classic, poker2.classic)

    def send_broadcast_message(self, card1_index, card2_index, port=5005):
        # 发送广播消息
        start = time.time()
        message = f"{self.table_data['table_id']},{card1_index},{card2_index},{self.table_data['name']},{start}"

        if self.websocket_client and self.websocket_client.connected:
            try:
                self.websocket_client.send(message)
                self.logger.info(f"WS发消息: {message}")
            except Exception as e:
                self.logger.error(f"Failed to send WebSocket message: {e}")

        self.sock.sendto(message.encode(), ('<broadcast>', port))
        self.logger.info(f"广播消息: {message}")

    def get_sub_folder(self):
        now = datetime.now()
        image_folder = "images"
        # 格式化日期和时间
        date_str = now.strftime("%Y%m%d")
        hour_str = now.strftime("%H")
        formatted_time = now.strftime("%Y%m%d%H%M%S.%f")[:-3]
        # 创建子文件夹路径
        if self.table_data and self.table_data['name'] and self.table_data['table_id']:
            subfolder_path = os.path.join(image_folder, f'{self.table_data["name"].replace(" ", "-")}-{self.table_data["table_id"]}',
                                          date_str, hour_str)
        else:
            subfolder_path = os.path.join(image_folder, date_str, hour_str)
        os.makedirs(subfolder_path, exist_ok=True)
        if not os.path.exists(subfolder_path):
            self.logger.error(f"目录创建失败: {subfolder_path}")
            return None, None
        return subfolder_path,formatted_time
    def save_images(self,poker1,poker2):
        if self.to_be_save_images:

            index = 0
            subfolder_path, formatted_time = self.get_sub_folder()
            for sub_images in self.to_be_save_images:
                index += 1
                image1, image2 = sub_images[0], sub_images[1]
                pil_img = Image.fromarray(cv2.cvtColor(image1, cv2.COLOR_BGR2RGB))
                pil_img.save(f'{subfolder_path}\\{poker1.classic}_{formatted_time}_{index}.jpg')
                pil_img2 = Image.fromarray(cv2.cvtColor(image2, cv2.COLOR_BGR2RGB))
                pil_img2.save(f'{subfolder_path}\\{poker2.classic}_{formatted_time}_{index}.jpg')
            self.to_be_save_images.clear()

    def set_websocket_client(self, websocket_client):
        self.websocket_client = websocket_client

