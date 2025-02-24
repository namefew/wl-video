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
                 logger: Optional[logging.Logger] = None,confidence_threshold=0.995):
        """
        :param regions: 截取区域列表，格式 [(x, y, width, height), ...]
        :param on_image_ready: 图像处理完成回调函数
        :param logger: 日志记录器
        """
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
        self.status = [0, 0]  # 0: 未看到卡牌背景, 1: 看到卡牌背景, 2: 看到卡牌正面
        self.confidence_threshold = confidence_threshold

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def _get_white_ratio(self, image, threshold=200):
        """检查图片中是否包含超过指定比例的白色像素"""
        gray = np.mean(image, axis=2)  # 更快地转换为灰度图
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
        if 0.008<white_ratio1<=0.025 and 0.008<white_ratio2<=0.025:
            if status[0]!=1 and status[1]!=1:
                b1, c1, b2, c2 = self.detect_images_background(image1, image2)
                if c1>0.95 and b1==1 and c2>0.95 and b2==1:
                    self.first_card_back_time[0] = time.time()
                    self.has_seen_card_back[0] = True
                    self.logger.info(f"虎 卡牌背景 {white_ratio2:.4f}")
                    self.first_card_back_time[1] = time.time()
                    self.has_seen_card_back[1] = True
                    self.logger.info(f"龙 卡牌背景 {white_ratio1:.4f}")
                    status[0]=1
                    status[1]=1
                    # self.update_image_callback(image1, image2, None, None)
        else:
            if white_ratio1 <= 0.008:
                if status[0] != 0:
                    status[0] = 0
                    self.logger.info(f"龙 无牌 {white_ratio1:.4f}")
            elif 0.60 <= white_ratio1:
                if status[0] != 2:
                    status[0] = 2
                    self.logger.info(f"龙 其他背景 {white_ratio2:.4f}")

            if 0.025 < white_ratio1 < 0.60:
                if status[0] != 3:
                    status[0] = 3
                    # 卡牌正面
                    self.logger.info(f"龙 卡牌正面 {white_ratio1:.4f}")

            if white_ratio2 <= 0.008:
                if status[1] != 0:
                    status[1] = 0
                    self.logger.info(f"虎 无牌 {white_ratio2:.4f}")
            # elif 0.008 < white_ratio2 <= 0.025:
            #     if status[1] != 1:
            #         status[1] = 1

            elif 0.60 <= white_ratio2:
                if status[1] != 2:
                    status[1] = 2
                    self.logger.info(f"虎 其他背景 {white_ratio2:.4f}")

            if 0.025 < white_ratio2 < 0.60:
                if status[1] != 3:
                    status[1] = 3
                    # 卡牌正面
                    self.logger.info(f"虎 卡牌正面 {white_ratio2:.4f}")

        # if old_status0!=1 and status[0]==1 and old_status1!=1 and status[1]==1:

        card_front1 = 0.025 <= white_ratio1 < 0.60
        card_front2 = 0.025 <= white_ratio2 < 0.60

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
        timestamp = int(time.time())
        for i, img in enumerate(sub_imgs):
            os.mkdir("images",True)
            cv2.imwrite(f'images/first_frame_{timestamp}.jpg', img)
        self.logger.debug("首帧验证图像已保存")

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
                if not card_front1 and not card_front2:
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
                    detection_time = time.time()
                    poker1 = Poker(predicted_class1)
                    poker2 = Poker(predicted_class2)

                    if confidence1 >= self.confidence_threshold and confidence2 >= self.confidence_threshold:
                        self.recongnize_cnt = 0
                        self.last_white_ratio = [white_ratio1, white_ratio2]
                        self.logger.info(f"龙{poker1.card} [{confidence1:.4f}]  - 虎{poker2.card} [{confidence2:.4f}] ")
                        self.logger.info(f"识别图耗时: {(detection_time - start_time) * 1000:.2f} 毫秒")
                        self.logger.info(f"总处理耗时: {(time.time() - start_time) * 1000:.2f} 毫秒")
                        if time.time() - self.first_card_back_time[0] < 15.0 and time.time() - \
                                self.first_card_back_time[1] < 15:
                            self.take_action(poker1, poker2)
                        else:
                            self.logger.warning("时间太长，不进行下注")
                        # self.update_image_callback(image1, image2, poker1, poker2)
                        # 重置状态变量
                        self.has_seen_card_back = [False, False]
                        self.first_card_back_time = [None, None]
                        return poker1.card, poker2.card
                    else:
                        self.recongnize_cnt += 1
                        self.last_white_ratio = [white_ratio1, white_ratio2]
                        self.logger.info(f"识别失败，置信度不够 龙{poker1.card} [{confidence1:.4f}]  - 虎{poker2.card} [{confidence2:.4f}] ")
                        self.logger.info(f"识别图耗时: {(detection_time - start_time) * 1000:.2f} 毫秒")
                        self.logger.info(f"总处理耗时: {(time.time() - start_time) * 1000:.2f} 毫秒")
                        # self.update_image_callback(image1, image2, poker1, poker2)
                else:
                    self.first_card_back_time = [None, None]
                    self.has_seen_card_back = [False, False]
                    return "",""

    def take_action(self, poker1: Poker, poker2: Poker):
        if poker1.card_num == poker2.card_num:
            name = '和'
        elif poker1.card_num > poker2.card_num:
            name = '龙'
        else:
            name = '虎'
        self.logger.info(f"龙：{poker1.card}，虎：{poker2.card} 下注{name}")
        self.send_broadcast_message(poker1.classic, poker2.classic)

    def send_broadcast_message(self, card1_index, card2_index, port=5005):
        # 发送广播消息
        start = time.time()
        message = f"{card1_index},{card2_index},{start}"
        # if self.websocket_server:
        #     # 使用 call_soon_threadsafe 来安全地调用 asyncio 的协程
        #     self.websocket_server.loop.call_soon_threadsafe(
        #         asyncio.create_task, self.websocket_server.broadcast_message(message)
        #     )
        self.sock.sendto(message.encode(), ('<broadcast>', port))
        self.logger.info(f"广播消息: {message}")
