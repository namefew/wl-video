# 模拟WebAssembly内存的字节数组
memory = bytearray(11 * 65536)  # 模拟初始内存大小（11页，每页64KB）


def b():
    """等效于函数$b的nop操作"""
    pass


def d(var0, var1):
    """处理字节数组的转换函数"""
    if var1 >= 3:
        var2 = var1 - 1
        var3 = 2 if var2 >= 2 else var2
        var5 = ~var3  # 等效i32.xor -1
        var4 = var2

        if (var1 - var3) & 1:
            var4 = var1 - 2
            addr = var0 + var4
            memory[addr] = (memory[addr] ^ var2) - memory[var0 + var1 - 3]

        if (-var1) != var5:
            while True:
                var3 = var4 - 1
                addr1 = var0 + var3
                temp1 = (memory[addr1] ^ var2) - memory[var0 + var4 - 2]
                memory[addr1] = temp1 & 0xFF  # 保持字节范围

                addr2 = var0 + var4 - 2
                temp2 = (memory[addr2] ^ var2) - memory[var0 + var4 + 1]
                memory[addr2] = temp2 & 0xFF

                var4 = var4 - 2
                if var3 <= 2:
                    break

        # 处理第一个字节
        xor_val = (var2 >> 24) ^ (var2 >> 16)
        memory[var0] = (memory[var0] ^ xor_val) - (var2 >> 8)


def c(var0, var1, var2):
    """带条件分支的复杂处理函数"""
    ptr = var0 + var1
    header = ptr  # WASM中var0被重新赋值为ptr

    # 检测头字节模式（严格匹配WASM的地址偏移）
    if memory[header] == 0 and memory[header + 1] == 0:
        if memory[header + 2] == 1:
            var1 = 3
        elif memory[header + 2] == 0 and memory[header + 3] == 1:
            var1 = 4

    var4 = header + var1
    if var1 == 0:
        return

    byte_val = memory[var4]

    # 严格匹配br_table逻辑（修正地址引用错误）
    if byte_val == 97:  # 'a'走label2
        pass
    elif byte_val == 101:  # 'e'走label4
        # WASM实际检查的是header地址处的值（原var0位置）
        if memory[header] != 65:  # 0x41='A'
            return
    else:
        return

    # 32位无符号运算处理
    remaining = (var2 - var1 - 1) % 0x100000000

    if remaining < 2:
        return

    var2_ptr = var4 + 1
    # 无符号右移处理
    shifts = (
        (remaining >> 24) & 0xFF,
        (remaining >> 16) & 0xFF,
        (remaining >> 8) & 0xFF,
        remaining & 0xFF
    )

    # 无符号循环条件
    var1 = remaining
    while (var1 % 0x100000000) > 2:  # 模拟i32.gt_u
        addr = var4 + (var1 & 0xFFFFFFFF)  # 处理32位溢出
        xor_val = remaining & 0xFF  # 确保异或操作使用低8位
        memory[addr] = ((memory[addr] ^ xor_val) - memory[var2_ptr + (var1 - 2)]) % 256
        var1 = (var1 - 1) % 0x100000000  # 模拟i32.sub

    # 最终字节处理（带符号修正）
    xor_val = (shifts[0] ^ shifts[1]) & 0xFF
    final = (memory[var2_ptr] ^ xor_val) - shifts[2]
    memory[var2_ptr] = final % 256  # 确保字节范围


def test_c_function():
    # 读取src.txt并构造字节数组
    with open('src.txt', 'r') as f:
        src_data = []
        for line in f:
            # 处理可能存在的换行拼接问题
            cleaned = line.strip().replace('\n', '').replace(' ', '').replace('[','').replace(']','')
            src_data.extend([int(x) for x in cleaned.split(',') if x])

    # 初始化内存（扩展内存容量）
    global memory
    required_size = len(src_data)
    if len(memory) < required_size:
        memory.extend(bytearray(required_size - len(memory)))

    # 将src数据填充到内存（从地址0开始）
    for i in range(len(src_data)):
        memory[i] = src_data[i]

    # 执行c函数
    c(0, 4, len(src_data) - 4)  # 参数：var0=0, var1=4, var2=len-4

    # 提取结果数据
    result = memory[:len(src_data)]

    # 写入dest1.txt（按源文件格式）
    with open('dest2.txt', 'w') as f:
        f.write(f"[{','.join(str(b) for b in result)}]")

    # 比较文件差异
    import filecmp
    are_equal = filecmp.cmp('dest.txt', 'dest2.txt', shallow=False)
    print(f"文件内容{'相同' if are_equal else '不同'}")


# 执行测试
test_c_function()

