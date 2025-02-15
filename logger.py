import logging

class LogManager:
    @staticmethod
    def setup():
        # 创建一个日志记录器
        logger = logging.getLogger('VideoAnalysisLogger')
        logger.setLevel(logging.DEBUG)

        # 创建一个控制台处理器
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # 创建一个格式化器
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # 将格式化器添加到处理器
        ch.setFormatter(formatter)

        # 将处理器添加到日志记录器
        logger.addHandler(ch)

        return logger
