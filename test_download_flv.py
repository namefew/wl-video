import requests
import time

url = "https://media-pull.bornin80s.live/daabfh/videosd.flv?wsSecret=1eb5a451cac7b8db1c1bf5af69807e89&wsABSTime=67B1EC54"
url = "https://media-pull.bornin80s.live/daabfh/videosd.flv?wsSecret=0ab0b1ee42890cf2cdadf0a2e95c39c7&wsABSTime=67B1EF7C"
url = "https://re.kjzao.cn/nw09/8-91D.flv"
url = "https://wmvdo.hongen.me/live116/720p.flv"
try:
    # 发送 GET 请求（stream 模式适用于大文件）
    response = requests.get(url, stream=True)
    response.raise_for_status()  # 检查 HTTP 错误
    
    # 生成唯一文件名（时间戳方式）
    filename = f"video_{int(time.time())}.flv"
    
    # 写入文件
    with open(filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:  # 过滤保持连接的 chunk
                f.write(chunk)
    
    print(f"文件已保存为：{filename}")

except requests.exceptions.RequestException as e:
    print(f"下载失败: {e}")
except Exception as e:
    print(f"发生错误: {e}")
