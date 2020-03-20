# pipline -> stage -> step
# testsuite -> testcase -> teststep (keyword)
# 支持状态机,权限,工作流
import requests



class Base(object):
    """基础模型"""
    def __init__(self, *args, **kwargs):
        # 属性 ----------------
        self.name = kwargs.get('name')
        self.description = kwargs.get('description')
        self.timeout = kwargs.get('timeout')  # 超时时间

        # 输入输出 ----------------
        self.options = kwargs.get('options')  # 需要输入的参数
        self.result = kwargs.get('result')  # 执行结果  # self.returns
        self.status = kwargs.get('status')  # 执行状态

        # 运行控制
        self.variables = kwargs.get('variables')  # 注册变量
        self.configs = kwargs.get('configs')  # 方法默认配置 {request: ...}
        self.timeout = kwargs.get('timeout')  # 超时时间
        self.re_runs = kwargs.get('optre_runsions')  # 重跑次数, 支持失败重跑,时间间隔,总是重跑

        # 请求前后
        self.hooks = kwargs.get('hooks')  # 钩子方法, pre, skip_if, on_error, post




class Pipeline(Base):
    """流程"""
    def __init__(self):
        super().__init__()
        # 属性 ----------------
        self.tags = None  # 标签
        self.level = None   # 等级

        self.triggers = None  # 触发器

        # 运行控制

        self.parameters = None  # 参数化变量
        self.agent = None  # 运行节点
        self.timeout = None  # 超时时间
        self.run_type = None  #  运行方式,顺序,乱序,并行,指定顺序

        self.setups = None  # 请求前步骤  self.skip_ifs = None  # 请求前检查
        self.teardowns = None  # 请求后步骤  # self.checks = None  # 断言  # self.extract = None  # 提取语句

        # 其他
        self.watches = None # 关注人

        self.stages = []


class Stage(Base):
    """阶段"""
    def __init__(self):
        super().__init__()
        # 属性 ----------------
        self.tags = None  # 标签
        self.level = None  # 等级

        # 运行控制
        self.parameters = None  # 参数化变量
        self.agent = None  # 运行节点
        self.run_type = None  # 运行方式,顺序,乱序,并行,指定顺序


        self.setups = None  # 请求前步骤  self.skip_ifs = None  # 请求前检查
        self.teardowns = None  # 请求后步骤  # self.checks = None  # 断言  # self.extract = None  # 提取语句

        # 其他
        self.watches = None  # 关注人

        self.steps = []



class Step(Base):
    """步骤"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 属性 ----------------

        self.pre_checks = None  # 步骤前检查
        self.post_checks = None  # 步骤后检查
        self.post_extract = None  # 提取语句

        # 其他

        self.func = None  # 目标方法

        def run(self, *args, **kwargs):
            pass



class Request(Step):
    """请求步骤"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def run(self):
        pass


if __name__ == '__main__':
    request = dict(name='test')
