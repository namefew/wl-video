from wasmtime import Engine, Store, Module, Instance, Memory, MemoryType, Limits,  Val
import ctypes
import wasmtime
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

def decrypt_function(src_data):
    # 读取src.txt并构造字节数组
    ptr = ctypes.cast(mem.data_ptr(store), ctypes.POINTER(ctypes.c_ubyte))
    # 内存写入（安全方式）
    src_bytes = bytes(src_data)
    ctypes.memmove(ptr, src_bytes, len(src_bytes))

    # 调用解密函数（参数验证）
    try:
        # 使用 store.call 方法来调用 Func 对象，并传递所有参数
        decrypt(store,
            Val.i32(0),  # 起始偏移量
            Val.i32(4),  # 操作起始位置
            Val.i32(len(src_bytes) - 4)  # 操作长度
        )
    except TypeError as e:
        print(f"函数调用参数错误: {str(e)}")
        return
    except wasmtime._error.WasmtimeError as e:
        print(f"Wasmtime 错误: {str(e)}")
        return

    # 读取结果（带缓冲区保护）
    result = bytes(ptr[i] for i in range(len(src_data)))

    return result
