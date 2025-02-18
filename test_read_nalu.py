import cv2

def decode_nalus_to_frames(nalu_file, output_dir):
    # 打开 NALU 文件
    with open(nalu_file, 'rb') as f:
        nalu_data = f.read()

    # 创建 VideoCapture 对象
    cap = cv2.VideoCapture(nalu_file, cv2.CAP_FFMPEG)

    # 检查是否成功打开
    if not cap.isOpened():
        print("Error: Could not open NALU file.")
        return

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 保存帧为图像文件
        frame_path = f"{output_dir}/frame_{frame_count:04d}.jpg"
        cv2.imwrite(frame_path, frame)
        print(f"Saved frame {frame_count} to {frame_path}")
        frame_count += 1

    cap.release()
    print(f"Total frames saved: {frame_count}")

if __name__ == "__main__":
    nalu_file = 'temp_nalus.bin'
    output_dir = 'output_frames'
    decode_nalus_to_frames(nalu_file, output_dir)
