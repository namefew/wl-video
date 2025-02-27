import threading

from video_ui import VideoUI



if __name__ == "__main__":
    tables = ['龙虎L01', '极速B07']
    # 在主线程启动UI
    video_ui = VideoUI(tables=tables)

    # 主线程运行UI
    video_ui.run()
