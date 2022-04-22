from concurrent.futures.thread import ThreadPoolExecutor


class ThreadPool(object):
    def __init__(self):
        # 线程池
        self.executor = ThreadPoolExecutor(2000)
        # 用于存储期程
        self.future_dict = {}

    # 检查worker线程是否正在运行
    def is_running(self, tag):
        future = self.future_dict.get(tag, None)
        if future and future.running():
            # 存在正在运行的任务
            return True
        return False

    # 展示所有的异步任务
    def check_future(self):
        data = {}
        for tag, future in self.future_dict.items():
            data[tag] = future.running()
        return data

    def __del__(self):
        self.executor.shutdown()


# 主线程中的全局线程池
# global_thread_pool的生命周期是Django主线程运行的生命周期
global_thread_pool = ThreadPool()
