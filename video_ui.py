# video_ui.py
import json
import os
import queue
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
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WL-Video")
        self.root.geometry("400x300+100+100")  # 固定窗口大小
        self.root.configure(bg='#2c3e50')  # 添加背景色


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

        # 图像更新线程
        self.image_update_thread = None
        self.image_update_queue = Queue()

    def create_toolbar(self):
        """创建工具栏"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        # 标签：请选择桌台
        label_table = ttk.Label(toolbar, text="桌台:", font=('Arial', 10), background='#34495e', foreground='white')
        label_table.pack(side=tk.LEFT, padx=5, pady=5)
        config = self.load_config()
        tables = [table['name'] for table in config]
        # 下拉选择框：tables
        self.table_combobox = ttk.Combobox(toolbar, values=tables, width=10)
        self.table_combobox.pack(side=tk.LEFT, padx=5, pady=5)
        self.table_combobox.bind("<<ComboboxSelected>>", self.update_links)

        # 标签：请选择视频流
        label_link = ttk.Label(toolbar, text="视频:", font=('Arial', 10), background='#34495e', foreground='white')
        label_link.pack(side=tk.LEFT, padx=5, pady=5)

        # 下拉选择框：links
        self.link_combobox = ttk.Combobox(toolbar, values=[], width=10)
        self.link_combobox.pack(side=tk.LEFT, padx=5, pady=5)

        # 按钮：开始/停止
        self.start_stop_button = ttk.Button(toolbar, text="开始", command=self.toggle_processing)
        self.start_stop_button.pack(side=tk.LEFT, padx=5, pady=5)

    def update_links(self, event):
        """更新视频流选择框"""
        table_name = self.table_combobox.get()
        config = self.load_config()
        selected_table = next((table for table in config if table['name'] == table_name), None)
        if selected_table:
            links = selected_table["links"]
            self.link_combobox['values'] = [link["type"] if "type" in link else link["url"] for link in links]
            self.link_combobox.current(0)  # 设置默认选择
        else:
            self.link_combobox['values'] = []

    def toggle_processing(self):
        """切换开始/停止处理"""
        if self.running:
            self.stop_processing()
        else:
            self.start_processing()

    def start_processing(self):
        """开始处理流媒体"""
        table_name = self.table_combobox.get()
        link_type = self.link_combobox.get()
        if table_name and link_type:
            logger.info(f"开始处理桌台: {table_name}, 视频流: {link_type}")
            self.root.title = f"WL-Video: {table_name} - {link_type}"
            self.running = True
            self.start_stop_button.config(text="停止")
            self.start_run(table_name, link_type)
        else:
            logger.warning("请选择桌台和视频流")

    def stop_processing(self):
        """停止处理流媒体"""
        logger.info("停止处理流媒体")
        self.running = False
        self.start_stop_button.config(text="开始")
        if self.stream_manager:
            self.stream_manager.stop()
        if self.image_update_thread and self.image_update_thread.is_alive():
            self.image_update_thread.join(timeout=1)  # 等待线程结束

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
            self.panel1.image = self.current_frames[0]  # 保持对 PhotoImage 的引用
            self.panel2.config(image=self.current_frames[1])
            self.panel2.image = self.current_frames[1]  # 保持对 PhotoImage 的引用

        self.task_queue.put(_task)

    def process_queue(self):
        """优化队列处理"""
        try:
            while not self.task_queue.empty():
                task = self.task_queue.get_nowait()
                task()
        finally:
            self.root.after(35, self.process_queue)  # 调整为35毫秒

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

    def load_config(self,config_path='config.json'):
        with open(config_path, 'r', encoding='utf-8') as file:
            config = json.load(file)
        return config['tables']

    def start_run(self, table_name, link_type):
        self.image_update_thread = threading.Thread(target=self._image_update_loop, daemon=True)
        self.image_update_thread.start()

        stream_thread = threading.Thread(target=self._start_run, args=(table_name, link_type), daemon=True)
        stream_thread.start()

    def _image_update_loop(self):
        """图像更新循环"""
        while self.running:
            try:
                frame_images = self.image_update_queue.get(timeout=0.1)
                self.task_queue.put(lambda: self.update_images(frame_images))
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"图像更新错误: {str(e)}")

    def _start_run(self, table_name, link_type):
        logger.info("启动流媒体处理器...")
        config = self.load_config()
        selected_table = next((table for table in config if table['name'] == table_name), None)
        if selected_table:
            selected_link = next((link for link in selected_table["links"] if link.get("type") == link_type or link["url"] == link_type), None)
            if selected_link:
                url = selected_link["url"]
                regions = selected_link["regions"]

                self.stream_manager = bt(data_callback=None, logger=logger, regions=regions, image_callback=self.on_image_ready,table_data=selected_table)
                self.stream_manager.direct_stream_reader(url)
            else:
                logger.warning(f"未找到视频流: {link_type}")
        else:
            logger.warning(f"未找到桌台: {table_name}")
