import time

from flv_parser import FLVParser
from media_play import yt
import requests
from concurrent.futures import ThreadPoolExecutor

class bt:

    def __init__(self, data_callback=None,image_callback=None,regions=None,logger=None, url='https://pl2079.gslxqy.com/live/v2flv_L01_2.flv'):
        self.logger = logger
        self.gn = None
        self.gA = None
        self.yA = data_callback  # 回调函数，用于处理解码后的数据
        self.image_callback = image_callback
        self.regions = regions
        self.config = {}  # 配置对象
        self.isPre = False  # 标记是否为预加载
        self.url = url  # 当前流的 URL
        self.en = True  # 标记是否是第一次接收到数据
        self.tn = 0  # 已接收的数据总长度
        self.QS = None  # 视频回调函数（可选）
        self.zS = None  # 音频回调函数（可选）
        self.sn = bytearray()  # 缓存未处理的数据块
        self.bA = []  # 存储事件监听器清理函数
        self.logger=logger

    def pn(self, e):
        if self.en:  # 如果是第一次接收到数据
            self.en = False  # 标记已处理首次数据
            self.logger.debug(f"Create MSEFlvDemuxer(), decryptionOption")  # 日志记录
            self.gn = FLVParser(logger=self.logger,regions=self.regions,on_image_ready=self.image_callback)
            self.gn.Aa = False  # 设置是否有音频
            self.gn.ma = True  # 设置是否有视频
            self.gn.da = 0  # 初始化解复用器的状态
            self.gn.ha = self.fn  # 绑定元数据回调
            self.gn.na = self.er  # 绑定媒体信息回调
            # self.gn.oa = self.tr  # 绑定错误回调
            # self.gn.la = self.ir  # 绑定完成回调
            self.gA = yt(logger=self.logger)  # 创建缓冲区管理器
            self.gA.ia(self.gn)  # 将解复用器绑定到缓冲区管理器
            self.gA.aA = self.vA  # 绑定视频数据回调
            self.gA.rA = self.SA  # 绑定音频数据回调

            # 智能缓冲区管理
        if len(self.sn) > 4 * 1024 * 1024:  # 4MB阈值
            keep = len(self.sn) // 2
            self.sn = self.sn[-keep:]
            self.tn -= (len(self.sn) - keep)

            # 链式内存视图处理
        chunks = [memoryview(self.sn), memoryview(e)]
        # 修改后（正确方式）
        merged_bytes = b''.join(chunks)  # 使用bytes类型进行合并
        merged_view = memoryview(merged_bytes)  # 转换为memoryview
        s = self.gn.ra(merged_bytes,self.tn-len(self.sn))
        # 直接操作视图切片
        self.sn = merged_view[s:]
        self.tn += len(e)

    # 设置视频回调函数
    @property
    def aA(self):
        return self.QS

    @aA.setter
    def aA(self, value):
        self.QS = value

    # 设置音频回调函数
    @property
    def rA(self):
        return self.zS

    @rA.setter
    def rA(self, value):
        self.zS = value

    # 音频数据回调
    def vA(self, e, t):
        if self.yA:
            t['isPre'] = self.isPre  # 标记是否为预加载
            t['url'] = self.url  # 设置 URL
            self.yA(e, t)  # 调用回调函数处理数据

    # 视频数据回调
    def SA(self, e, t):
        if self.yA:
            t['isPre'] = self.isPre  # 标记是否为预加载
            t['url'] = self.url  # 设置 URL
            self.yA(e, t)  # 调用回调函数处理数据

    # 元数据回调（预留方法）
    def fn(self, e, t):
        pass

    # 媒体信息回调
    def er(self, e):
        if self.yA:
            self.yA("mediaInfo", {**e, 'isPre': self.isPre, 'url': self.url})

    def direct_stream_reader(self, url):
        try:
            self.logger.info(f"Starting to read stream from {url}")
            response = requests.get(url, stream=True)
            response.raise_for_status()

            for chunk in response.iter_content(chunk_size=4096*4):
                if chunk:
                    start = time.time()
                    self.pn(chunk)
                    # self.logger.debug(f"Processed chunk in {(time.time() - start)*1000} ms")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error reading stream from {url}: {e}")
