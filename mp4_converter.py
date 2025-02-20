# 新增mp4_writer.py
import subprocess

class MP4Converter:
    @staticmethod
    def convert_to_mp4(input_h264, output_mp4):
        """
        使用FFmpeg封装为MP4
        :param input_h264: 输入的H.264裸流文件
        :param output_mp4: 输出的MP4文件
        """
        command = [
            'ffmpeg',
            '-y',                # 覆盖输出文件
            '-f', 'h264',        # 输入格式
            '-i', input_h264,    # 输入文件
            '-c:v', 'copy',      # 视频直接拷贝
            '-movflags', 'faststart',  # 适合流式播放
            output_mp4
        ]
        
        try:
            subprocess.run(command, check=True, stderr=subprocess.PIPE)
            print(f"成功生成MP4文件: {output_mp4}")
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg封装失败: {e.stderr.decode()}")
