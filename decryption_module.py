import base64

from wasmtime import Store, Module, Instance, MemoryType, Memory

# 创建一个存储对象
store = Store()

# 解码 Base64 字符串为字节数据
wasm_bytes = base64.b64decode("AGFzbQEAAAABDwNgAABgAn9/AGADf39/AAMEAwABAgQFAXABAQEFBAEBCwsHFQUBYQIAAWIAAAFjAAIBZAABAWUBAAqvAwMDAAELyAEBBX8gAUEDTgRAQQIgAUEBayICIAJBAk8bIgNBf3MhBSACIQQgASADa0EBcQRAIAAgAUECayIEaiIDIAMtAAAgAnMgACABakEDay0AAGs6AAALQQAgAWkgBUcEQANAIAAgBEEBayIDaiIBIAEtAAAgAnMgACAEQQJrIgFqIgUtAAAiBms6AAAgBSACIAZzIAAgBGpBA2stAABrOgAAIAEhBCADQQJLDQALCyAAIAAtAAAgAkEYdiACQRB2c3MgAkEIdms6AAALC94BAQV/AkACQAJAAn8CQCAAIAFqIgAtAAANACAALQABDQBBAyAALQACQQFGDQEaIAAtAAINAEEEIAAtAANBAUYNARoLQQALIgEgAGoiBC0AACIAQeEAaw4FAQICAgEACyAAQcEARw0BCyABQX9zIAJqIgBBAkgNACAEQQFqIQIgAEEYdiEFIABBEHYhBiAAQQh2IQcgACEBA0AgASAEaiIDIAMtAAAgAHMgASACakECay0AAGs6AAAgAUECSyEDIAFBAWshASADDQALIAIgAi0AACAFIAZzcyAHazoAAAsL");
with open("module.wasm", "wb") as f:
    f.write(wasm_bytes)
# 加载 WebAssembly 模块
module = Module(store.engine, wasm_bytes)

# 创建内存导入
memory_type = MemoryType(Limits='{min=2,max=128}')  # 至少1页内存
memory = Memory(store, memory_type)

# 实例化模块，提供内存导入
instance = Instance(store, module, [memory])

# 调用导出的函数
decryption_export= instance.exports(store)
decrypt_func = decryption_export["c"]
decrypt_mem = decryption_export["a"]
