from logger import LogManager
from stream_manager import bt
import time

logger = LogManager.setup()

# 生成唯一文件名（时间戳方式）
filename = f"wl_video_{int(time.time())}.flv"

# 写入文件

def callback(*args):
    if "video" == args[0] and args[1]:
        data = args[1].get('data')
        detail = args[1].get('detail')

        if data and detail:
            # 处理数据
            with open(filename, 'ab') as f:
                f.write(args[1]['data'])
                logger.info(f"write size:{len(args[1]['data'])}")
        else:
            print("Missing 'data' or 'detail' in args[1]:", args[1])



if __name__ == "__main__":

    logger.info("starting ...")
    streamManager = bt(callback, logger=logger)
    streamManager.direct_stream_reader('https://pl2079.gslxqy.com/live/v2flv_L01_2.flv')