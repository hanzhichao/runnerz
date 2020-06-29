import threading


class MyThread(threading.Thread):
    def __init__(self, func, *args, **kwargs):  # 改变线程的使用方式，可以直接传递函数方法和函数参数
        super(MyThread, self).__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.result = None

    def run(self):
        self.result = self.func(*self.args, **self.kwargs)  # 为线程添加属性result存储运行结果

