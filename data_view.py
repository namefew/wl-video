import struct


class DataView:
    def __init__(self, buffer, offset=0, little_endian=False):
        self.buffer = buffer
        self.offset = offset
        self.little_endian = little_endian

    def os(self):
        return self.get_uint8()

    def get_uint8(self, index=0):
        value = self.buffer[self.offset+index]
        return value

    def hs(self):
        return self.get_uint16()

    def get_uint16(self,index=0,little_endian=False):
        fmt = '<H' if little_endian else '>H'
        value = struct.unpack_from(fmt, self.buffer, self.offset+index)[0]
        return value

    def rs(self, length):
        return self.get_bytes(length)

    def get_bytes(self, length):
        value = self.buffer[self.offset:self.offset + length]
        return value

    def ns(self):
        return self.get_uint32()

    def get_uint32(self, index=0,little_endian=False):
        fmt = '<I' if little_endian else '>I'
        value = struct.unpack_from(fmt, self.buffer, self.offset+index)[0]
        return value

    def us(self):
        return self.get_uint16()

    def destroy(self):
        self.buffer = None
        self.offset = 0
