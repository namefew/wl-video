from logger import LogManager
from stream_manager import bt

logger = LogManager.setup()
def callback(*args):
    logger.info("callback called with args: %s", args)


if __name__ == "__main__":

    logger.info("starting ...")
    streamManager = bt(None, logger)
    streamManager.direct_stream_reader('https://pl2079.gslxqy.com/live/v2flv_L01_2.flv')