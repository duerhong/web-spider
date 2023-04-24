# Python Web Spider
## 申明
代码、教程仅限于学习交流，请勿用于任何商业用途！
## 简介
Python Web Spider 专门用于爬取网站内链，可以导出成csv,json,xml等文件。可以用于给网站生成专用的sitemap。

## 官网
https://web-tools.cn/web-spider

## 文件结构
config.py                   配置文件，可配置redis，日志，导出数据文件路径
utils.py                    核心函数库
worker.py                   爬取主程序
task.py                     任务相关
demo_create_task.py         创建任务demo
demo_export.py              导出数据demo
env-example                 env配置文件demo，请复制一份名称env的文件
requirements.txt            依赖安装
data/csv                    当执行了导出csv文件后创建
data/sitemap                当执行了导出sitemap文件后创建
## 环境
python3.8 +
redis

## 安装
pip install -r requirements.txt
如果以上安装未能安装所有依赖程序，请手动安装依赖程序。

## 运行
### env文件配置
将当前env-example复制一份，新文件名称为env文件，并且做好以下配置
```
ROOT_PATH：./               当前项目根路径
REDIS_HOST=127.0.0.1        redis host
REDIS_PORT=6379             redis prot
REDIS_PASSWORD=             redis password
REDIS_DB=0                  redis db
```
### config.py 配置文件
如果想改动默认配置，请修改相关配置项

### 运行worker.py
worker.py 为多线程 + 轮询监听运行，可以通过config.py 文件下配置spider_thread_list来调整线程数量
运行：
```
python worker.py
```
## 创建任务
可参考 demo_create_task.py 来创建一个爬取任务，主要代码
```python
from task import SpiderTask
task = SpiderTask()
ret = task.createTask(
    # 着陆页
    landing_page="https://www.test.com",
    # 域名，多个域名可以用逗号隔开。当爬取链接的域名配置这个域名的时候，被认为是内链。
    # 该方案解决部分内链写的是不规范的绝对链接。
    domain="www.test.com",
    # 基础链接，用于生成最终爬取链接，比如当爬取的内链为 /test/1 那么最终链接为 https://www.web-tools.cn/test/1
    basic_page="https://www.test.com/"
)
```


## 导出为csv文件
请参考demo_export.py

## 导出为sitemap文件
请参考demo_export.py

## 其他
QQ： 1796958708，有问题随时联系
