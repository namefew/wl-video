import struct
import logging

logger = logging.getLogger(__name__)


def parse_script(data, offset, size):
    """解析 AMF 对象属性"""
    s = {}
    try:
        # 解析第一个 AMF 值（通常是属性名称）
        o = parse_value(data, offset, size)
        # 解析第二个 AMF 值（通常是属性值）
        a = parse_value(data, offset + o['size'], size - o['size'])
        # 将解析的名称和值存储在字典中
        s[o['data']] = a['data']
    except Exception as e:
        print(f"AMF {str(e)}")
    return s

def parse_value(data, offset, size):
    """解析 AMF 值"""
    if size < 1:
        raise Exception("Data not enough when parse Value")

    s = None
    a = 1
    r = data[offset]
    n = False

    try:
        match r:
            case 0:  # Number (double)
                s = struct.unpack('>d', data[offset + 1:offset + 9])[0]
                a += 8
            case 1:  # Boolean
                s = bool(data[offset + 1])
                a += 1
            case 2:  # String
                result = parse_string(data, offset + 1, size - 1)
                s = result['data']
                a += result['size']
            case 3:  # Object
                s = {}
                r = 0
                if struct.unpack('>I', data[offset + size - 4:offset + size])[0] & 0xFFFFFF == 9:
                    r = 3
                while a < size - 4:
                    result = parse_object_property(data, offset + a, size - a - r)
                    if result['qi']:
                        break
                    s[result['data']['name']] = result['data']['value']
                    a += result['size']
                if a <= size - 3 and struct.unpack('>I', data[offset + a - 1:offset + a + 3])[0] & 0xFFFFFF == 9:
                    a += 3
            case 8:  # ECMA Array
                s = {}
                a += 4
                r = 0
                if struct.unpack('>I', data[offset + size - 4:offset + size])[0] & 0xFFFFFF == 9:
                    r = 3
                while a < size - 8:
                    result = parse_ecma_array_property(data, offset + a, size - a - r)
                    if result['qi']:
                        break
                    s[result['data']['name']] = result['data']['value']
                    a += result['size']
                if a <= size - 3 and struct.unpack('>I', data[offset + a - 1:offset + a + 3])[0] & 0xFFFFFF == 9:
                    a += 3
            case 9:  # Strict Array
                s = None
                a = 1
                n = True
            case 10:  # Array
                s = []
                count = struct.unpack('>I', data[offset + 1:offset + 5])[0]
                a += 4
                for _ in range(count):
                    result = parse_value(data, offset + a, size - a)
                    s.append(result['data'])
                    a += result['size']
            case 11:  # Date
                result = parse_date(data, offset + 1, size - 1)
                s = result['data']
                a += result['size']
            case 12:  # Long String
                result = parse_long_string(data, offset + 1, size - 1)
                s = result['data']
                a += result['size']
            case _:
                a = size
                logger.debug(f"AMF Unsupported AMF value type {r}")
    except Exception as e:
        logger.debug(f"AMF {str(e)}")

    return {
        'data': s,
        'size': a,
        'qi': n
    }

def parse_string(data, offset, size):
    """解析字符串"""
    length = struct.unpack('>H', data[offset:offset + 2])[0]
    string_data = data[offset + 2:offset + 2 + length].decode('utf-8')
    return {
        'data': string_data,
        'size': 2 + length
    }

def parse_object_property(data, offset, size):
    """解析对象属性"""
    name_result = parse_string(data, offset, size)
    value_result = parse_value(data, offset + name_result['size'], size - name_result['size'])
    return {
        'data': {
            'name': name_result['data'],
            'value': value_result['data']
        },
        'size': name_result['size'] + value_result['size'],
        'qi': value_result['qi']
    }

def parse_ecma_array_property(data, offset, size):
    """解析 ECMA 数组属性"""
    name_result = parse_string(data, offset, size)
    value_result = parse_value(data, offset + name_result['size'], size - name_result['size'])
    return {
        'data': {
            'name': name_result['data'],
            'value': value_result['data']
        },
        'size': name_result['size'] + value_result['size'],
        'qi': value_result['qi']
    }

def parse_date(data, offset, size):
    """解析日期"""
    timestamp = struct.unpack('>d', data[offset:offset + 8])[0]
    return {
        'data': timestamp,
        'size': 8
    }

def parse_long_string(data, offset, size):
    """解析长字符串"""
    length = struct.unpack('>I', data[offset:offset + 4])[0]
    string_data = data[offset + 4:offset + 4 + length].decode('utf-8')
    return {
        'data': string_data,
        'size': 4 + length
    }
