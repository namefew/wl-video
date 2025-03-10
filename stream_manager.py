import threading
import time

from websocket import WebSocket, WebSocketConnectionClosedException

from flv_parser import FLVParser
from media_play import yt
import requests

class bt:

    def __init__(self, data_callback=None,image_callback=None,regions=None,logger=None, url='https://pl2079.gslxqy.com/live/v2flv_L01_2.flv',table_data=None):
        self.logger = logger
        self.gn = None
        self.gA = None
        self.yA = data_callback  # 回调函数，用于处理解码后的数据
        self.image_callback = image_callback
        self.regions = regions
        self.table_data = table_data
        self.config = {}  # 配置对象
        self.isPre = False  # 标记是否为预加载
        self.url = url  # 当前流的 URL
        self.en = True  # 标记是否是第一次接收到数据
        self.tn = 0  # 已接收的数据总长度
        self.QS = None  # 视频回调函数（可选）
        self.zS = None  # 音频回调函数（可选）
        self.sn = bytearray()  # 缓存未处理的数据块
        self.bA = []  # 存储事件监听器清理函数
        self.running = True
        self.logger=logger

        self.en = False  # 标记已处理首次数据
        self.logger.debug(f"Create MSEFlvDemuxer(), decryptionOption")  # 日志记录
        self.gn = FLVParser(logger=self.logger, regions=self.regions, on_image_ready=self.image_callback,
                            table_data=self.table_data)
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
        self.ws = None
        self._start_websocket_client()

    def _start_websocket_client(self):
        # 启动守护线程
        threading.Thread(target=self._run_forever, daemon=True).start()

    def connect(self):
        try:
            url = 'ws://localhost:8765'
            self.logger.info(f"Connecting to {url}")
            self.ws = WebSocket()
            self.ws.connect(url)
            self.logger.info(f"WebSocket connected!")
            self.gn.set_websocket_client(self.ws)
            return True
        except Exception as e:
            self.logger.warning(f"WS connect failed: {e}")
        return False

    def _run_forever(self):
        while self.running:
            if not self.ws or not self.ws.connected:
                self.connect()
            else:
                try:
                    message = self.ws.recv()
                    self.logger.info(f"Received: {message}")
                    # 在这里处理接收到的消息
                except WebSocketConnectionClosedException:
                    # self.logger.warning("Connection closed, reconnecting...")
                    self.ws = None  # 重置 ws 对象
                except Exception as e:
                    # self.logger.error(f"Error receiving message: {e}")
                    self.ws = None  # 重置 ws 对象
            time.sleep(1)

    def pn(self, e):


        # 合并新旧数据块
        t = self.tn - len(self.sn)
        i = bytearray(len(self.sn) + len(e))
        i[:len(self.sn)] = self.sn  # 设置旧数据
        i[len(self.sn):] = e  # 追加新数据

        # 解析合并后的数据
        s = self.gn.ra(i, t)
        self.sn = bytearray()  # 清空缓存
        if s < len(i):
            self.sn = i[s:]  # 保留未处理的数据
        self.tn += len(e)  # 更新已接收的数据总长度


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
        if not self.running:
            if self.ws and self.ws.connected:
                self.ws.close()
            return
        try:
            self.logger.info(f"Starting to read stream from {url}")
            response = requests.get(url, stream=True,timeout=10)
            response.raise_for_status()

            for chunk in response.iter_content(chunk_size=4096 * 4):
                if not self.running:
                    break
                if chunk:
                    # start = time.time()
                    self.pn(chunk)
                    # self.logger.debug(f"Processed chunk in {(time.time() - start)*1000} ms")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error reading stream from {url}: {e}")
            self.clear_data()  # 清空数据
            self.reconnect(url)  # 重新连接
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout while reading stream from {url}")
            self.clear_data()  # 清空数据
            self.reconnect(url)  # 重新连接
        except Exception as e:
            self.logger.error(f"Unexpected error while reading stream from {url}: {e}")
            self.clear_data()  # 清空数据
            self.reconnect(url)  # 重新连接
    def stop(self):
        self.running = False
        if self.ws and self.ws.connected:
            self.ws.close()
        self.clear_data()
        self.logger.info("处理视频流已被终止！！")
    def clear_data(self):
        self.sn = bytearray()  # 清空缓存未处理的数据块
        self.tn = 0  # 重置已接收的数据总长度
        self.en = True  # 标记为第一次接收到数据
        self.isPre = False  # 标记为非预加载

    def reconnect(self, url):
        self.url = url  # 更新 URL
        self.direct_stream_reader(url)  # 重新启动流读取
