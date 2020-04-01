

SUB_STEPS = ['stages', 'steps', 'testcases', 'tests', 'teststeps']

def get_section(data, keyword_list):
    for keyword in keyword_list:
        section = data.get(keyword)
        if section is not None:
            return section



class Step(object):
    """步骤Stage/TestCase/Steps"""
    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        self.description = kwargs.get('description')
        self.tags = kwargs.get('tags')
        self.level = kwargs.get('level')
        self.status = None
        self.result = None

        # 过程性数据
        self.config = kwargs.get('config')
        self.sub_steps = get_section(kwargs, SUB_STEPS)

        # 仅最末端的步骤
        action = kwargs.get('action')
        request = kwargs.get('request')
        check = kwargs.get('check')
        extract = kwargs.get('extract')

        # 运行前
        # self.args = None
        # self.options = None
        # self.agent = None
        # self.trigger = None  # 仅最外层支持
        # self.watches = None  # 观察者

        # 运行控制
        self.skip = kwargs.get('skip')   # True or True if $a > 0
        self.timeout = kwargs.get('timeout')
        self.times = kwargs.get('times')  # 3 or rerun  (3, 1, 'on_fail/on_error/always')
        self.concurrency = kwargs.get('concurrency')


        # STEP GROUP
        self.run_mode = kwargs.get('run_mode')  # 顺序,并行,打乱,test

        # 前后步骤
        self.pre_steps = []
        self.sub_steps = None
        self.post_steps = None  # post_check, post_extract

        self.hooks = None  # 捎带步骤 setup_hooks, teardown_hooks

        # 运行时
        self.context = None  # variables, config, session, functions 参考pytest request
        self.raw = kwargs  # 元素数据

    def parse(self, data):
        """解析$变量"""
        pass

    def run(self):
        """运行步骤"""



if __name__ == '__main__':
    import yaml
    with open('/Users/apple/Documents/Projects/Self/PyPi/runnerz/data.yml', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    print(data)