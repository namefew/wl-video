import os
import tkinter as tk
from queue import Queue
from tkinter import ttk

from PIL import Image, ImageTk
import cv2


# video_ui.py
class VideoUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WL-LongHu")
        self.root.geometry("400x300+100+100")  # 固定窗口大小
        self.root.configure(bg='#2c3e50')  # 添加背景色

        # 主容器
        self.main_frame = ttk.Frame(self.root, width=315, height=300)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 初始化双缓冲
        self.current_frames = [None, None]
        self.display_frames = [None, None]

        # 构建UI
        self.create_image_panels()
        self.create_status_bar()

        # 优化刷新机制
        self.task_queue = Queue()
        self.root.after(50, self.process_queue)

    def create_image_panels(self):
        """重构图像显示区域"""
        img_frame = ttk.Frame(self.main_frame)
        img_frame.pack(fill=tk.BOTH, expand=True)

        # 区域1
        self.panel1 = ttk.Label(img_frame)
        self.panel1.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')

        # 区域2
        self.panel2 = ttk.Label(img_frame)
        self.panel2.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')

        # 配置网格权重
        img_frame.columnconfigure(0, weight=1)
        img_frame.columnconfigure(1, weight=1)
        img_frame.rowconfigure(0, weight=1)

    def create_status_bar(self):
        """重构状态栏"""
        status_frame = ttk.Frame(self.main_frame)
        status_frame.pack(fill=tk.X, pady=5)

        self.status_labels = [
            ttk.Label(status_frame, font=('Arial', 10),  # 减小字体
                      background='#34495e', foreground='white',
                      anchor=tk.CENTER)
            for _ in range(2)
        ]

        self.status_labels[0].pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.status_labels[1].pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

    def update_images(self, frame_images):
        """固定图像尺寸为80x100"""

        def _task():
            TARGET_SIZE = (120, 150)  # 宽x高

            for i in range(2):
                if frame_images[i] is not None:
                    try:
                        # 强制缩放+保持比例填充
                        img = frame_images[i]
                        img = cv2.resize(img, TARGET_SIZE)
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        self.current_frames[i] = ImageTk.PhotoImage(Image.fromarray(img))
                    except Exception as e:
                        print(f"图像处理错误: {str(e)}")

            # 更新显示
            self.panel1.config(image=self.current_frames[0])
            self.panel2.config(image=self.current_frames[1])

        self.task_queue.put(_task)

    def process_queue(self):
        """优化队列处理"""
        try:
            while not self.task_queue.empty():
                task = self.task_queue.get_nowait()
                task()
        finally:
            self.root.after(50, self.process_queue)  # 调整为20fps

    def run(self):
        """启动主循环"""
        self.root.mainloop()

    def update_labels(self, text1, text2):
        """标签实时更新"""
        def _task():
            self.status_labels[0].config(text=text1)
            self.status_labels[1].config(text=text2)
            # 强制重绘
            self.root.update_idletasks()
        if text1 and text2:
            self.task_queue.put(_task)

    def on_close(self):
        """安全关闭窗口"""
        self.root.destroy()
        os._exit(0)  # 强制结束所有线程

    def drag_window(self, event):
        """实现窗口拖动"""
        x = self.root.winfo_pointerx() - self._offsetx
        y = self.root.winfo_pointery() - self._offsety
        self.root.geometry(f"+{x}+{y}")

    def click_window(self, event):
        """记录窗口拖动起始位置"""
        self._offsetx = event.x
        self._offsety = event.y
