# 通用 -------------------------------
NAME = 'name'  # 名称
DESCRIPTION = 'description'
TAGS = 'tags'
LEVEL = 'level'

VAIABLES = 'variables'  # 用户自定义变量关键字
CONFIG = 'config'  # 配置关键字  settings

SKIP = 'skip'  # 跳过步骤关键字
TIMES = 'times'  # 循环步骤关键字  circle
CONCURRENCY = 'concurrency'
TIMEOUT = 'timeout'

SETUP_HOOKS = 'setup_hooks'
TEARDOWN_HOOKS = 'teardown_hooks'


# 步骤组 -------------------------------
RUN_MODE = 'run_type'  # stage中steps运行方式
SUB_STEPS = ['stages', 'steps', 'testcases', 'tests', 'teststeps']

BASEURL = 'baseurl'
REQUEST = 'request'  # 请求配置,请求数据关键字
CHECK = 'check'  # 验证关键字  check/validate/assert
EXTRACT = 'extract'   # 提取关键字 output/register
ACTION = 'action'  # 步骤类型 operation/keywords/function/target

DATA = 'tests'
CONTEXT = 'context'

# 上下文变量
POLL = 'poll'  # 线程池  废弃
REQUEST_SESSION = 'request_session'  # 请求会话
# CONFIG = '_config'  # 配置
FUNCTIONS = 'functions'
FIXTURES = 'fixtures'
