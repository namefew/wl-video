from mp4_helper import dt

t = {'$a': 1080, 'Ca': bytearray(b"\x01d\x00(\xff\xe1\x00%gd\x00(\xac+@\'\x81\x13\xdc\xb8\x0bP\x10\x10\x14\x00\x00\x0f\xa0\x00\x03\rC\x80\x00\x03\r@\x00\x18j\x0b\xbc\xb8(\x01\x00\x04h\xee<\xb0"), 'Ga': {'height': 1, 'width': 1}, 'Ha': 1080, 'Ja': bytearray(b"\x00\x00\x00\x01gd\x00(\xac+@\'\x81\x13\xdc\xb8\x0bP\x10\x10\x14\x00\x00\x0f\xa0\x00\x03\rC\x80\x00\x03\r@\x00\x18j\x0b\xbc\xb8(\x00\x00\x00\x01h\xee<\xb0"), 'Ls': 420, 'Oa': 1260, 'Pa': 40.0, 'Wa': 1260, '_a': bytearray(b"\x01d\x00(\xff\xe1\x00%gd\x00(\xac+@\'\x81\x13\xdc\xb8\x0bP\x10\x10\x14\x00\x00\x0f\xa0\x00\x03\rC\x80\x00\x03\r@\x00\x18j\x0b\xbc\xb8(\x01\x00\x04h\xee<\xb0"), 'codec': 'avc1.640028', 'duration': 0, 'id': 1, 'ja': 'h264', 'level': '4.0', 'profile': 'High', 'qa': {'Is': 50000, 'bs': 2000, 'fixed': True, 'xs': 25.0}, 'type': 'video', 'xa': 1000.0, 'za': 8}

# 修正后的Python实现应输出96字节
print(len(dt.mvhd(1000.0, 0)))  # 应当输出96
stsd_data = dt.stsd(t)
print(len(stsd_data))  # 应当输出 102
avc1_data = dt.avc1(t)
print(len(avc1_data))  # 应当输出 86 (avc1_box 62字节 + avcC_box 24字节)

data = dt.eS(t)

print(f' 预期长度667 实际长度 ：{len(data)} , {"pass" if len(data)==667 else "fail"}')