import av
import subprocess

def check_env():
    # 检查CUDA
    cuda_ok = subprocess.run("nvcc --version", shell=True).returncode == 0

    # 检查FFmpeg
    ffmpeg_ok = False
    try:
        res = subprocess.check_output("ffmpeg -hwaccels", shell=True)
        ffmpeg_ok = b'cuda' in res
    except: pass

    # 检查NVCUVID动态库是否可访问
    import ctypes
    ctypes.WinDLL('nvcuvid.dll')  # 关键检查项

    # 增强版解码器检测
    decoders = av.codec.get_decoders()
    cuvid_decoders = [
        f"{d.name} ({', '.join(d.video_codecs)})"
        for d in decoders
        if 'cuvid' in d.name.lower()
    ]
    print("CUVID解码器列表：\n" + '\n'.join(cuvid_decoders) if cuvid_decoders else "未检测到CUVID解码器")

    # 最终正确的PyAV检查方式
    av_ok = False
    try:
        # 获取所有H264解码器
        decoders = av.codec.get_decoders('h264')
        print("PyAV支持的H264解码器:")
        decoder_names = [d.name for d in decoders]
        print(decoder_names)
        av_ok = any('cuvid' in name.lower() for name in decoder_names)
    except Exception as e:
        print(f"PyAV检查异常: {str(e)}")
    print(f"[PyAV cuvid] {'√' if av_ok else '×'}")

    print(f"[CUDA] {'√' if cuda_ok else '×'}")
    print(f"[FFmpeg] {'√' if ffmpeg_ok else '×'}")

if __name__ == "__main__":
    check_env()
