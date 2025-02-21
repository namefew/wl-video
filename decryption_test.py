
from decryption_module import decrypt_function

def test_decrypt_function():
    # 读取src.txt并构造字节数组
    with open('src0.txt', 'r') as f:
        src_data = []
        for line in f:
            cleaned = line.strip().replace('\n', '').replace(' ', '').replace('[','').replace(']','')
            src_data.extend([int(x) for x in cleaned.split(',') if x])


    # 读取结果（带缓冲区保护）
    result = decrypt_function(bytearray(src_data))

    # 写入dest2.txt（按源文件格式）
    with open('dest2.txt', 'w') as f:
        f.write(f"[{','.join(str(b) for b in result)}]")

    # 比较文件差异
    import filecmp
    are_equal = filecmp.cmp('dest0.txt', 'dest2.txt', shallow=False)
    print(f"文件内容{'相同' if are_equal else '不同'}")


# 执行测试
test_decrypt_function()
