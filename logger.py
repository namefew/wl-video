import logging
from colorama import Fore, Style, init

# 初始化 colorama
init(autoreset=True)

class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, Fore.RESET)
        record.msg = f"{log_color}{record.msg}{Style.RESET_ALL}"
        return super().format(record)

class LogManager:
    @staticmethod
    def setup():
        # 创建一个日志记录器
        logger = logging.getLogger('MAIN')

        # 避免重复添加处理器
        if not logger.hasHandlers():
            logger.setLevel(logging.DEBUG)

            # 创建一个控制台处理器
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)

            # 创建一个自定义格式化器
            formatter = ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

            # 将格式化器添加到处理器
            ch.setFormatter(formatter)

            # 将处理器添加到日志记录器
            logger.addHandler(ch)

            # 创建一个文件处理器
            fh = logging.FileHandler('app.log')
            fh.setLevel(logging.DEBUG)
            fh_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            fh.setFormatter(fh_formatter)
            logger.addHandler(fh)

        return logger

# 设置日志记录器
logger = LogManager.setup()

# 记录日志
logger.debug("This is a debug message")
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")
logger.critical("This is a critical message")

# 示例：正确使用 logging.info
logger.info("onMediaInfo: %s", "some data")
