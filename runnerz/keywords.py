

# 步骤定义
CONFIG = 'config'  # 配置关键字  settings
STAGES = 'stages'
STEPS = 'steps'  # 步骤关键字  steps/teststeps/testcases

NAME = 'name'  # 名称
VAIABLES = 'variables'  # 用户自定义变量关键字
RUN_TYPE = 'run_type'  # stage中steps运行方式
BASEURL = 'baseurl'
REQUEST = 'request'  # 请求配置,请求数据关键字
CHECK = 'check'  # 验证关键字  check/validate/assert
EXTRACT = 'extract'   # 提取关键字 output/register
SKIP = 'skip'  # 跳过步骤关键字
TIMES = 'times'  # 循环步骤关键字  circle
ACTION = 'action'  # 步骤类型 operation/keywords/function/target

CONCURRENCY = 'concurrency'

# 上下文变量
POLL = '_poll'  # 线程池  废弃
SESSION = '_session'  # 请求会话
CONFIG = '_config'  # 配置