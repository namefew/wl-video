import struct
import threading
import time
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageTk
import av
import cv2
import numpy as np
import requests


class VideoDecoder:
    def __init__(self, on_frame_decoded):
        self._codec_ctx = None
        self.on_frame_decoded = on_frame_decoded
        self._executor = ThreadPoolExecutor(max_workers=1)
        self.sps = None
        self.pps = None

    def init_decoder(self, sps, pps):
        # 构建extradata (AVCDecoderConfigurationRecord)
        extradata = bytes([0x01]) + sps[1:4]
        extradata += bytes([0xff, 0xe1])
        extradata += len(sps).to_bytes(2, 'big') + sps
        extradata += bytes([0x01])
        extradata += len(pps).to_bytes(2, 'big') + pps

        try:
            # 优先尝试硬件解码
            codec = av.Codec('h264_cuvid', 'r')
            self._codec_ctx = av.CodecContext.create(codec)
            self._codec_ctx.options = {
                'gpu': '0',
                'output_format': 'bgr24',
                'flags': '+low_delay'
            }
            print("Hardware decoder initialized successfully")
        except Exception as e:
            print("Hardware decoder failed:", str(e))
            # 回退到软件解码
            codec = av.Codec('h264', 'r')
            self._codec_ctx = av.CodecContext.create(codec)

        self._codec_ctx.extradata = extradata
        self._codec_ctx.open(codec)

    def decode_nalu(self, nalu_data):
        if not self._codec_ctx:
            return

        def _decode():
            try:
                packets = self._codec_ctx.parse(nalu_data)
                frames = []
                for packet in packets:
                    decoded = self._codec_ctx.decode(packet)
                    frames.extend([f.to_ndarray(format='bgr24') for f in decoded])

                if frames:
                    self.on_frame_decoded(frames)
            except Exception as e:
                print(f"解码错误: {str(e)}")

        self._executor.submit(_decode)


class FLVPlayer:
    def __init__(self, url):
        self.root = tk.Tk()
        self.root.title("FLV实时播放器")
        self.video_label = tk.Label(self.root)
        self.video_label.pack()

        self.decoder = VideoDecoder(self._update_ui)
        self.buffer = bytearray()
        self.running = True
        self.lock = threading.Lock()
        self.last_frame_time = 0
        self.has_skipped_flv_header = False

        # 启动网络线程
        threading.Thread(target=self._fetch_stream, args=(url,), daemon=True).start()
        self.root.mainloop()

    def _fetch_stream(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            }
            with requests.get(url, headers=headers, stream=True, timeout=5) as res:
                print(f"Response status: {res.status_code}")
                for chunk in res.iter_content(40960):
                    if not self.running:
                        break
                    print(f"Received chunk of size: {len(chunk)}")
                    self._parse_flv(chunk)
        except Exception as e:
            print(f"网络错误: {str(e)}")
            self._shutdown()

    def _parse_flv(self, data):
        with self.lock:
            self.buffer.extend(data)

            # Step 1: Skip FLV Header
            if not self.has_skipped_flv_header:
                if len(self.buffer) >= 9:
                    flv_header = self.buffer[:9]
                    if flv_header[0] == 70 and flv_header[1] == 76 and flv_header[2] == 86:
                        del self.buffer[:9]
                        self.has_skipped_flv_header = True
                    else:
                        print("Invalid FLV header")
                        self.buffer.clear()
                        return
                else:
                    return

            while len(self.buffer) >= 11:
                # Step 2: Resync if invalid tag type
                if self.buffer[0] not in (8, 9, 18):
                    self.buffer.pop(0)
                    continue

                header = self.buffer[:11]
                tag_type = header[0]
                data_size = struct.unpack('>I', b'\x00' + header[1:4])[0]
                total_size = data_size + 15

                if len(self.buffer) < total_size + 4:
                    break

                # Step 3: Validate PreviousTagSize
                prev_tag_size = struct.unpack('>I', self.buffer[total_size:total_size+4])[0]
                if prev_tag_size != data_size + 11:
                    print("PreviousTagSize mismatch, possible data corruption")
                    self.buffer.pop(0)
                    continue

                tag_data = self.buffer[11:11 + data_size]
                del self.buffer[:total_size + 4]

                if tag_type == 9:
                    print(f"Processing video tag of size: {data_size}")
                    self._process_video(tag_data)

    def _process_video(self, data):
        avc_type = data[0]
        print(f"AVC Type: {avc_type}")
        if avc_type == 0:
            print("Parsing AVCDecoderConfigurationRecord")
            self._parse_avcc(data[5:])
        elif avc_type == 1:
            print("Processing NALUs")
            self._process_nalus(data[5:])
        else:
            print(f"未知的 AVC 类型: {avc_type}")

    def _parse_avcc(self, data):
        sps_count = data[5] & 0x1f
        pos = 6
        for _ in range(sps_count):
            sps_len = struct.unpack('>H', data[pos:pos + 2])[0]
            self.sps = data[pos + 2:pos + 2 + sps_len]
            pos += 2 + sps_len

        pps_count = data[pos]
        pos += 1
        for _ in range(pps_count):
            pps_len = struct.unpack('>H', data[pos:pos + 2])[0]
            self.pps = data[pos + 2:pos + 2 + pps_len]
            pos += 2 + pps_len

        if self.sps and self.pps:
            self.decoder.init_decoder(self.sps, self.pps)

    def _process_nalus(self, data):
        def safe_split_nalus(data):
            start_code = b'\x00\x00\x00\x01'
            pos = 0
            while pos < len(data):
                idx = data.find(start_code, pos)
                if idx == -1:
                    break
                next_idx = data.find(start_code, idx + 4)
                end = next_idx if next_idx != -1 else len(data)
                yield data[idx:end]
                pos = end

        for nalu in safe_split_nalus(data):
            if len(nalu) > 4:
                self.decoder.decode_nalu(nalu)

    def _update_ui(self, frames):
        now = time.time()
        if now - self.last_frame_time < 0.033:  # ~30fps
            return

        self.last_frame_time = now
        if frames:
            print("Updating UI with new frame")
            self.root.after(0, self._show_frame, frames[0])

    def _show_frame(self, frame):
        try:
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img).resize((1280, 720))
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.configure(image=imgtk)
            self.video_label.image = imgtk
            print("Frame displayed successfully")
        except Exception as e:
            print(f"显示错误: {str(e)}")

    def _shutdown(self):
        self.running = False
        self.root.destroy()


if __name__ == "__main__":
    FLVPlayer("https://pu300.bighit888.com/livestream/dtg01-1.flv")
