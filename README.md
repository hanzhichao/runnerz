# Runnerz

simple runner like httprunner


## 目标
- 支持多步骤
- 支持dubbo
- 兼容httprunner










## 特性
- [x] HTTP默认配置
- [x] 用户自定义变量
- [x] 环境变量
- [ ] .env支持
- [x] 并发及多轮
- [ ] 重跑
- [ ] 步骤组并行运行
- [x] setup_hook/teardown_hook
- [x] eq断言
- [ ] schema断言
- [x] xpath/jsonpath/re提取
- [ ] css selector提取
- [ ] 根据条件跳过用例
- [ ] 测试报告
- [x] merge config
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