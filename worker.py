# coding=utf-8
"""
爬取说明：
该爬虫只负责爬取内链，不爬取外链。外链逻辑可以在适当位置自定义爬取
"""
import json
import time
import redis
import utils
import requests
from config import config
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import traceback
import threading
from urllib import parse
# from Model import SpiderProcess
from task import SpiderTask

threadLock = threading.Lock()
taskObj = None


class Spider:
    def __init__(self, taskQueueHash, threadID, basicUrl, taskData, keepParameter=False, keepPageParameter=True,
                 domains=None, allowKeyword=None, allowRule=None, disKeyword=None, disRule=None):
        """
        :param domains: The domain name of the inner chain.The 0th is considered to be the main domain name,
        and the others are auxiliary domain names, but they all refer to unified site resources.for example [
        'www.web-tools.cn', 'web-tools.cn']
        :param disRule: Rules: rules for prohibiting the occurrence of URL
        :param disKeyword: Keywords prohibited in the URL
        :param allowRule: Allow in URL Rules
        :param allowKeyword: Keywords allowed in the URL
        :return:
        """
        # task info
        self.taskData = taskData
        # thread ID
        self.threadID = threadID
        # log file
        self.logFile = "process_for_%s.log" % self.threadID
        # init redis
        self.redisConn = redis.Redis(host=config['redis']['host'],
                                     port=config['redis']['port'],
                                     db=config['redis']['db'],
                                     password=config['redis']['password'],
                                     socket_keepalive=True
                                     )
        # task hash
        self.taskQueueHash = taskQueueHash
        """
        爬取队列url是否保留参数, 该参数不影响分页参数：isCrawKeepPage的保留
        """
        self.isKeepUrlParameterForQueue = keepParameter
        # 爬取的时候，是否保留分页，如果不保留，则对分页不进行爬取
        self.isCrawlKeepPage = keepPageParameter
        # 分页参数设置
        self.crawlPageParameter = "page"
        # 爬取结果中是否保留参数，如果选择了False，所有的参数都将去掉，包括分页参数。暂不支持该参数
        self.isKeepUrlParameterForResult = False

        self.allowKeyword = allowKeyword
        self.allowRule = allowRule
        self.disKeyword = disKeyword
        self.disRule = disRule

        # 爬取的域名列表，当url域名在该域名列表中，则认为是内链
        self.domains = domains
        self.basicUrl = basicUrl

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/86.0.4240.111 Safari/537.36"}

    @staticmethod
    def stripAnchor(url):
        """
        将url锚点抛出
        :param url:
        :return:
        """
        if not url:
            return url
        return str(re.sub(r'\#.*', "", str(url)))

    @staticmethod
    def stripAllParameter(url):
        """
        移除所有参数
        :param url:
        :return:
        """
        if not url:
            return url
        return str(re.sub(r'\?.*', "", str(url)))

    @staticmethod
    def stripLine(url):
        """
        移除换行
        :param url:
        :return:
        """
        url = str(url)
        if not url:
            return url
        url = str(re.sub(r'/r/n', "", url))
        url = str(re.sub(r'/n', "", url))
        url = str(re.sub(r'/t', "", url))
        return url

    @staticmethod
    def byUrlGetDomain(url):
        return urlparse(url).netloc.lower()

    def isIncludePageParameter(self, url):
        params = parse.parse_qs(parse.urlparse(url).query)
        if self.crawlPageParameter in params:
            return True
        return False

    def getKeepPageUrl(self, url):
        """
        获取保留了分页，但是不保留其他参数的url
        :return:
        """
        params = parse.parse_qs(parse.urlparse(url).query)
        if self.crawlPageParameter in params:
            page = params[self.crawlPageParameter][0]
            return "%s?%s=%s" % (self.stripAllParameter(url), self.crawlPageParameter, page)
        return self.stripAllParameter(url)

    def toStandardUrl(self, url):
        """
        转化为标准url
        根据规则来过滤不需要爬取的url，支持正则和字符串过滤
        过滤javascript伪协议，比如javascript:; mail: tel: file: #
        过滤包含空链接
        :param url:
        :return: string|None
        """
        # url 规范化
        url = url.lower()
        # 移除锚点
        url = self.stripAnchor(url)
        # 移除换行
        url = self.stripLine(url)
        # 如果url中存在换行，则将换行替换为空
        url = url.replace("\n", "")
        if not url:
            return None

        # 过滤伪协议
        if url.startswith("javascript:"):
            return None
        if url.startswith("mail:"):
            return None
        if url.startswith("tel:"):
            return None
        if url.startswith("file:"):
            return None
        if url.startswith("mailto:"):
            return None

        """
        如果不保留参数 + 不保留分页:直接将 url中问号后面的全面移除
        """
        if self.isCrawlKeepPage is False and self.isKeepUrlParameterForQueue is False:
            url = self.stripAllParameter(url)

        """
        如果不保留参数 + 保留分页:获取page，将page参数附加到去除了所有参数的链接后面
        """
        if self.isCrawlKeepPage is True and self.isKeepUrlParameterForQueue is False:
            url = self.getKeepPageUrl(url)

        """
        其他情况：
        保留参数 + 不保留分页： 保留所有参数，不过滤
        pass
        保留参数 + 保留分页： 保留所有参数，不过滤
        pass
        """

        """
        保留匹配关键字，直接返回
        """
        if self.allowKeyword and self.allowKeyword in url:
            return url

        """
        保留符合正则的url，直接返回
        """
        if re.search(r"%s" % self.allowRule, url, re.M):
            return url

        """
        过滤符合匹配关键字的url，直接返回
        """
        if self.disKeyword and self.disKeyword in url:
            return None

        """
        过滤符合正则的url，直接返回
        """
        if re.search(r"%s" % self.disRule, url, re.M):
            return None

        return url

    def isInnerUrl(self, url):
        """
        url是否为内链
        :param url:
        :return:
        """
        # 非http链接开头的，认为是内链
        if not url.startswith("https://") and not url.startswith("http://"):
            return True
        # 在域名范围内，认为是内链。
        if self.byUrlGetDomain(url) in self.domains:
            return True
        return False

    def getPageInnerUrls(self, content):
        """
        获取网页内容下所有超链接
        :param content:
        :return:
        """
        result = []
        html = BeautifulSoup(content, "html.parser")
        all_a = html.select("a[href]")
        for item in all_a:
            url = str(item['href'])
            if not url:
                continue
            if not self.isInnerUrl(url):
                continue
            url = self.toStandardUrl(item['href'])
            if not url:
                continue
            result.append(url)
        return result

    def pushUrlToWaitQueue(self, urls):
        """
        将url推送到待爬取队列
        :param urls:
        :return:
        """
        res = []
        for url in urls:
            if not url:
                continue
            # url唯一队列
            if self.redisConn.sadd('%s%s' % (config['redis_urls_fingerprint_prefix_key'], self.taskQueueHash),
                                   utils.md5(url)) > 0:
                res.append(url)
                # 待爬取的url队列
                self.redisConn.rpush('%s%s' % (config['redis_urls_waite_queue_prefix_key'], self.taskQueueHash), url)
        return res

    def getWaitUrls(self, count=10):
        rKey = '%s%s' % (config['redis_urls_waite_queue_prefix_key'], self.taskQueueHash)
        urls = self.redisConn.lrange(rKey, 0, count)
        if len(urls) > 0:
            self.redisConn.ltrim(rKey, len(urls), -1)
        return urls

    def finishTask(self):
        """
        完成爬取任务，设置数据库进程状态为完成，清除相关redis
        :return:
        """
        taskObj.setFinish(self.taskQueueHash)
        self.redisConn.delete('%s%s' % (config['redis_urls_fingerprint_prefix_key'], self.taskQueueHash))

    def pushUrlToResultQueue(self, urlData=None):
        """
        将url推送到结果队列
        :param urlData:
        :return:
        """
        if not self.isIncludePageParameter(urlData['origin_url']):
            self.redisConn.rpush('%s%s' % (config['redis_urls_result_queue_prefix_key'],
                                           self.taskQueueHash), json.dumps(urlData))
        return True

    def getFullUrl(self, url):
        if "https://" not in url and "http://" not in url:
            return self.basicUrl.strip("/") + "/" + str(url).strip("/")
        return url

    def crawl(self, url, logTab=0):
        """
        根据url爬取
        :param logTab:
        :param url:
        :return:
        """
        logTab = logTab + 1
        url = self.getFullUrl(url)
        utils.log('crawl %s' % url, self.logFile, logTab=logTab)
        rTimes = 3
        rIndex = 0
        resp = None
        for retryTimes in range(0, rTimes):
            rIndex = rIndex + 1
            if rIndex >= rTimes - 1:
                utils.log("requests url %s failed!" % url, "error.log")
                return True
            try:
                resp = requests.get(url, headers=self.headers)
                break
            except:
                utils.log(traceback.format_exc(), "error.log")
                continue

        # 请求失败
        if not resp:
            return False

        # 请求返回 http 状态码非200
        if resp and int(resp.status_code) != 200:
            utils.log('crawl failed, status: %s' % resp.status_code, self.logFile, logTab=logTab)
            self.pushUrlToResultQueue({
                "origin_url": url,
                "http_code": resp.status_code,
                "standard_url": url
            })
            return False

        html = resp.content.decode('utf-8')
        innerUrls = self.getPageInnerUrls(html)
        newInnerUrls = self.pushUrlToWaitQueue(innerUrls)

        if len(newInnerUrls) > 0:
            utils.log(f'discovered urls:', self.logFile, logTab=logTab)
            for discovered_url in newInnerUrls:
                utils.log('\t%s' % discovered_url, self.logFile, logTab=logTab)

        """
        外链爬取，不支持
        pass
        """

        """
        将当前页面加入到结果队列
        """
        self.pushUrlToResultQueue({
            "origin_url": url,
            "http_code": 200,
            "standard_url": url
        })
        return True

    def start(self, logTab=0):
        logTab = logTab + 1
        empty_times = 0
        while True:
            threadLock.acquire()
            urls = self.getWaitUrls()
            threadLock.release()
            if len(urls) == 0:
                empty_times += 1
                # 设定时间范围内，没有任何新的爬取链接，则认为爬取结束。同时结束线程
                if empty_times > config['spider_wait_times']:
                    utils.log(f'thread: {self.threadID}, task: {self.taskData["task_id"]}, queue empty_times > {config["spider_wait_times"]}, finished', self.logFile,
                              logTab=logTab)
                    threadLock.acquire()
                    self.finishTask()
                    threadLock.release()
                    break
                else:
                    utils.log(f'thread: {self.threadID}, queue empty ({empty_times}), sleep 1s to wait for uncarwl url', self.logFile,
                              logTab=logTab)
                    time.sleep(1)
                    continue
            else:
                empty_times = 0
                utils.log(f'thread: {self.threadID}, queue uncrawl urls: ', self.logFile, logTab=logTab)

            for url in urls:
                url = url.decode("utf-8", "ignore")
                utils.log(f'\tthread: {self.threadID}, {url}', self.logFile, logTab=logTab)

            for url in urls:
                url = url.decode("utf-8", "ignore")
                try:
                    self.crawl(url, logTab)
                except:
                    utils.log(f'exception happened, crawl next url, exception: {traceback.format_exc()}', "error.log")


class SpiderThread(threading.Thread):
    def __init__(self, tid, spider):
        threading.Thread.__init__(self)
        self.threadID = tid
        self.spider = spider

    def run(self):
        self.spider.start()


if __name__ == '__main__':
    """
    线程启动
    """
    idx = 0
    while True:

        try:
            if not taskObj:
                taskObj = SpiderTask()
            process = taskObj.getFirstWaitTask()
            time.sleep(5)
            if process:
                domains = process['domain'].split(",")
                # 初始化
                threads = []
                spiderList = []
                for threadID in config['spider_thread_list']:
                    spider = Spider(
                        domains=domains,
                        taskQueueHash=process['task_id'],
                        threadID=threadID,
                        basicUrl=process['basic_page'],
                        taskData = process
                    )
                    spiderList.append(spider)
                    if threadID == "main":
                        # 将第一个url加入
                        spider.pushUrlToWaitQueue([process['landing_page']])

                    thread = SpiderThread(threadID, spider)
                    thread.start()
                    threads.append(thread)

                for t in threads:
                    t.join()

                # 创建多个线程爬取
        except Exception as e:
            time.sleep(10)
            error = traceback.format_exc()
            utils.log(error, "error.log")
