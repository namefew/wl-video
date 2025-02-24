# import time
# from concurrent.futures import ThreadPoolExecutor
#
# import PyNvCodec as nvc
# import numpy as np
# from typing import Callable, Optional
#
# class H264Decoder2:
#     def __init__(self,
#                  logger,
#                  on_decoded: Callable[[list[np.ndarray]], None],
#                  on_error: Optional[Callable[[Exception], None]] = None):
#         self.logger = logger
#         self._on_decoded = on_decoded
#         self._on_error = on_error
#         self._executor = ThreadPoolExecutor(max_workers=1)
#         self._decoder = None
#         self._gpu_id = 0
#         self._frame_buffer = nvc.PyFrameUploader(1920, 1080, nvc.PixelFormat.RGB_PLANAR, self._gpu_id)
#
#     def init_decoder(self, sps: bytes, pps: bytes, width: int, height: int):
#         """实时流解码器初始化"""
#         try:
#             # 构造extradata (VPF要求格式)
#             extradata = self._build_extradata(sps, pps)
#
#             # 创建低延迟解码器
#             self._decoder = nvc.PyNvDecoder(
#                 width,
#                 height,
#                 nvc.PixelFormat.NV12,  # 硬件解码原生格式
#                 self._gpu_id,
#                 {'codec': 'h264', 's': f'{width}x{height}', 'low_latency': '1'}
#             )
#             self._decoder.SetDecodeParams({
#                 'num_decode_surfaces': '4',  # 减少显存占用
#                 'num_output_surfaces': '2',  # 输出缓冲
#                 'gpu_rate_control': '1',  # GPU频率提升
#                 'zero_copy': '1',  # 零拷贝模式
#                 'max_delay': '1000',  # 1ms最大延迟
#                 'flags': '+low_delay+zerolatency'
#             })
#             # 配置实时流参数
#             self._decoder.SetReconnectParams(3, 5000)  # 3次重连，间隔5秒
#             self._decoder.SetFrameRate(30)  # 预期帧率
#
#             self.logger.info("NVIDIA硬件解码器初始化成功（实时流模式）")
#
#         except Exception as e:
#             self.logger.error(f"解码器初始化失败: {str(e)}")
#             raise
#
#     def async_decode(self, nalu_data: bytes):
#         """提交实时流解码任务"""
#         def _wrap_packet():
#             try:
#                 # 添加H264起始码
#                 wrapped_data = b'\x00\x00\x00\x01' + nalu_data
#
#                 # 创建VPF兼容的数据包
#                 enc_packet = nvc.PacketData()
#                 enc_packet.data = wrapped_data
#                 enc_packet.pts = int(time.time() * 1e6)  # 使用时间戳
#
#                 # 硬件解码
#                 raw_frame = np.ndarray(shape=(1080,1920,3), dtype=np.uint8)
#                 success = self._decoder.DecodeFrameFromPacket(raw_frame, enc_packet)
#
#                 if success:
#                     # GPU->CPU异步传输
#                     self._frame_buffer.Upload(raw_frame)
#                     return [self._frame_buffer.Download()]
#                 return []
#
#             except Exception as e:
#                 self._handle_error(e)
#                 return []
#
#         future = self._executor.submit(_wrap_packet)
#         future.add_done_callback(
#             lambda f: self._on_decoded(f.result())
#         )
#
#     def _build_extradata(self, sps, pps):
#         """构建VPF要求的extradata格式"""
#         return b''.join([
#             bytes([0x01]), sps[1:4],
#             bytes([0xff, 0xe1]),
#             len(sps).to_bytes(2, 'big'), sps,
#             bytes([0x01]),
#             len(pps).to_bytes(2, 'big'), pps
#         ])
#
#     # 其他方法保持原有逻辑...
