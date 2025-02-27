# video_ui.py
import os
import threading
import tkinter as tk
from queue import Queue
from tkinter import ttk

import numpy as np
from PIL import Image, ImageTk
import cv2

from logger import LogManager
from stream_manager import bt

logger = LogManager.setup()

# video_ui.py
class VideoUI:
    def __init__(self, tables=None):
        self.root = tk.Tk()
        self.root.title("WL-LongHu")
        self.root.geometry("400x300+100+100")  # 固定窗口大小
        self.root.configure(bg='#2c3e50')  # 添加背景色

        # 初始化桌台数据
        self.tables = tables

        # 创建工具栏
        self.create_toolbar()

        # 主容器
        self.main_frame = ttk.Frame(self.root, width=300, height=280)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 初始化双缓冲
        self.current_frames = [None, None]
        self.display_frames = [None, None]

        # 构建UI
        self.create_image_panels()
        self.create_status_bar()

        # 优化刷新机制
        self.task_queue = Queue()
        self.root.after(35, self.process_queue)

        # 流媒体处理线程
        self.stream_manager = None
        self.running = False

    def create_toolbar(self):
        """创建工具栏"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        # 标签：请选择桌台
        label = ttk.Label(toolbar, text="请选择桌台:", font=('Arial', 10), background='#34495e', foreground='white')
        label.pack(side=tk.LEFT, padx=5, pady=5)

        # 下拉选择框：tables
        self.table_combobox = ttk.Combobox(toolbar, values=self.tables, width=20)
        self.table_combobox.pack(side=tk.LEFT, padx=5, pady=5)

        # 按钮：开始/停止
        self.start_stop_button = ttk.Button(toolbar, text="开始", command=self.toggle_processing)
        self.start_stop_button.pack(side=tk.LEFT, padx=5, pady=5)

    def toggle_processing(self):
        """切换开始/停止处理"""
        if self.running:
            self.stop_processing()
        else:
            self.start_processing()

    def start_processing(self):
        """开始处理流媒体"""
        table_name = self.table_combobox.get()
        if table_name:
            logger.info(f"开始处理桌台: {table_name}")
            self.running = True
            self.start_stop_button.config(text="停止")
            self.start_run(table_name)
        else:
            logger.warning("请选择桌台")

    def stop_processing(self):
        """停止处理流媒体"""
        logger.info("停止处理流媒体")
        self.running = False
        self.start_stop_button.config(text="开始")
        self.stream_manager.stop()


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
            self.root.after(35, self.process_queue)  # 调整为20fps

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

    def on_image_ready(self, event):
        # 添加数据校验
        if 'images' not in event or 'labels' not in event:
            return
        if len(event['labels']) != 2:
            return
        self.update_labels(event['labels'][0], event['labels'][1])
        for i in range(len(event['images'])):
            sub_imgs = event['images'][i]
            # 显式拷贝图像数据
            safe_images = [np.copy(img) for img in sub_imgs]
            self.update_images(safe_images)

    def start_run(self, table_name):
        stream_thread = threading.Thread(target=self._start_run, args=(table_name,), daemon=True)
        stream_thread.start()

    def _start_run(self, table_name):
        logger.info("启动流媒体处理器...")
        tables = [{'table_id': 8801, 'name': '龙虎L01',
                   'links': [{'url': 'https://pl2079.gslxqy.com/live/v2flv_L01_2.flv',
                             'regions': [(486, 924, 94, 96),(724, 924, 94, 96)]},
                            {'url': 'https://pl2079.gslxqy.com/live/v2flv_L01_2_l.flv',
                             'regions': [(324, 615, 62, 62), (483, 615, 62, 62)]}
                            ]
                   },
                  {'table_id': 8802, 'name': '极速B07',
                   'links': [{ 'url': 'https://pl1653.cslyxs.cn/live/v3flv_B07_2.flv',
                            'regions': [(508-78, 838-82, 78, 80),(508+4, 838-82, 78, 80)]},
                            {'url': 'https://pl1653.cslyxs.cn/live/v3flv_B07_1.flv',
                             'regions': [(508-78, 838-82, 78, 80),(508+4, 838-82, 78, 80)]},
                            {'url': 'https://pl1653.cslyxs.cn/live/v3flv_B07_1_l.flv',
                             'regions': [(324, 615, 62, 62), (483, 615, 62, 62)]}
                            ]
                   }]
        selected_table = next((table for table in tables if table['name'] == table_name), None)
        if selected_table:
            link = selected_table["links"][0]
            url = link["url"]
            regions = link["regions"]

            self.stream_manager = bt(data_callback=None, logger=logger, regions=regions, image_callback=self.on_image_ready)
            self.stream_manager.direct_stream_reader(url)
        else:
            logger.warning(f"未找到桌台: {table_name}")
