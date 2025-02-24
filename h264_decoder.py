import time

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
        self.hw_decoder_fps = 0.0

    def init_decoder(self, sps: bytes, pps: bytes, width: int, height: int):
        """初始化解码器"""
        try:
            # 硬件解码器配置
            codec = av.Codec('h264_cuvid', 'r')
            self._parser = av.CodecContext.create(codec)

            # 硬件加速关键参数
            self._parser.options = {
                'gpu': '0',  # 指定GPU设备编号
                'surfaces': '8',  # 显存中解码表面数量
                'deint': 'adaptive',  # 反交错模式
                'cudacache': '1',  # 启用CUDA缓存
                'nvdec_preserve': '1',  # 保留显存优化
                'threads': '4',  # 解码线程数（建议为GPU流处理器数/8）
                'delay': '0',  # 零延迟模式
                'flags': '+low_delay+fast'  # 低延迟+快速解码标志
            }
            # Windows需添加的专用参数
            self._parser.options.update({
                'gpu': '0',
                'cuda_ctx': '1',  # 显式启用CUDA上下文
                'delay': '0',
                'flags': '+low_delay+auto_alt_ref',  # Windows专用低延迟模式
                'output_format': 'cuda',  # 强制CUDA输出格式
                'hwaccel_output_format': 'cuda'  # 硬件加速输出格式
            })
            # 调整解码参数（在init_decoder方法中）
            self._parser.options.update({
                'surfaces': '4',  # 减少显存占用
                'gpu_copy': '1',  # 启用显存到内存拷贝
                'max_width': '1920',  # 限制最大分辨率
                'max_height': '1080'
            })
            # 添加低延迟优化参数
            self._parser.options.update({
                'flags': '+low_delay+zerolatency+nonstrict',
                'strict': 'experimental',
                'max_delay': '1000000'  # 1秒最大延迟
            })

            self._is_hw_accel = True
            self.logger.info(f"成功启用NVIDIA硬件解码器，配置参数：{self._parser.options}")

        except Exception as e:
            self.logger.warning(f"Fallback to software decoder: {str(e)}")
            codec = av.Codec('h264', 'r')
            self._parser = av.CodecContext.create(codec)
            self._parser.options = {
                'threads': '4',  # 自动检测CPU核心数
                'flags': '+low_delay',
                'refs': '1',  # 减少参考帧数
                'err_detect': 'ignore_err',
                'enable': 'fast'  # 启用快速解码模式
            }
            self._parser.options.update({
                'skip_frame': 'default',  # 跳过非关键帧的解码
                'skip_loop_filter': 'all',  # 关闭环路滤波
                'error_resilient': '1',  # 增强容错能力
                'max_pixel': '2.5',  # 限制像素计算复杂度
                'lowres': '0'  # 保持原始分辨率但要确认是否可降级
            })
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
            start_time = time.time()
            try:
                frames = []
                for packet in self._parser.parse(nalu_data):
                    decoded_frames = self._parser.decode(packet)
                    frames.extend(
                        f.to_ndarray(format='bgr24')
                        for f in decoded_frames
                        if f is not None
                    )
                # 计算解码性能
                self.logger.debug(f"解码{len(frames)}帧耗时: {(time.time() - start_time)*1000:.2f} ms")
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
