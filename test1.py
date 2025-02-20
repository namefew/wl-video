import subprocess
import os

def extract_frames_from_flv(input_file, output_folder):
    # 确保输出文件夹存在
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

        # FFmpeg 命令
    command = [
        'ffmpeg', '-i', input_file,
        '-vf', 'fps=1',  # 每秒提取一帧
        '-loglevel', 'info',  # 更详细的日志输出
        f'{output_folder}/frame_%04d.png'  # 输出文件名格式
    ]

    # 执行 FFmpeg 命令
    subprocess.run(command, check=True)

import struct

def add_header_to_flv(input_file, output_file):
    # 读取原始文件内容
    with open(input_file, 'rb') as f:
        original_content = f.read()

    # 定义要添加的头部信息
    header_info = "video/mp4;codecs=avc1.640028"

    # 将头部信息转换为字节
    header_bytes = header_info.encode('utf-8')

    # 计算头部信息的长度
    header_length = len(header_bytes)

    # 创建一个新的文件并写入头部信息
    with open(output_file, 'wb') as f:
        # 写入头部信息的长度
        f.write(struct.pack('<I', header_length))
        # 写入头部信息
        f.write(header_bytes)
        # 写入原始文件内容
        f.write(original_content)


if __name__ == "__main__":
    # 指定输入和输出文件路径
    input_file = 'wl_video_1739963092.flv'
    # output_file = 'wl_video_1739869263_with_header.flv'

    # 调用函数添加头部信息
    # add_header_to_flv(input_file, output_file)

    # # input_file = 'videos/video_1739713504.flv'
    output_folder = 'videos/wl_video_1739963092'
    #
    extract_frames_from_flv(input_file, output_folder)
