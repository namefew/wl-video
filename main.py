import threading

import numpy as np

from logger import LogManager
from stream_manager import bt
from video_ui import VideoUI

logger = LogManager.setup()

def callback(*args):
    """流回调函数"""
    if args[0] == "video" and args[1]:
        data = args[1].get('data')
        if data:
            try:
                # 将数据发送给处理器
                logger.debug(f"写入 {len(data)} bytes 到解码器")
            except Exception as e:
                logger.error(f"数据处理失败: {str(e)}")
        else:
            logger.warning("收到空视频数据")


# 修改on_image_ready回调
def on_image_ready(event):
    # 添加数据校验
    if 'images' not in event or 'labels' not in event:
        return
    if len(event['labels']) != 2:
        return
    video_ui.update_labels(event['labels'][0], event['labels'][1])
    for i in range(len(event['images'])):
        sub_imgs = event['images'][i]
        # 显式拷贝图像数据
        safe_images = [np.copy(img) for img in sub_imgs]
        video_ui.update_images(safe_images)


def start_stream():
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
    table = tables[0]
    link = table["links"][0]
    url = link["url"]
    regions = link["regions"]

    stream_manager = bt(data_callback=None, logger=logger, regions=regions, image_callback=on_image_ready)
    stream_manager.direct_stream_reader(url)



if __name__ == "__main__":
    logger.info("启动流媒体处理器...")
    # 在主线程启动UI
    video_ui = VideoUI()

    stream_thread = threading.Thread(target=start_stream, daemon=True)
    stream_thread.start()

    # 主线程运行UI
    video_ui.run()
