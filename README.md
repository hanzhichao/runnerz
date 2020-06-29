# Runnerz

simple runner like httprunner

## 相比于httprunner

- 支持多种步骤,及自定义步骤
- 支持dubbo接口
- 用例支持多种步骤
- 支持多种样式的报告,及自定义报告模板 reportz
- 支持用例并发
- 支持异步请求 aiohttp
- 用例支持tag, level
- 支持xpath
- 支持trigger及设置定时任务 pytest-crontab
- 支持更相信的请求连接信息 requestz
- 支持json_schema断言
- 支持直接使用python/js脚本
- 支持参数化运行 cli / html
- 支持自定义keywords


## 特性
- [ ] HTTP默认配置
- [ ] 用户自定义变量
- [ ] 环境变量
- [ ] .env支持
- [ ] 并发及多轮
- [ ] 重跑
- [ ] 步骤组并行运行
- [ ] setup_hook/teardown_hook
- [x] eq断言
- [ ] schema断言
- [ ] xpath/jsonpath/re提取
- [ ] css selector提取
- [ ] 根据条件跳过用例
- [ ] 测试报告
- [ ] merge config
- [x] 多级steps
- [ ] 支持ddt
- [ ] 支持if/else/switch/while
- [ ] args
- [ ] options
- [ ] add options ini
- [ ] trigger
- [x] unittest用例
- [ ] har
- [ ] 运行postman
- [ ] 运行jmeter
- [ ] 运行robot
- [ ] timeout限制
- [ ] dubbo支持


Base基类负责
* 处理skip
* times
* concurrency



TestCase类负责
* 变量解析替换,
* merge config
* merge variables
* setup/teardown执行
* check/extra执行



Request具体步骤负责
* 根据config设置session默认值
* 注册session变量
* 组装url
* 设置默认method


字段支持 字符串 简写 和 字典格式

## Todo
* 尝试使用模板组装形式
* config中setup teardown variables不支持$变量


为每个关键字处理写个方法


* 步骤的call 和 run 混乱
* 步骤注册和自动发现

