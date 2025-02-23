
def left_shift_32( value, shift):
    result = (value << shift) & 0xFFFFFFFF
    if result & 0x80000000:
        result -= 0x100000000

    return result

def right_shift_32(value, shift):
    if value & 0x80000000:
        value -= 0x100000000
    result = (value >> shift) & 0xFFFFFFFF
    if result & 0x80000000:
        result -= 0x100000000
    return result
def unsigned_right_shift_32( value, shift):
    return ((value&0xFFFFFFFF) >> shift)&0xFFFFFFFF

def ds(e):
    t = e
    i = len(t)
    s = bytearray(i)
    o = 0
    for e in range(i):
        if e >= 2 and t[e] == 3 and t[e - 1] == 0 and t[e - 2] == 0:
            continue
        s[o] = t[e]
        o += 1
    return s[:o]

def cs(e):
    t = ds(e)
    i = tt(t)
    i.os()
    s = i.os()
    i.os()
    o = i.os()
    i.hs()
    a = As(s)
    r = ps(o)
    n = 1
    l = 420
    h = 8
    if s in [100, 110, 122, 244, 44, 83, 86, 118, 128, 138, 144]:
        n = i.hs()
        if n == 3:
            i.rs(1)
        if n <= 3:
            l = [0, 420, 422, 444][n]
        h = i.hs() + 8
        i.hs()
        i.rs(1)
        if i.ns():
            e1 = 12 if n == 3 else 8
            for t in range(e1):
                if i.ns():
                    gs(i, 16 if t < 6 else 64)
    i.hs()
    d = i.hs()
    if d == 0:
        i.hs()
    elif d == 1:
        i.rs(1)
        i.us()
        i.us()
        e2 = i.hs()
        for t in range(e2):
            i.us()
    u = i.hs()
    i.rs(1)
    c = i.hs()
    p = i.hs()
    m = i.rs(1)
    if m == 0:
        i.rs(1)
    i.rs(1)
    f = 0
    y = 0
    b = 0
    g = 0
    if i.ns():
        f = i.hs()
        y = i.hs()
        b = i.hs()
        g = i.hs()
    v = 1
    S = 1
    A = 0
    k = True
    I = 0
    V = 0
    if i.ns():
        if i.ns():
            e3 = i.os()
            if 0 < e3 < 16:
                v = [1, 12, 10, 16, 40, 24, 20, 32, 80, 18, 15, 64, 160, 4, 3, 2][e3 - 1]
                S = [1, 11, 11, 11, 33, 11, 11, 11, 33, 11, 11, 33, 99, 3, 2, 1][e3 - 1]
            elif e3 == 255:
                v = i.os() << 8 | i.os()
                S = i.os() << 8 | i.os()
        if i.ns():
            i.ns()
        if i.ns():
            i.rs(4)
            if i.ns():
                i.rs(24)
        if i.ns():
            i.hs()
            i.hs()
        if i.ns():
            e = i.rs(32)
            t = i.rs(32)
            k = i.ns()
            I = t
            V = 2 * e
            A = I / V
    G = 1
    if v != 1 or S != 1:
        G = v / S
    D = 0
    Z = 0
    if n == 0:
        D = 1
        Z = 2 - m
    else:
        D = 1 if n == 3 else 2
        Z = (2 - m) * (2 if n == 1 else 1)
    w = 16 * (c + 1)
    R = 16 * (p + 1) * (2 - m)
    w -= (f + y) * D
    R -= (b + g) * Z
    T = int(w * G)
    i.destroy()
    i = None
    return {
        'fs': a,
        'vs': r,
        'ys': h,
        'Ds': u,
        'Ss': l,
        'ws': Ms(l),
        'Es': {
            'fixed': k,
            'xs': A,
            'bs': V,
            'Is': I
        },
        'Fs': {
            'width': v,
            'height': S
        },
        'Ts': {
            'width': w,
            'height': R
        },
        'Cs': {
            'width': T,
            'height': R
        }
    }
def As(e):
    switcher = {
        66: "Baseline",
        77: "Main",
        88: "Extended",
        100: "High",
        110: "High10",
        122: "High422",
        244: "High444"
    }
    return switcher.get(e, "Unknown")
def gs(e, t):
    i = 8
    s = 8
    o = 0
    for a in range(t):
        if s != 0:
            o = e.us()
            s = (i + o + 256) % 256
        i = 0 if s == 0 else s

def ps(e):
    return f"{e / 10:.1f}"

def Ms(e):
    switcher = {
        420: "4:2:0",
        422: "4:2:2",
        444: "4:4:4"
    }
    return switcher.get(e, "Unknown")

class tt:
    def __init__(self, e):
        self.Yi = bytearray(e)  # 将输入数据转换为 bytearray
        self.Zi = 0  # 当前读取位置
        self.Xi = len(self.Yi)  # 数据总长度
        self.es = 0  # 当前 32 位字
        self.ts = 0  # 当前 32 位字中剩余的位数

    def destroy(self):
        self.Yi = bytearray()  # 清空数据

    def ss(self):
        e = self.Xi - self.Zi
        if e <= 0:
            raise ValueError("ExpGolomb: _fillCurrentWord() but no bytes available")
        t = min(4, e)
        i = bytearray(4)
        i[:t] = self.Yi[self.Zi:self.Zi + t]
        self.es =int.from_bytes(i, byteorder='big')  # 大端序
        self.Zi += t
        self.ts = 8 * t

    def rs(self, e):
        if e > 32:
            raise ValueError("ExpGolomb: readBits() bits exceeded max 32bits!")
        if e <= self.ts:
            t = unsigned_right_shift_32(self.es , (32 - e))
            self.es = left_shift_32(self.es, e)
            self.ts -= e
            return t
        t = self.es if self.ts else 0
        t = unsigned_right_shift_32(t,32 - self.ts)
        i = e - self.ts
        self.ss()
        s = min(i, self.ts)
        o = unsigned_right_shift_32(self.es , (32 - s))
        self.es = left_shift_32(self.es, s)
        self.ts -= s
        t = (t << s) | o
        return t

    def ns(self):
        return self.rs(1) == 1

    def os(self):
        return self.rs(8)

    def ls(self):
        e = 0
        for e in range(self.ts):
            if self.es & unsigned_right_shift_32(2147483648, e):
                self.es = left_shift_32(self.es, e)
                self.ts -= e
                return e
        self.ss()
        return e + self.ls()

    def hs(self):
        e = self.ls()
        return self.rs(e + 1) - 1

    def us(self):
        e = self.hs()
        return unsigned_right_shift_32(e + 1, 1) if e & 1 else -1 * unsigned_right_shift_32(e , 1)

class St:
    def __init__(self):
        self.mime_type = None
        self.has_audio = None
        self.audio_codec = None
        self.audio_sample_rate = None
        self.us = None
        self.has_video = False
        self.video_codec = None
        self.width = None
        self.height = None
        self.xs = None
        self.profile = None
        self.level = None
        self.ls = None
        self.Ns = 1
        self.Qs = 1
        self.Bs = 1
        self.Ls = "4:2:0"
        self.mime_type = None
        self.duration = None
        self.metadata = None
        self._s = False
        self.Ws = None


        # 检查媒体源是否准备好

    def Ps(self):
        # 检查音频相关属性是否已设置
        audio_ready = not self.has_audio or (
                self.has_audio and self.audio_codec is not None and self.audio_sample_rate is not None and self.us is not None)

        # 检查视频相关属性是否已设置
        video_ready = not self.has_video or (
                self.has_video and self.video_codec is not None and self.width is not None and self.height is not None and self.xs is not None and self.profile is not None and self.level is not None and self.Bs is not None and self.Ls is not None and self.Ns is not None and self.Qs is not None)

        # 检查所有必需的属性是否已设置
        return self.mime_type is not None and self.duration is not None and self.metadata is not None and self._s is not None and audio_ready and video_ready

        # 检查媒体源是否已初始化

    def Os(self):
        return self._s is True

    # 根据时间戳查找对应的样本信息
    def Hs(self, e):
        # 如果 Ws 为 None，则返回 None
        if self.Ws is None:
            return None

        t = self.Ws  # 获取 Ws 对象
        i = self._s(t['zs'], e)  # 查找时间戳对应的索引

        # 返回样本信息
        return {
            'index': i,  # 索引
            'Gs': t['zs'][i],  # 样本时间戳
            'qs': t['js'][i]  # 样本数据
        }

    # 使用二分查找法查找时间戳对应的索引
    def _s(self, e, t):
        i = 0  # 起始索引
        s = len(e) - 1  # 结束索引
        o = 0  # 中间索引
        a = 0  # 左边界
        r = s  # 右边界

        # 如果时间戳小于第一个样本时间戳，则返回第一个样本的索引
        if t < e[0]:
            i = 0
            a = r + 1

        # 二分查找
        while a <= r:
            o = a + (r - a) // 2  # 计算中间索引
            if o == s or (t >= e[o] and t < e[o + 1]):
                i = o  # 找到目标索引
                break
            if e[o] < t:
                a = o + 1  # 调整左边界
            else:
                r = o - 1  # 调整右边界

        return i  # 返回找到的索引
