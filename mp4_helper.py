class dt:
    constants = None
    types = None

    @staticmethod
    def init():
        dt.types = {
            'avc1': [],
            'avcC': [],
            'btrt': [],
            'dinf': [],
            'dref': [],
            'esds': [],
            'ftyp': [],
            'hdlr': [],
            'mdat': [],
            'mdhd': [],
            'mdia': [],
            'mfhd': [],
            'minf': [],
            'moof': [],
            'moov': [],
            'mp4a': [],
            'mvex': [],
            'mvhd': [],
            'sdtp': [],
            'stbl': [],
            'stco': [],
            'stsc': [],
            'stsd': [],
            'stsz': [],
            'stts': [],
            'tfdt': [],
            'tfhd': [],
            'traf': [],
            'trak': [],
            'trun': [],
            'trex': [],
            'tkhd': [],
            'vmhd': [],
            'smhd': [],
            'Uv': []
        }
        for key in dt.types:
            if key in dt.types:  # 确保只处理自身属性
                dt.types[key] = [ord(c) for c in key]
        constants = dt.constants = {}
        constants['Yv'] = bytearray([105, 115, 111, 109, 0, 0, 0, 1, 105, 115, 111, 109, 97, 118, 99, 49])
        constants['Jv'] = bytearray([0, 0, 0, 0, 0, 0, 0, 1])
        constants['Qv'] = bytearray([0, 0, 0, 0, 0, 0, 0, 0])
        constants['zv'] = constants['Kv'] = constants['Qv']
        constants['Nv'] = bytearray([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        constants['Bv'] = bytearray(
            [0, 0, 0, 0, 0, 0, 0, 0, 118, 105, 100, 101, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 86, 105, 100, 101, 111, 72,
             97, 110, 100, 108, 101, 114, 0])
        constants['Ov'] = bytearray(
            [0, 0, 0, 0, 0, 0, 0, 0, 115, 111, 117, 110, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 83, 111, 117, 110, 100, 72,
             97, 110, 100, 108, 101, 114, 0])
        constants['jv'] = bytearray([0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 12, 117, 114, 108, 32, 0, 0, 0, 1])
        constants['$v'] = bytearray([0, 0, 0, 0, 0, 0, 0, 0])
        constants['_v'] = bytearray([0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])

    @staticmethod
    def qv(e, *t):
        i = 8
        s = bytearray(0)
        o = len(t)
        for _ in range(o):
            i += len(t[_])
        s = bytearray(i)
        s[0] = (i >> 24) & 255
        s[1] = (i >> 16) & 255
        s[2] = (i >> 8) & 255
        s[3] = i & 255
        s[4:8] = e
        a = 8
        for _ in range(o):
            s[a:a + len(t[_])] = t[_]
            a += len(t[_])
        return s

    @staticmethod
    def eS(e):
        t = dt.qv(dt.types['ftyp'], dt.constants['Yv'])
        i = dt.moov(e)
        s = bytearray(len(t) + len(i))
        s[:len(t)] = t
        s[len(t):] = i
        return s

    @staticmethod
    def moov(e):
        t = dt.mvhd(e['xa'], e['duration'])
        i = dt.trak(e)
        s = dt.mvex(e)
        return dt.qv(dt.types['moov'], t, i, s)

    @staticmethod
    def mvhd(e, t):
        if not isinstance(e, int):
            e = int(e)
        if not isinstance(t, int):
            t = int(t)
        return dt.qv(dt.types['mvhd'], bytearray(
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, (e >> 24) & 255, (e >> 16) & 255, (e >> 8) & 255, 255 & e,
             (t >> 24) & 255, (t >> 16) & 255, (t >> 8) & 255, 255 & t, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 64, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 255, 255, 255, 255]
        ))

    @staticmethod
    def trak(e):
        return dt.qv(dt.types['trak'], dt.tkhd(e), dt.mdia(e))

    @staticmethod
    def tkhd(e):
        t = e['id']
        i = e['duration']
        s = e['Wa']
        o = e['$a']
        return dt.qv(dt.types['tkhd'], bytearray(
            [0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0, (t >> 24) & 255, (t >> 16) & 255, (t >> 8) & 255, 255 & t, 0, 0, 0, 0,
             (i >> 24) & 255, (i >> 16) & 255, (i >> 8) & 255, 255 & i, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 64, 0, 0,
             0, (s >> 8) & 255, 255 & s, 0, 0, (o >> 8) & 255, 255 & o, 0, 0]
        ))

    @staticmethod
    def mdia(e):
        return dt.qv(dt.types['mdia'], dt.mdhd(e), dt.hdlr(e), dt.minf(e))

    @staticmethod
    def mdhd(e):
        t = int(e['xa'])
        i = int(e['duration'])
        return dt.qv(dt.types['mdhd'], bytearray(
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, (t >> 24) & 255, (t >> 16) & 255, (t >> 8) & 255, 255 & t,
             (i >> 24) & 255, (i >> 16) & 255, (i >> 8) & 255, 255 & i, 85, 196, 0, 0]
        ))

    @staticmethod
    def hdlr(e):
        t = None
        if e['type'] == 'audio':
            t = dt.constants['Ov']
        else:
            t = dt.constants['Bv']
        return dt.qv(dt.types['hdlr'], t)

    @staticmethod
    def minf(e):
        t = None
        if e['type'] == 'audio':
            t = dt.qv(dt.types['smhd'], dt.constants['$v'])
        else:
            t = dt.qv(dt.types['vmhd'], dt.constants['_v'])
        return dt.qv(dt.types['minf'], t, dt.dinf(), dt.stbl(e))

    @staticmethod
    def dinf():
        return dt.qv(dt.types['dinf'], dt.qv(dt.types['dref'], dt.constants['jv']))

    @staticmethod
    def stbl(e):
        return dt.qv(dt.types['stbl'], dt.stsd(e), dt.qv(dt.types['stts'], dt.constants['Qv']),
                     dt.qv(dt.types['stsc'], dt.constants['zv']), dt.qv(dt.types['stsz'], dt.constants['Nv']),
                     dt.qv(dt.types['stco'], dt.constants['Kv']))

    @staticmethod
    def stsd(e):
        if e['type'] == 'audio':
            if e['codec'] == 'mp3':
                return dt.qv(dt.types['stsd'], dt.constants['Jv'], dt.tS(e))
            else:
                return dt.qv(dt.types['stsd'], dt.constants['Jv'], dt.mp4a(e))
        else:
            return dt.qv(dt.types['stsd'], dt.constants['Jv'], dt.avc1(e))

    @staticmethod
    def tS(e):
        t = e['channelCount']
        i = e['audioSampleRate']
        s = bytearray([
            0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
            0, t, 0, 16, 0, 0, 0, 0, (i >> 8) & 255, i & 255, 0, 0
        ])
        return dt.qv(dt.types['Uv'], s)

    @staticmethod
    def mp4a(e):
        t = e['channelCount']
        i = e['audioSampleRate']
        s = bytearray([
            0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
            0, t, 0, 16, 0, 0, 0, 0, (i >> 8) & 255, i & 255, 0, 0
        ])
        return dt.qv(dt.types['mp4a'], s, dt.esds(e))

    @staticmethod
    def esds(e):
        t = e.get('config', [])
        i = len(t)
        s = bytearray([
                          0, 0, 0, 0, 3, 23 + i, 0, 1, 0, 4, 15 + i, 64, 21, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5
                      ] + t + [6, 1, 2])
        return dt.qv(dt.types['esds'], s)

    @staticmethod
    def avc1(e):
        t = e['_a']
        i = e['Oa']
        s = e['Ha']
        o = bytearray([
            0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            (i >> 8) & 255, i & 255, (s >> 8) & 255, s & 255, 0, 72, 0, 0, 0, 72, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 24, 255, 255
        ])
        return dt.qv(dt.types['avc1'], o, dt.qv(dt.types['avcC'], t))

    @staticmethod
    def mvex(e):
        return dt.qv(dt.types['mvex'], dt.trex(e))

    @staticmethod
    def trex(e):
        t = e['id']
        i = bytearray([
            0, 0, 0, 0, (t >> 24) & 255, (t >> 16) & 255, (t >> 8) & 255, t & 255,
            0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1
        ])
        return dt.qv(dt.types['trex'], i)

    @staticmethod
    def moof(e, t):
        return dt.qv(dt.types['moof'], dt.mfhd(e['kr']), dt.traf(e, t))

    @staticmethod
    def mfhd(e):
        t = bytearray([
            0, 0, 0, 0, (e >> 24) & 255, (e >> 16) & 255, (e >> 8) & 255, e & 255
        ])
        return dt.qv(dt.types['mfhd'], t)

    @staticmethod
    def traf(e, t):
        i = e['id']
        s = dt.qv(dt.types['tfhd'], bytearray([
            0, 0, 0, 0, (i >> 24) & 255, (i >> 16) & 255, (i >> 8) & 255, i & 255
        ]))
        o = dt.qv(dt.types['tfdt'], bytearray([
            0, 0, 0, 0, (t >> 24) & 255, (t >> 16) & 255, (t >> 8) & 255, t & 255
        ]))
        a = dt.sdtp(e)
        r = dt.trun(e, len(a) + 16 + 16 + 8 + 16 + 8 + 8)
        return dt.qv(dt.types['traf'], s, o, r, a)

    @staticmethod
    def sdtp(e):
        t = e.get('Vr', [])
        i = len(t)
        s = bytearray(4 + i)
        for index in range(i):
            flags = t[index]['flags']
            s[index + 4] = (flags['iS'] << 6) | (flags['sS'] << 4) | (flags['oS'] << 2) | flags['aS']
        return dt.qv(dt.types['sdtp'], s)

    @staticmethod
    def trun(e, t):
        i = e.get('Vr', [])
        s = len(i)
        o = 12 + 16 * s
        a = bytearray(o)
        t += 8 + o
        a[0:8] = [
            0, 0, 15, 1,
            (s >> 24) & 255, (s >> 16) & 255, (s >> 8) & 255, s & 255,
            (t >> 24) & 255, (t >> 16) & 255, (t >> 8) & 255, t & 255
        ]
        for index in range(s):
            duration = int(i[index]['duration'])
            size = int(i[index]['size'])
            flags = i[index]['flags']
            Ya = i[index]['Ya']
            a[12 + 16 * index:12 + 16 * (index + 1)] = [
                (duration >> 24) & 255, (duration >> 16) & 255, (duration >> 8) & 255, duration & 255,
                (size >> 24) & 255, (size >> 16) & 255, (size >> 8) & 255, size & 255,
                (flags['iS'] << 2) | flags['sS'],
                (flags['oS'] << 6) | (flags['aS'] << 4) | flags['rS'],
                0, 0,
                (Ya >> 24) & 255, (Ya >> 16) & 255, (Ya >> 8) & 255, Ya & 255
            ]
        return dt.qv(dt.types['trun'], a)

    @staticmethod
    def mdat(e):
        return dt.qv(dt.types['mdat'], e)


dt.init()


class ut:
    @staticmethod
    def nS(e, t):
        if e == "mp4a.40.2":
            if t == 1:
                return bytearray([0, 200, 0, 128, 35, 128])
            elif t == 2:
                return bytearray([33, 0, 73, 144, 2, 25, 0, 35, 128])
            elif t == 3:
                return bytearray([0, 200, 0, 128, 32, 132, 1, 38, 64, 8, 100, 0, 142])
            elif t == 4:
                return bytearray([0, 200, 0, 128, 32, 132, 1, 38, 64, 8, 100, 0, 128, 44, 128, 8, 2, 56])
            elif t == 5:
                return bytearray([0, 200, 0, 128, 32, 132, 1, 38, 64, 8, 100, 0, 130, 48, 4, 153, 0, 33, 144, 2, 56])
            elif t == 6:
                return bytearray(
                    [0, 200, 0, 128, 32, 132, 1, 38, 64, 8, 100, 0, 130, 48, 4, 153, 0, 33, 144, 2, 0, 178, 0, 32, 8,
                     224])
        else:
            if t == 1:
                return bytearray(
                    [1, 64, 34, 128, 163, 78, 230, 128, 186, 8, 0, 0, 0, 28, 6, 241, 193, 10, 90, 90, 90, 90, 90, 90,
                     90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90,
                     90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 94])
            elif t == 2:
                return bytearray(
                    [1, 64, 34, 128, 163, 94, 230, 128, 186, 8, 0, 0, 0, 0, 149, 0, 6, 241, 161, 10, 90, 90, 90, 90, 90,
                     90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90,
                     90, 90, 90, 90, 90, 90, 90, 90, 94])
            elif t == 3:
                return bytearray(
                    [1, 64, 34, 128, 163, 94, 230, 128, 186, 8, 0, 0, 0, 0, 149, 0, 6, 241, 161, 10, 90, 90, 90, 90, 90,
                     90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90,
                     90, 90, 90, 90, 90, 90, 90, 94])
        return None
