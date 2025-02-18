from logger import LogManager
from stream_manager import bt
import time

logger = LogManager.setup()

# 生成唯一文件名（时间戳方式）
filename = f"wl_video_{int(time.time())}.flv"

# 写入文件

def callback(*args):
    if args[1] and args[1]['data'] :
        with open(filename, 'ab') as f:
            f.write(args[1]['data'])
    logger.info("callback called with args: %s", args)


if __name__ == "__main__":

    logger.info("starting ...")
    streamManager = bt(callback, logger=logger)
    streamManager.direct_stream_reader('https://pl2079.gslxqy.com/live/v2flv_L01_2.flv')