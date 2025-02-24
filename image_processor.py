import cv2
import numpy as np
import logging
import time
from typing import List, Tuple, Callable, Optional

class RegionCaptureProcessor:
    """多区域图像捕获处理器"""
    def __init__(self, 
                 regions: List[Tuple[int, int, int, int]],
                 on_image_ready: Optional[Callable[[dict], None]] = None,
                 logger: Optional[logging.Logger] = None):
        """
        :param regions: 截取区域列表，格式 [(x, y, width, height), ...]
        :param on_image_ready: 图像处理完成回调函数
        :param logger: 日志记录器
        """
        self.crop_regions = regions
        self.on_image_ready = on_image_ready
        self.logger = logger or logging.getLogger(__name__)
        self.frame_count = 0
        self._first_frame_saved = False

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
        
        self._trigger_callback(all_sub_images)
        self.frame_count += len(frames)
        return all_sub_images

    def _capture_regions(self, frame: np.ndarray) -> List[np.ndarray]:
        """执行多区域截取"""
        sub_images = []
        for (x, y, w, h) in self.crop_regions:
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
            cv2.imwrite(f'first_frame_crop_{timestamp}.jpg', img)
        self.logger.debug("首帧验证图像已保存")

    def _trigger_callback(self, all_sub_images: List[List[np.ndarray]]):
        """触发图像就绪回调"""
        if self.on_image_ready:
            self.on_image_ready({
                'timestamp': time.time(),
                'frame_count': self.frame_count,
                'images': all_sub_images
            })

    @property
    def region_count(self) -> int:
        """获取配置的区域数量"""
        return len(self.crop_regions)
