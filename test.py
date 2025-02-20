import subprocess

# 假设 nalus 是一个包含NALU单元的列表

def write_nalus_to_file(nalus, output_file):
    with open(output_file, 'wb') as f:
        for unit in nalus:
            f.write(unit['data'])

def convert_nalus_to_h264(nalu_file, h264_file):
    command = [
        'ffmpeg', '-i', nalu_file,
        '-c:v', 'h264',
        '-b:v', '800k',
        '-r', '25',
        '-vf', '"scale=1260:1080"',
        '-profile:v', 'high',
        '-level', '4.0',
        '-pix_fmt', 'yuv420p',
        h264_file
    ]
    subprocess.run(command, check=True)

def wrap_h264_to_mp4(h264_file, mp4_file):
    command = [
        'ffmpeg', '-i', h264_file, '-c', 'copy', mp4_file
    ]
    subprocess.run(command, check=True)

# 步骤 1: 写入NALU单元到文件
nalu_file_path = 'temp_nalus.bin'

# 步骤 2: 使用FFmpeg转换为H.264格式
h264_output_file = 'nalus-to-h264.h264'
convert_nalus_to_h264(nalu_file_path, h264_output_file)

# 步骤 3: 封装为MP4容器
mp4_output_file = 'h264-to-mp4.mp4'
wrap_h264_to_mp4(h264_output_file, mp4_output_file)
