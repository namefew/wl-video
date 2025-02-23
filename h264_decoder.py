import av
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional

class H264Decoder:
    """异步H264解码器（事件驱动模式）"""
    def __init__(self, 
                 logger, 
                 on_decoded: Callable[[list[np.ndarray]], None],
                 on_error: Optional[Callable[[Exception], None]] = None):
        """
        :param on_decoded: 解码完成回调 (frames: list[ndarray]) -> None
        :param on_error: 错误处理回调 (exception: Exception) -> None
        """
        self.logger = logger
        self._on_decoded = on_decoded
        self._on_error = on_error
        self._executor = ThreadPoolExecutor(max_workers=1)  # 单线程解码保证顺序
        self._parser = None
        self._is_hw_accel = False

    def init_decoder(self, sps: bytes, pps: bytes, width: int, height: int):
        """初始化解码器"""
        try:
            # 优先尝试硬件解码
            codec = av.Codec('h264_cuvid', 'r')
            self._parser = av.CodecContext.create(codec)
            self._is_hw_accel = True
            self.logger.info("Initialized NVIDIA CUVID hardware decoder")
        except Exception as e:
            self.logger.warning(f"Fallback to software decoder: {str(e)}")
            codec = av.Codec('h264', 'r')
            self._parser = av.CodecContext.create(codec)
            self._is_hw_accel = False

        # 构建extradata
        extradata = bytes([0x01]) + sps[1:4]
        extradata += bytes([0xff, 0xe1]) 
        extradata += len(sps).to_bytes(2, 'big') + sps
        extradata += bytes([0x01]) 
        extradata += len(pps).to_bytes(2, 'big') + pps
        
        self._parser.extradata = extradata
        self._parser.width = width
        self._parser.height = height

    def async_decode(self, nalu_data: bytes):
        """提交异步解码任务"""
        if not self._parser:
            raise RuntimeError("Decoder not initialized")
        
        def _decode_task():
            try:
                frames = []
                for packet in self._parser.parse(nalu_data):
                    decoded_frames = self._parser.decode(packet)
                    frames.extend(
                        f.to_ndarray(format='bgr24') 
                        for f in decoded_frames 
                        if f is not None
                    )
                return frames
            except Exception as e:
                self._handle_error(e)
                return []
        
        future = self._executor.submit(_decode_task)
        future.add_done_callback(
            lambda f: self._on_decoded(f.result())
        )

    def _handle_error(self, error: Exception):
        self.logger.error(f"Decoding error: {str(error)}")
        if self._on_error:
            self._on_error(error)

    def release(self):
        """释放资源"""
        if self._parser:
            self._parser.close()
        self._executor.shutdown()
