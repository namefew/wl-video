from wasmtime import Engine, Store, Module, Instance, Memory, MemoryType, Limits,  Val
import ctypes
# 创建存储和引擎
store = Store(Engine())
module = Module.from_file(store.engine, 'decrypt.wasm')  # 直接加载wasm文件

# 配置内存（自动匹配WASM模块定义）
memory_type = MemoryType( Limits(11,11))
memory = Memory(store, memory_type)

# 构建导入对象
imports = {}

# 实例化模块
instance = Instance(store, module, imports)

# 获取导出函数
exports = instance.exports(store)
mem = exports['a']
decrypt = exports['c']
current_offset = 0
WASM_MEM_SIZE = 11*65535


def decrypt_function(src_data: bytes) -> bytes:
    global current_offset

    data_len = len(src_data)
    required_size = data_len + 4  # 保留头部4字节

    # 内存循环使用逻辑
    if current_offset + required_size > WASM_MEM_SIZE:
        current_offset = 0

    # 获取WASM内存视图
    wasm_buf = (ctypes.c_ubyte * WASM_MEM_SIZE).from_address(
        ctypes.addressof(mem.data_ptr(store).contents)
    )

    # 内存拷贝
    ctypes.memmove(
        ctypes.byref(wasm_buf, current_offset),  # 目标地址
        src_data,  # 源数据
        data_len
    )

    # 调用解密函数
    decrypt(store,
            Val.i32(current_offset),  # 起始偏移
            Val.i32(4),  # 操作起始位置
            Val.i32(data_len - 4)  # 操作长度
            )

    # 读取结果
    result = bytes(wasm_buf[current_offset: current_offset + data_len])

    current_offset += required_size
    return result
