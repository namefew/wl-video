class ft:
    def __init__(self, e):
        self.ZS = e
        self.DS = []
        self.wS = -1

    @property
    def type(self):
        return self.ZS

    @property
    def length(self):
        return len(self.DS)

    def tm(self):
        return len(self.DS) == 0

    def clear(self):
        self.DS = []
        self.wS = -1

    def RS(self, e):
        t = self.DS
        if len(t) == 0:
            return -2
        i = len(t) - 1
        s = 0
        o = 0
        a = i
        r = 0
        if e < t[0].IS:
            r = -1
            return r
        while o <= a:
            s = o + (a - o) // 2
            if s == i or (e > t[s].lastSample.bS and e < t[s + 1].IS):
                r = s
                break
            if t[s].IS < e:
                o = s + 1
            else:
                a = s - 1
        return r

    def append(self, e):
        t = self.DS
        i = e
        s = self.wS
        o = 0
        if s != -1 and s < len(t) and i.IS >= t[s].lastSample.bS and (s == len(t) - 1 or s < len(t) - 1 and i.IS < t[s + 1].IS):
            o = s + 1
        elif len(t) > 0:
            o = self.RS(i.IS) + 1
        self.wS = o
        self.DS.insert(o, i)

    def TS(self, e):
        t = self.RS(e)
        return self.DS[t] if t >= 0 else None

    def MS(self, e):
        t = self.TS(e)
        return t.lastSample if t is not None else None

    def WS(self, e):
        t = self.RS(e)
        i = self.DS[t].VS
        while len(i) == 0 and t > 0:
            t -= 1
            i = self.DS[t].VS
        return i[-1] if len(i) > 0 else None
