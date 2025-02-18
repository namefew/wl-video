import logging
import struct
import subprocess

import cv2
import numpy as np
from amf_parser import parse_script
from decode_module import DecodeModule
from data_view import DataView
from decode_util import cs,St,unsigned_right_shift_32

class FLVParser:  #ht
    """优化的FLV解析器"""
    def __init__(self, e=None, t='all', i=None, logger=None):
        if i is None:
            i = [6]
        if e is None:
            e =  {
                "match": True,
                "ea": 9,
                "zr": 9,
                "qr": True,
                "Jr": True
            }

        self.jr = None
        self.meta_data = None # 视频元数据
        self.decoder = DecodeModule()
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)
        self.Zs = "MSEFlvDemuxer"  # 类名标识符
        self.fi = "A.It"  # 日志模块标识符
        self.Xs = self.onError  # 错误回调函数
        self.er = self.onMediaInfo  # 媒体信息回调函数
        self.tr = self.onTrackMetadata  # 轨道元数据回调函数
        self.ir = self.onDataAvailable  # 数据可用回调函数
        self.sr = self.onTrackMetadata  # 解密回调函数
        self.rr = self.onMediaInfo  # 音视频数据回调函数
        self.ar = True  # 标记是否是第一次解析
        self.nr = False  # 标记是否正在解析数据块
        self.lr = False  # 标记音频轨道状态
        self.hr = False  # 标记视频轨道状态
        self.ur = False  # 标记是否有可用的视频数据
        self.dr = False  # 标记是否有可用的音频数据
        self.cr = None  # 存储脚本数据
        self.Ar = None  # 音频配置
        self.mr = None  # 视频配置
        self.pr = 4  # NALU 长度大小减一
        self.gr = 0  # 时间戳基准值
        self.vr = 1e3  # 时间缩放因子
        self.yr = 0  # 持续时间（毫秒）
        self.Dr = False  # 标记是否已设置持续时间
        self.Sr = {
            'fixed': True,
            'xs': 23.976,
            'Is': 23976,
            'bs': 1e3
        }  # 固定帧率配置
        self.wr = [5500, 11025, 22050, 44100, 48e3]  # 支持的采样率
        self.Mr = [96e3, 88200, 64e3, 48e3, 44100, 32e3, 24e3, 22050, 16e3, 12e3, 11025, 8e3, 7350]  # AAC 编码比特率
        self.Er = [44100, 48e3, 32e3, 0]  # MP3 编码比特率
        self.br = [22050, 24e3, 16e3, 0]  # MP3 编码比特率
        self.Ir = [11025, 12e3, 8e3, 0]  # MP3 编码比特率
        self.Fr = [0, 32, 64, 96, 128, 160, 192, 224, 256, 288, 320, 352, 384, 416, 448, -1]  # MPEG-4 AAC 比特率
        self.Tr = [0, 32, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 384, -1]  # MPEG-4 AAC 比特率
        self.Cr = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, -1]  # MPEG-4 AAC 比特率
        self.Pr = {
            'type': "video",
            'id': 1,
            'kr': 0,
            'Vr': [],
            'length': 0
        }  # 视频缓冲区
        self.Ur = {
            'type': "audio",
            'id': 2,
            'kr': 0,
            'Vr': [],
            'length': 0
        }  # 音频缓冲区
        self.Rr = 0  # 视频开始时间戳
        self.Br = 0  # 关键帧时间戳
        self.Lr = 0  # 上一个关键帧时间戳
        self.Nr = 0  # 上一个 B 帧时间戳
        self.videoDuration = 0  # 视频持续时间
        self._r = 0  # B 帧延迟计数器
        self.Or = [6]  # 支持的 NALU 类型

        # 日志记录构造函数参数
        logging.debug(f"constructor, decryptionOption: {t}")

        # 设置解密选项
        if t == "All":
            self.Hr = True
            self.Wr = True
        elif t == "Audio":
            self.Hr = True
            self.Wr = False
        elif t == "Video":
            self.Hr = False
            self.Wr = True
        elif t == "None" or t is None:
            self.Hr = False
            self.Wr = False

        self._r = e['zr']  # 文件头大小
        self.Gr = e['qr']  # 是否包含音频
        self.jr = e['Jr']  # 是否包含视频
        self.Kr = St()  # 创建解复用器实例
        self.Kr.has_audio = self.Gr
        self.Kr.has_video = self.jr

        # 检查字节序
        self.Ti = self._check_byte_order()

        self.Or = i or []  # 支持的 NALU 类型列表

        self.nalu_file = open('temp_nalus.bin', 'ab')

    def _check_byte_order(self):
        e = bytearray(2)
        e[0] = 0x01  # 设置为 256 的小端表示
        return int.from_bytes(e, byteorder='little') == 256


    # 设置解密选项
    def ta(self, e, t):
        logging.debug(f"setDecrypt audio: {e}, video: {t}")
        self.Hr = e
        self.Wr = t

    # 绑定解析方法
    def ia(self, e):
        e.sa = self.ra
        return self

    # Getter 和 Setter 方法
    @property
    def aa(self):
        return self.sr

    @aa.setter
    def aa(self, e):
        self.sr = e

    @property
    def na(self):
        return self.er

    @na.setter
    def na(self, e):
        ## TODO 现在强绑在onMediaInfo上，后续优化
        if not self.er:
            self.er = e

    @property
    def oa(self):
        return self.tr

    @oa.setter
    def oa(self, e):
        self.tr = e

    @property
    def la(self):
        return self.ir

    @la.setter
    def la(self, e):
        self.ir = e

    @property
    def ha(self):
        return self.Xs

    @ha.setter
    def ha(self, e):
        self.Xs = e

    @property
    def ua(self):
        return self.rr

    @ua.setter
    def ua(self, e):
        self.rr = e

    @property
    def da(self):
        return self.gr

    @da.setter
    def da(self, e):
        self.gr = e

    @property
    def ca(self):
        return self.yr

    @ca.setter
    def ca(self, e):
        self.Dr = True
        self.yr = e
        self.Kr.duration = e

    @property
    def Aa(self):
        return self.Gr

    @Aa.setter
    def Aa(self, e):
        self.lr = True
        self.Gr = e
        self.Kr.has_audio = e

    @property
    def ma(self):
        return self.jr

    @ma.setter
    def ma(self, e):
        self.hr = True
        self.jr = e
        self.Kr.has_video = e

    # 重置解复用器实例
    def pa(self):
        self.Kr = St()

    # 检查是否有可用的数据
    def ga(self):
        if self.lr or self.hr:
            return self.ur or self.dr
        elif self.Gr and self.jr:
            return self.ur and self.dr
        elif self.Gr and not self.jr:
            return self.ur
        else:
            return not (self.Gr or not self.jr) and self.dr

    # 重置音视频缓冲区
    def fa(self):
        self.Pr = {
            'type': "video",
            'id': 1,
            'kr': 0,
            'Vr': [],
            'length': 0
        }
        self.Ur = {
            'type': "audio",
            'id': 2,
            'kr': 0,
            'Vr': [],
            'length': 0
        }
    def onError(self,msg):
        self.logger.error("onError",msg)
    def onMediaInfo(self,*args):
        self.logger.info("onMediaInfo %s",*args)
    def onTrackMetadata(self,*info):
        self.logger.info("onTrackMetadata %s",*info)
    def onDataAvailable(self,*info):
        self.logger.info("onDataAvailable %s",*info)

    def ra(self, e, t):
        if not (self.Xs and self.er and self.sr and self.rr):
            raise ValueError(
                "Flv: onError & onMediaInfo & onTrackMetadata & onDataAvailable callback must be specified")

        o = 0
        a = not self.Ti

        if t == 0:
            if len(e) <= 13:
                return 0
            o = self.flv_header(e)['zr']

        if self.ar:
            self.ar = False
            if t + o != self._r:
                logging.debug(f"First time parsing but chunk byteStart invalid!")
            if struct.unpack_from('>I' if a else '<I', e, o)[0] & 0xFFFFFF != 0:
                logging.debug("PrevTagSize0 !== 0 !!!")
            o += 4

        while o < len(e):
            self.nr = True
            i = DataView(e, o)

            if o + 11 + 4 > len(e):
                break

            s = i.get_uint8(0)
            r = i.get_uint32(0) & 0xFFFFFF

            if o + 11 + r + 4 > len(e):
                break

            if s not in [8, 9, 18]:
                logging.debug(f"Unsupported tag type {s}, skipped")
                o += 11 + r + 4
                continue

            n = i.get_uint8(4)
            l = i.get_uint8(5)
            h = i.get_uint8(6) | l << 8 | n << 16 | i.get_uint8(7) << 24

            if struct.unpack_from('>I' if a else '<I', e, o + 7)[0] & 0xFFFFFF != 0:
                logging.debug("Meet tag which has StreamID != 0!")

            d = o + 11

            if s == 8:
                self.parse_audio_tag(e, d, r, h)
            elif s == 9:
                self.parse_video_tag(e, d, r, h, t + o)
            elif s == 18:
                self.parse_script_data(e, d, r)

            u = struct.unpack_from('>I' if a else '<I', e, o + 11 + r)[0]
            if u != 11 + r:
                logging.debug(f"Invalid PrevTagSize {u}")

            o += 11 + r + 4

        # if self.ga() and self.nr:
        i = self.Ur
        s = self.Pr
        if (i is not None and len(i)) or (s is not None and len(s)):
            self.rr(self.Ur, self.Pr)
        return o
    def parse_flv_tags(self, data, byte_start):
        return self.ra(data,byte_start)

    def parse_script_data(self, data, data_start, data_size):
        """处理脚本数据"""
        self.logger.debug("Enter ScriptData")  # 记录进入脚本数据处理的日志

        # 解析脚本数据（假设 et._i 是解析 FLV 脚本数据的方法）
        s = parse_script(data, data_start, data_size)
        self.logger.debug(f"ScriptData: {s}")
        # 检查是否存在 onMetaData 字段
        if "onMetaData" in s:
            meta_data = s["onMetaData"]  # 获取 onMetaData 对象

            # 检查 onMetaData 是否为有效对象
            if meta_data is None or not isinstance(meta_data, dict):
                self.logger.debug("Invalid onMetaData structure!")
                return
            self.meta_data = meta_data  # 保存当前脚本数据



    def flv_header(self,data):
        return self.probe(data)

    @staticmethod
    def probe(data):
        """探测 FLV 文件格式"""
        # 将输入数据转换为字节数组
        t = bytearray(data)
        # 初始化结果字典
        i = {  'match': False,'header_size': 0}
        # 检查文件头是否为 "FLV"
        if t[0] != 0x46 or t[1] != 0x4C or t[2] != 0x56 or t[3] != 0x01:
            return i
        # 获取文件头信息
        has_audio = (t[4] & 0x04) >> 2 != 0  # 检查是否有音频数据
        has_video = (t[4] & 0x01) != 0  # 检查是否有视频数据
        # 计算文件头中的偏移量
        def get_offset(e):
            return (e[5] << 24) | (e[6] << 16) | (e[7] << 8) | e[8]
        header_size = get_offset(t)
        # 检查偏移量是否有效
        if header_size < 9:
            return i
        # 返回探测结果
        return {
            'match': True,
            'header_size': header_size,
            'has_audio': has_audio,
            'has_video': has_video,
            'ea': header_size, # 文件头大小
            'zr': header_size, #文件头大小
            'qr': has_audio, #是否有音频数据
            'Jr': has_video #是否有视频数据
        }


    def parse_audio_tag(self, data, tag_data_start, tag_data_size, timestamp):
        """智能解析Tag"""

        return None


    def parse_video_tag(self, data, offset, size, timestamp, byte_start):
        """智能解析Tag"""
        return self.ya(data,offset,size,timestamp,byte_start)

    def ya(self, data, t, i, s, o):
        if i <= 1:
            logging.debug("Flv: Invalid video packet, missing VideoData payload!")
            return

        if self.hr and not self.jr:
            return

        a = data[t]  # 读取视频数据的第一个字节
        r = (240 & a) >> 4  # 提取帧类型（高4位）
        n = 15 & a  # 提取编解码器类型（低4位）

        # 检查编解码器类型是否为 H.264
        if n == 7:
            self.La(data, t + 1, i - 1, s, o, r)  # 处理 H.264 视频帧
        else:
            self.Xs("Flv: Unsupported codec in video frame: {}".format(n))  # 记录不支持的编解码器类型

    def decode_h264(self, data, offset, size, timestamp, byte_start, frame_type):
        return self.La(data,offset,size,timestamp,byte_start,frame_type)
    def La(self, data, offset, size, timestamp, byte_start, frame_type):
        if size < 4:
            logging.debug("Flv: Invalid AVC packet, missing AVCPacketType or/and CompositionTime")
            return

        r = self.Ti  # 字节序标志（True 表示大端，False 表示小端）
        n = DataView(data, offset, r)  # 创建 DataView 对象以读取 AVC 数据
        l = n.get_uint8(0)  # 获取 AVCPacketType
        h = (0xFFFFFF & n.get_uint32(0))  # 获取 CompositionTime

        # 处理不同的 AVCPacketType
        if l == 0:
            # AVCPacketType 为 0，表示 AVC 序列参数集（SPS）或参数集（PPS）
            self.Na(data, offset + 4, size - 4)
        elif l == 1:
            # AVCPacketType 为 1，表示 AVC 原始帧数据
            self.Qa(data, offset + 4, size - 4, timestamp, byte_start, frame_type, h)
        elif l != 2:
            # AVCPacketType 不为 0 或 1，表示无效的视频数据类型
            self.Xs("Flv: Invalid video packet type {}".format(l))

    def Na(self, e, t, length):
        if length < 7:
            logging.debug("IFlv: Invalid AVCDecoderConfigurationRecord, lack of data!")
            return

        a = self.mr  # 当前视频轨道信息
        r = self.Pr  # 当前视频缓冲区
        n = self.Ti  # 字节序标志（True 表示大端，False 表示小端）
        l = DataView(e, t, n)  # 创建 DataView 对象以读取 AVC 数据

        # 初始化视频轨道信息（如果尚未初始化）
        if a:
            if hasattr(a, '_a'):
                logging.debug("Found another AVCDecoderConfigurationRecord!")
        else:
            if not self.jr and not self.hr:
                self.jr = True
                self.Kr.has_video = True
            dd = self.mr = {
                'type': "",
                'id': 0,
                'xa': 0,
                'duration': 0,
                'Oa': 0,
                'Ha': 0,
                'Wa': 0,
                '$a': 0,
                'profile': "",
                'level': "",
                'za': 0,
                'Ls': 0,
                'Ga': {
                    'width': 0,
                    'height': 0
                },
                'qa': {
                    'fixed': False,
                    'xs': 0,
                    'bs': 0,
                    'Is': 0
                },
                'codec': "",
                'ja': "",
                'Ja': bytearray(0),
                '_a': bytearray(0),
                'Pa': 0,
                'Ca': bytearray(e[t:t + length])
            }
            dd['type'] = "video"
            dd['id'] = r['id']
            dd['xa'] = self.vr
            dd['duration'] = self.yr

        # 解析 AVCDecoderConfigurationRecord
        h = l.get_uint8(0)  # 配置版本
        d = l.get_uint8(1)  # AVCProfileIndication

        # 检查配置版本和 AVCProfileIndication 是否有效
        if h != 1 or d == 0:
            self.Xs("Flv: Invalid AVCDecoderConfigurationRecord")
            return

        # 获取 NaluLengthSizeMinusOne
        self.pr = 1 + (3 & l.get_uint8(4))
        if self.pr != 3 and self.pr != 4:
            self.Xs(f"Flv: Strange NaluLengthSizeMinusOne: {self.pr - 1}")
            return

        # 获取 SPS（Sequence Parameter Set）数量
        u = 31 & l.get_uint8(5)
        if u == 0:
            self.Xs("Flv: Invalid AVCDecoderConfigurationRecord: No SPS")
            return
        if u > 1:
            logging.debug(f"Flv: Strange AVCDecoderConfigurationRecord: SPS Count = {u}")

        c = 6  # 当前解析位置
        p = bytearray([0, 0, 0, 1])  # NALU 分隔符
        m = bytearray(0)  # 用于存储合并后的 SPS 数据

        # 解析每个 SPS
        for _ in range(u):
            s = l.get_uint16(c)  # 获取 SPS 长度
            c += 2
            if s == 0:
                continue
            o = e[t + c:t + c + s]  # 获取 SPS 数据
            r = bytearray(m + p + o)  # 合并 SPS 数据和分隔符
            m = r
            c += s

            # 解析 SPS 数据
            h = cs(o)
            if _ != 0:
                continue

            # 更新视频轨道信息
            dd['Oa'] = h['Ts']['width']  # 显示宽度
            dd['Ha'] = h['Ts']['height']  # 显示高度
            dd['Wa'] = h['Cs']['width']  # 编码宽度
            dd['$a'] = h['Cs']['height']  # 编码高度
            dd['profile'] = h['fs']  # 配置文件
            dd['level'] = h['vs']  # 级别
            dd['za'] = h['ys']  # 限制标志
            dd['Ls'] = h['Ss']  # 序列参数集 ID
            dd['Ga'] = h['Fs']  # 帧大小
            dd['qa'] = h['Es']  # 帧速率信息

            # 如果帧速率信息无效，则使用默认帧速率信息
            if not h['Es']['fixed'] or h['Es']['Is'] == 0 or h['Es']['bs'] == 0:
                dd['qa'] = self.Sr

            # 计算帧间隔
            d = dd['qa']['bs']
            u = dd['qa']['Is']
            dd['Pa'] = dd['xa'] * (d / u)

            # 构建编码器字符串
            f = o[1:4]
            y = "avc1."
            for ii in f:
                ti = hex(ii)[2:]
                if len(ti) < 2:
                    ti = "0" + ti
                y += ti
            dd['codec'] = y
            dd['ja'] = "h264"

            # 更新媒体信息
            b = self.Kr
            b.width = dd['Oa']
            b.height = dd['Ha']
            b.xs = dd['qa']['xs']
            b.profile = dd['profile']
            b.level = dd['level']
            b.Bs = h['Ds']
            b.Ls = h['ws']
            b.Ns = dd['Ga']['width']
            b.Qs = dd['Ga']['height']
            b.audio_codec = y
            if b.has_audio:
                if b.audio_codec:
                    b.mime_type = f'video/x-flv; codecs="{b.audio_codec},{b.audio_codec}"'
            else:
                b.mime_type = f'video/x-flv; codecs="{b.audio_codec}"'
            if b.Ps() or True: # 如果媒体信息未初始化，先强制进去看看
                self.er(b)  # 发送媒体信息

        # 获取 PPS（Picture Parameter Set）数量
        f = l.get_uint8(c)
        if f == 0:
            self.Xs("Flv: Invalid AVCDecoderConfigurationRecord: No PPS")
            return
        if f > 1:
            logging.debug(f"Flv: Strange AVCDecoderConfigurationRecord: PPS Count = {f}")
        c += 1

        # 解析每个 PPS
        for _ in range(f):
            i1 = l.get_uint16(c)  # 获取 PPS 长度
            c += 2
            if i1 == 0:
                continue
            s = e[t + c:t + c + i1] # 获取 PPS 数据
            r = bytearray(m + p + s)  # 合并 PPS 数据和分隔符
            m = r
            c += i1

        # 更新视频轨道信息
        dd['Ja'] = m
        dd['_a'][0:length] = bytearray(e[t:t + length])
        self.logger.debug(f"Parsed AVCDecoderConfigurationRecord{dd}")

        # 触发 onDataAvailable 回调（如果有新的音视频数据）
        if self.Ur is not None and len(self.Ur) or self.Pr is not None and len(self.Pr):
            self.rr(self.Ur, self.Pr)
        self.nr = False
        self.sr("video", dd)  # 发送轨道元数据


    #检查是否有可用的数据 //TODO 这里有问题，self.dr没有 同步赋值
    def ga(self):
        if self.lr or self.hr:
            return self.ur or self.dr
        elif self.Gr and self.jr:
            return self.ur and self.dr
        elif self.Gr and not self.jr:
            return self.ur
        else:
            return not (self.Gr or not self.jr) and self.dr

    def Qa(self, data, offset, size, timestamp, byte_start, frame_type, r):
        l = DataView(data, offset, size)  # 创建 DataView 对象以读取 AVC 数据
        frames = []  # 用于存储解析后的 NALU 单元
        d = 0  # 总数据长度
        u = 0  # 当前偏移量

        c = self.pr  # NALU 头长度
        p = self.gr + timestamp  # 当前时间戳
        m = frame_type == 1  # 标记是否为关键帧
        f = ""  # NALU 类型描述符
        y = 0  # 北京时间毫秒数

        while u < size:
            if u + 4 >= size:
                logging.debug(f"Malformed Nalu near timestamp {p}, offset = {u}, dataSize = {size}")
                break

            s = l.get_uint32(u,False)  # 读取 NALU 大小
            if c == 3:
                s = unsigned_right_shift_32(s, 8)  # 如果 NALU 头长度为 3，则右移 8 位以获取正确的大小

            if s > size - c:
                logging.debug(f"Malformed Nalus near timestamp {p}, NaluSize > DataSize!")
                return

            nalu_type = l.get_uint8(u + c) & 31  # 获取 NALU 类型

            if nalu_type == 5:
                m = True
                self.Br = p
                self.Rr = p + r

            if self.videoDuration == 0 and self.Br != 0 and p != self.Br:
                self.videoDuration = p - self.Br

            if nalu_type == 5:
                f = "I"
            elif nalu_type == 1:
                if abs(p - self.videoDuration - self.Br) < 2 and r != 0 and not abs(
                        p + r - self.videoDuration - self.Rr) < 2:
                    self._r = (r + p - self.Rr) / self.videoDuration - 1
                    if self._r < 0.1:
                        self._r = 0
                    f = "P"
                    self.Rr = r + p
                elif r > 0:
                    if self._r > 0:
                        self._r -= 1
                        if self._r < 0.1:
                            self._r = 0
                    f = "B"
                    if self._r <= 0:
                        self.Br = p
                        self._r = 0
                else:
                    f = "P"
            else:
                f = "P"
            a = bytearray(data[offset + u:offset + u + c + s])  # 读取 NALU 数据
            b = a[c] & 255  # 获取 NALU 数据的第一个字节

            if (b == 65 or b == 97 or b == 101) :
                # data = bytearray(rt.buffer[:a.length])
                # data[:] = a[:]
                # self.at(0, c, s)
                # a[:] = data[:]
                data = bytearray(self.decoder.memory[0:len(a)])
                data[:] = a[:]
                self.decoder.c(0,c, s )
                a[:] = data[:]

            if b == 6 and a[c + 1] == 5 and s == 29:
                data1 = a[c + 2:c + 4]
                offset1 = (data1[1] << 8) + data1[0]
                i = a[c + 4:c + 4 + 16].decode('utf-8')
                if offset1 == 24 and i == "BeiJingTimeMsec\0":
                    x = 8
                    data2 = a[c + 20:c + 20 + x]
                    i = 0
                    for jj in range(x):
                        i += data2[jj] * (2 ** (8 * jj))
                    y = i

            if b not in self.Or:
                data2 = {
                    'type': byte_start,
                    'data': a
                }
                frames.append(data2)
                d += len(a)

            u += (c + s)

        if frames:
            e3 = self.Pr  # 获取当前视频缓冲区
            t4 = {
                'units': frames,  # NALU 单元数组
                'length': d,  # 总数据长度
                'Ka': m,  # 是否为关键帧
                'ka': p,  # 时间戳
                'Ya': r,  # 帧时长
                'Za': f,  # 帧类型描述符
                'Va': p + r,  # 结束时间戳
                'qs': 0,  # 关键帧索引（仅在关键帧时设置）
                'Xa': y  # 北京时间毫秒数
            }

            if m:
                t4['qs'] = byte_start

            e3['Vr'].append(t4)
            e3['length'] += d

            # 写入 NALU 单元到文件
            for frame in frames:
                nalu_data = frame['data']
                self._write_nalu_to_file(nalu_data)

            # 触发 onDataAvailable 回调（如果有新的音视频数据）
            if (self.Ur is not None and len(self.Ur)) or (self.Pr is not None and len(self.Pr)):
                self.rr(self.Ur, self.Pr)
            self.nr = False

    def _write_nalu_to_file(self, nalu_data):
        if self.nalu_file is not None:
            self.nalu_file.write(nalu_data)


def convert_nalus_to_h264(nalu_units, output_file):
    with open(output_file, 'wb') as f:
        for unit in nalu_units:
            f.write(unit['data'])

    # 使用 ffmpeg 将 NALU 单元转换为 H.264 编码格式
    h264_output_file = 'output.h264'
    command = [
        'ffmpeg', '-f', 'h264', '-i', output_file, '-c', 'copy', h264_output_file
    ]
    subprocess.run(command, check=True)

    return h264_output_file

def write_h264_to_mp4(h264_file, mp4_file):
    command = [
        'ffmpeg', '-i', h264_file, '-c', 'copy', mp4_file
    ]
    subprocess.run(command, check=True)