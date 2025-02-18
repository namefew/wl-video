import math

from media_cache import ft
from mp4_helper import dt,ut
from logger import LogManager

ee = {
    "supports": {
        "mediaSource": True,
        "hls": False,
        "webAssembly": True,
        "simd": True,
        "pthreads": False,
        "webCodecsVideo": True,
        "webCodecsAudio": True,
        "webAudio": True,
        "webWorker": True,
        "serviceWorker": True,
        "moduleScriptsOnWorker": True,
        "videoCodecs": False,
        "transfer": True,
        "Th": False,
        "Ih": True,
        "Vh": True
    },
    "Eh": {},
    "Oh": {},
    "Ch": [
        "webCodecsVideo",
        "videoCodecs",
        "webAssembly"
    ],
    "Fh": [
        "webAssembly",
        "webCodecsAudio",
        "webAudio"
    ],
    "zh": "mediaSource"
}

ct = {
    "chrome": True,
    "version": {
        "hS": 132,
        "string": "132.0.0.0",
        "dS": 0,
        "uS": 0
    },
    "windows": True,
    "cS": True,
    "name": "chrome",
    "platform": "windows",
    "safari":None
}
re = {
    "version": "v4.8.22_fix2",
    "th": 1e3,
    "eh": 500,
    "sh": 400
}
A = {
    "Dt": "Player",
    "Tt": "MSEPlayer",
    "HttpLoader": "HttpLoader",
    "xt": "WebSocketLoader",
    "FlvDemuxer": "FlvDemuxer",
    "wt": "FlvDemuxerV2",
    "It": "MSEFlvDemuxer",
    "AudioDecoder": "AudioDecoder",
    "VideoDecoder": "VideoDecoder",
    "At": "AudioContextDecoder",
    "Mt": "WebVideoDecoder",
    "bt": "WebAudioDecoder",
    "Ft": "PcmRender",
    "Vt": "YuvRender",
    "Lt": "Controller",
    "kt": "DataManager",
    "Rt": "StatusManager",
    "Ot": "TaskManager",
    "Ct": "CircularQueue",
    "Ut": "HlsRemuxer",
    "Ht": "HlsPlayer",
    "Wt": "VideoCodecsPlayer",
    "$t": "DataFlow"
}
C = {
    "od": {
        "Jh": "mediaSource",
        "Xh": "mediaSource",
        "rg": 1000,
        "ng": 0,
        "xs": 25,
        "version": "v4.8.22_fix2"
    },
    "extInfo": {
        "解析绝对时差": None,
        "校准时差": "NaN",
        "校准耗时": "267"
    },
    "rd": [],
    "startTime": {
        "videoFirstFrameTime": 438.5
    }
}
class pt:
    def __init__(self, e, t, i, s, o):
        self.ka = e
        self.Va = t
        self.duration = i
        self.bS = s
        self.gS = o
        self.qs = None

class mt:
    def __init__(self):
        self.vS = 0
        self.SS = 0
        self.AS = 0
        self.rf = 0
        self.IS = 0
        self.kS = 0
        self.VS = []

    def GS(self, e):
        e.gS = True
        self.VS.append(e)

class yt: #Mp4Remuxer
    def __init__(self, logger=None):
        self.logger = logger
        self.sA = None
        self.lastSample = None
        self.Zs = "Mp4Remuxer"  # 类标识符
        self.xS = True  # 是否启用视频处理
        self.LS = -1  # 当前时间戳
        self.PS = False  # 是否已初始化
        self.XS = float('inf')  # 视频起始时间戳
        self.CS = float('inf')  # 音频起始时间戳
        self.HS = None  # 视频时间戳参考
        self.FS = None  # 音频时间戳参考
        self.ES = None  # 音频缓存数据
        self.US = None  # 视频缓存数据
        self.YS = None  # 音频配置
        self.JS = None  # 视频配置
        self.QS = None  # 初始化回调函数
        self.zS = None  # 媒体段回调函数
        self.Jm = -1  # 关键帧时间戳
        self.rg = 0  # Gop 时间
        self.xs = 0  # 帧率（FPS）
        self.KS = False  # 是否检测到 B 帧
        self.ng = 0  # B 帧数量
        self.NS = 0  # 帧率修正计数器
        self.BS = ft("audio")  # 音频数据缓存
        self.OS = ft("video")  # 视频数据缓存
        self.jS = True # 是否支持 Chrome 低版本
        self._S = True  # 浏览器类型
        self.eA = False  # 是否支持 MP3
        self.iA = False  # 是否支持时间戳修正

    def destroy(self):
        self.LS = -1  # 重置时间戳
        self.PS = False  # 重置初始化状态
        self.YS = None  # 清空音频配置
        self.JS = None  # 清空视频配置
        if self.BS is not None:
            self.BS.clear()  # 清空音频缓存
        self.BS = None
        if self.OS is not None:
            self.OS.clear()  # 清空视频缓存
        self.OS = None
        self.QS = None  # 清空初始化回调
        self.zS = None  # 清空媒体段回调
        self.NS = 0  # 重置帧率修正计数器
        self.lastSample = None  # 清空最后一个样本
        self.sA = None  # 清空当前样本
        self.Jm = -1  # 重置关键帧时间戳
        self.rg = 0  # 重置 Gop 时间
        self.xs = 0  # 重置帧率
        self.KS = False  # 重置 B 帧检测状态
        self.ng = 0  # 重置 B 帧数量

    # 绑定回调函数到外部对象
    def ia(self, e):
        e.ua = self.oA  # 绑定媒体段回调
        e.aa = self.yn  # 绑定初始化回调
        return self

    # 获取初始化回调
    @property
    def aA(self):
        return self.QS

    # 设置初始化回调
    @aA.setter
    def aA(self, e):
        self.QS = e

    # 获取媒体段回调
    @property
    def rA(self):
        return self.zS

    # 设置媒体段回调
    @rA.setter
    def rA(self, e):
        self.zS = e

    # 清空时间戳参考
    def nA(self):
        self.HS = self.FS = None

    # 清空媒体缓存
    def seek(self, e):
        self.ES = None  # 清空音频缓存
        self.US = None  # 清空视频缓存
        self.OS.clear()  # 清空视频数据缓存
        self.BS.clear()  # 清空音频数据缓存

    # 处理视频帧的时间戳和关键帧信息
    def lA(self, e):
        timestamp = e['Ya']  # 获取当前帧的时间戳

        # 如果当前帧是关键帧（I帧）
        if e['Ka']:
            # 如果 Jm 小于 0，则初始化 Jm 为当前时间戳
            if self.Jm < 0:
                self.Jm = timestamp

            # 如果 rg 为 0，则初始化 rg 为负的时间戳
            if self.rg == 0:
                self.rg = -e['ka']
            elif self.rg < 0 and -self.rg != timestamp:
                # 如果 rg 小于 0 且 rg 的绝对值不等于当前时间戳，则更新 rg 和相关参数
                self.rg += timestamp
                self.xs = round(1000 / self.JS['Pa'])  # 计算帧率（FPS）
                if self.KS:
                    self.ng = round(-self.ng / self.JS['Pa'])  # 计算 B 帧数量
                else:
                    self.ng = 0

                #发送 Gop 信息   主要更新了C的信息
                # _.il("HeadInfo", None, {
                #     "rg": self.rg,  # Gop 时间（毫秒）
                #     "ng": self.ng,  # B 帧数量
                #     "xs": self.xs,  # 帧率（FPS）
                #     "version": re['version']  # 版本号
                # })
                # 记录 Gop 信息
                self.logger.info(f"Gop: {self.rg} ms; B frame num: {self.ng}; Fps: {self.xs}")

        # 如果 Jm 大于 0 且 xs 为 0 且当前时间戳大于 Jm 且 KS 为 false 且 ng 为 0
        if self.Jm > 0 and not self.xs and timestamp > self.Jm and not self.KS and not self.ng:
            self.KS = True  # 设置 KS 为 true
            self.ng = self.Jm - timestamp  # 计算 B 帧数量

    # 处理媒体段数据，调用 lA 处理视频帧，并生成媒体段
    def oA(self, e, t):
        if not self.zS:
            raise Exception("Mp4Remuxer: onMediaSegment callback must be specificed!")
        if self.PS or self.hA(e, t):
            if ee['supports']['videoCodecs']:
                e = list(t.Vr)
                for i in e:
                    self.lA(i)
                    if self.lastSample:
                        if i.ka == self.lastSample.ka:
                            continue
                        self.sA['Vr'] = [self.lastSample]
                        self.sA['length'] = self.lastSample['length']
                        self.dA(self.sA, True, i['ka'] - self.lastSample['ka'])
                    self.sA = t
                    self.lastSample = i
            else:
                for i in t['Vr']:
                    self.lA(i)
                self.dA(t, False)
        self.uA(e, False)

    # 处理初始化段数据
    def yn(self, e, t):
        i = None
        s = "mp4"
        o = t.codec
        if e == "audio":
            self.YS = t
            if t['codec'] == "mp3" and self.eA:
                s = "mpeg"
                o = ""
                i = bytearray()
            else:
                i = dt.eS(t)
        elif e == "video":
            self.JS = t
            i = dt.eS(t)
        else:
            return
        if not self.QS:
            raise Exception("Mp4Remuxer: onInitSegment callback must be specified!")
        self.QS(e, {
            "type": e,
            "data": i,
            "codec": o,
            "container": f"{e}/{s}",
            "cA": t.duration
        })

    # 初始化时间戳
    def hA(self, e, t):
        if not self.PS:
            if e['Vr'] and len(e['Vr']):
                self.XS = e['Vr'][0]['ka']
            else:
                self.XS = 0
            if t['Vr'] and len(t['Vr']):
                self.CS = t['Vr'][0]['ka']
            else:
                self.CS = 0
            self.LS = min(self.XS, self.CS)
            self.PS = True

    # 生成并发送视频和音频数据
    def pA(self):
        e = self.US
        t = self.ES
        i = {
            "type": "video",
            "id": 1,
            "kr": 0,
            "Vr": [],
            "length": 0
        }
        if e is not None:
            i["Vr"].append(e)
            i["length"] = e.length
        s = {
            "type": "audio",
            "id": 2,
            "kr": 0,
            "Vr": [],
            "length": 0
        }
        if t is not None:
            s["Vr"].append(t)
            s["length"] = t.length
        self.US = None
        self.ES = None
        self.dA(i, True)
        self.uA(s, True)

    # 处理音频数据
    def uA(self, e, t):
        if self.YS is None:
            return
        i, s = None, e
        o = s['Vr']
        a = -1
        r = -1
        n = self.YS['Pa']
        l = self.YS['codec'] == "mp3" and self.eA
        h = self.PS and self.HS is None
        d = False
        if not o or len(o) == 0 or (len(o) == 1 and not t):
            return
        u = 0
        c = None
        p = 0
        if l:
            u = 0
            p = s.length
        else:
            u = 8
            p = 8 + s.length
        m = None
        if len(o) > 1:
            m = o.pop()
            p -= m.length
        if self.ES is not None:
            e = self.ES
            self.ES = None
            o.insert(0, e)
            p += e.length
        if m is not None:
            self.ES = m
        f = o[0].ka - self.LS
        if self.HS:
            i = f - self.HS
        elif self.BS.tm():
            i = 0
            if self._S and not self.OS.tm() and self.YS.codec != "mp3":
                d = True
        else:
            e = self.BS.MS(f)
            if e is not None:
                t = f - (e.bS + e.duration)
                if t <= 3:
                    t = 0
                i = f - (e.ka + e.duration + t)
            else:
                i = 0
        if d:
            e = f - i
            t = self.OS.TS(f)
            if t is not None and t.vS < e:
                i = ut.nS(self.YS.codec, self.YS.channelCount)
                if i:
                    s = t.vS
                    a = e - t.vS
                    print(self.Zs, f"InsertPrefixSilentAudio: dts: {s}, duration: {a}")
                    o.insert(0, {
                        "unit": i,
                        "ka": s,
                        "Va": s
                    })
                    p += len(i)  # 修改这里以确保正确处理字节长度
            else:
                d = False
        y = []
        for e in range(len(o)):
            t = o[e]
            s = t.unit
            if isinstance(s, int):  # 检查并转换为 bytearray 如果是整数
                s = bytearray([s])
            r = t.ka - self.LS
            l = r
            h = False
            d = None
            u = 0
            if not r < -0.001:
                if self.YS.codec != "mp3":
                    e = r
                    if self.HS:
                        e = self.HS
                    i = r - e
                    if i <= -3 * n:
                        print(self.Zs,
                              f"Dropping 1 audio frame (originalDts: {r} ms ,curRefDts: {e} ms)  due to dtsCorrection: {i} ms overlap.")
                        continue
                    if i >= 3 * n and self.iA and not ct['safari']:
                        h = True
                        t = int(i / n)
                        print(self.Zs,
                              f"Large audio timestamp gap detected, may cause AV sync to drift.Silent frames will be generated to avoid unsync.\noriginalDts: {r} ms, curRefDts: {e} ms, dtsCorrection: {round(i)} ms, generate: {t} frames")
                        l = int(e)
                        u = int(e + n) - l
                        i = ut.nS(self.YS.codec, self.YS.channelCount)
                        if i is None:
                            print(self.Zs,
                                  f"Unable to generate silent frame for {self.YS.codec} with {self.YS.channelCount} channels, repeat last frame")
                            i = s
                        d = []
                        for i in range(t):
                            e += n
                            t = int(e)
                            i = int(e + n) - t
                            s = {
                                "ka": t,
                                "Va": t,
                                "Ya": 0,
                                "unit": i,
                                "size": 4,  # 修改这里以确保正确处理字节长度
                                "duration": i,
                                "bS": r,
                                "flags": {
                                    "iS": 0,
                                    "sS": 1,
                                    "oS": 0,
                                    "aS": 0
                                }
                            }
                            d.append(s)
                            p += s["size"]
                        self.HS = e + n
                    else:
                        l = int(e)
                        u = int(e + n) - l
                        self.HS = e + n
                else:
                    l = r - i
                    u = e != len(o) - 1 and o[e + 1].ka - self.LS - i - l or m and m.ka - self.LS - i - l or len(
                        y) >= 1 and y[len(y) - 1]["duration"] or int(n)
                    self.HS = l + u
                if a == -1:
                    a = l
                y.append({
                    "ka": l,
                    "Va": l,
                    "Ya": 0,
                    "unit": t.unit,
                    "size": len(t.unit),  # 修改这里以确保正确处理字节长度
                    "duration": u,
                    "bS": r,
                    "flags": {
                        "iS": 0,
                        "sS": 1,
                        "oS": 0,
                        "aS": 0
                    }
                })
                if h:
                    y.extend(d)
        if len(y) == 0:
            s["Vr"] = []
            s["length"] = 0
            return
        if l:
            c = bytearray(p)
        else:
            c = bytearray(p)
            c[0] = p >> 24 & 255
            c[1] = p >> 16 & 255
            c[2] = p >> 8 & 255
            c[3] = 255 & p
            c[4:8] = dt.types.mdat
        for e in range(len(y)):
            t = y[e]["unit"]
            c[u:u + len(t)] = t  # 修改这里以确保正确处理字节长度
            u += len(t)
        b = y[len(y) - 1]
        r = b["ka"] + b["duration"]
        g = mt()
        g.vS = a
        g.SS = r
        g.AS = a
        g.rf = r
        g.IS = y[0]["bS"]
        g.kS = b["bS"] + b["duration"]
        g.mA = pt(y[0]["ka"], y[0]["Va"], y[0]["duration"], y[0]["bS"], False)
        g.lastSample = pt(b["ka"], b["Va"], b["duration"], b["bS"], False)
        if not self.xS:
            self.BS.append(g)
        s["Vr"] = y
        s["kr"] += 1
        v = None
        v = bytearray() if l else dt.moof(s, a)
        s["Vr"] = []
        s["length"] = 0
        S = {
            "type": "audio",
            "data": self.fA(v, c),
            "sampleCount": len(y),
            "info": g,
            "timeStamp": g.AS,
            "duration": g.rf - g.AS
        }
        if l and h:
            S["timestampOffset"] = a
        self.zS("audio", S)

    def yn(self, e, t):
        i = None
        s = "mp4"
        o = t['codec']

        if e == "audio":
            self.YS = t
            if t['codec'] == "mp3" and self.eA:
                s = "mpeg"
                o = ""
                i = bytearray()  # 创建一个空的 bytearray
            else:
                i = dt.eS(t)
        elif e == "video":
            self.JS = t
            i = dt.eS(t)
        else:
            return

        if not self.QS:
            raise Exception("Mp4Remuxer: onInitSegment callback must be specified!")

        self.QS(e, {
            "type": e,
            "data": i,  # 直接使用 bytearray
            "codec": o,
            "container": f"{e}/{s}",
            "cA": t['duration']
        })

    def dA(self, e, t, i=0):
        if self.JS is None:
            return

        s = None
        o = e
        a= e['Vr']
        r, h, d, u = -1, -1, -1, -1

        if not a or len(a) == 0 or (len(a) == 1 and not t):
            return

        c = 8
        p = None
        m = 8 + e['length']
        f = None

        if len(a) > 1:
            f = a.pop()
            m -= f['length']

        if self.US is not None:
            e1 = self.US
            self.US = None
            a.insert(0, e1)
            m += len(e1)

        if f is not None:
            self.US = f

        y = a[0]['ka'] - self.LS

        if self.FS:
            s = y - self.FS
        elif self.OS.tm():
            s = 0
        else:
            e2 = self.OS.MS(y)
            if e2 is not None:
                t1 = y - (e2['bS'] + e2['duration'])
                if t1<=3:
                    t1=0
                s = y - (e2['ka'] + e2['duration'] + t1)
            else:
                s = 0

        b = mt()
        g = []

        for e2 in range(len(a)):
            t2 = a[e2]
            o1 = t2['ka'] - self.LS
            n = t2['Ka']
            l = o1 - s
            h = t2['Ya']
            u = l + h

            if r == -1:
                r = l
                d = u

            ii = 0
            if e2 != len(a)- 1:
                ii = a[e2 + 1]['ka'] - self.LS - s - l
            elif f is not None:
                ii = f['ka'] - self.LS - s - l
            elif len(g) >= 1:
                ii = g[-1]['duration']
            elif i:
                ii = i
                s = 0
            else:
                e3 = math.floor(self.JS['Pa'])
                t2 = self.JS['Pa'] - e3
                ii = e3 + round(t2 * (++self.NS) % 1)

            if n:
                e4 = pt(l, u, ii, t2['ka'], True)
                e4.qs = t2['qs']
                b.GS(e4)
                self.NS = 0

            g.append({
                'ka': l,
                'Va': u,
                'Ya': h,
                'units': t2['units'],
                'size': t2['length'],
                'Ka': n,
                'duration': ii,
                'bS': o1,
                'Xa': t2['Xa'],
                'flags': {
                    'iS': 0,
                    'sS': 2 if n else 1,
                    'oS': 1 if n else 0,
                    'aS': 0,
                    'rS': 0 if n else 1
                }
            })

        p = bytearray(m)
        p[0] = (m >> 24) & 255
        p[1] = (m >> 16) & 255
        p[2] = (m >> 8) & 255
        p[3] = m & 255
        p[4:] = bytes(dt.types['mdat'])

        for e5 in range(len(g)):
            t3 = g[e5]['units']
            while t3:
                e6 = t3.pop(0)['data']
                p[c:c + len(e6)] = e6
                c += len(e6)

        v = g[-1]
        h = v['ka'] + v['duration']
        u = v['Va'] + v['duration']
        self.FS = h
        b.vS = r
        b.SS = h
        b.AS = d
        b.rf = u
        b.IS = g[0]['bS']
        b.kS = v['bS'] + v['duration']
        b.mA = pt(g[0]['ka'], g[0]['Va'], g[0]['duration'], g[0]['bS'], g[0]['Ka'])
        b.lastSample = pt(v['ka'], v['Va'], v['duration'], v['bS'], v['Ka'])

        if not self.xS:
            self.OS.append(b)
        o['Vr'] = g
        o['kr'] += 1
        if self.jS:
            e4 = g[0]['flags']
            e4['sS'] = 2
            e4['rS'] = 0
        if r<0:
            r=0
        S = dt.moof(o, r)
        o['Vr'] = []
        o['length'] = 0
        the_data =  {
            'type': "video",
            'data': self.fA(S, p),
            'sampleCount': len(g),
            'info': b,
            'timeStamp': b.AS,
            'duration': sum([t['duration'] for t in g]),
            'detail': [{**t, 'units': [], 'flags': None} for t in g]
        }
        self.zS("video",the_data)
    # 合并二进制数据
    def fA(self, e, t):
        i = bytearray(len(e) + len(t))
        i[:len(e)] = e
        i[len(e):] = t
        return i