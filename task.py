# coding=utf-8
import utils
import json
import redis
from config import config


class SpiderTask:
    def __init__(self):
        self.redisConn = redis.Redis(host=config['redis']['host'],
                                     port=config['redis']['port'],
                                     db=config['redis']['db'],
                                     password=config['redis']['password']
                                     )

    def getAllTask(self):
        result = []
        taskList = self.redisConn.hvals(config['redis_task_list_key'])
        for item in taskList:
            itemObj = json.loads(item)
            result.append(itemObj)
        return result

    def getAllWaitTask(self):
        result = []
        taskList = self.redisConn.hvals(config['redis_task_list_key'])
        for item in taskList:
            itemObj = json.loads(item)
            if itemObj['status'] == "wait":
                result.append(itemObj)
        return result

    def getFirstWaitTask(self):
        taskList = self.redisConn.hvals(config['redis_task_list_key'])
        for item in taskList:
            itemObj = json.loads(item)
            if itemObj['status'] == "wait":
                self.setOngoing(itemObj['task_id'])
                return itemObj
        return None

    def setFinish(self, taskID):
        data = self.redisConn.hget(config['redis_task_list_key'], taskID)
        if data:
            data = json.loads(data)
            if data['status'] != "finish":
                data['status'] = "finish"
                data["updated_at"] = utils.getNowStrTime()
                data["end_time"] = utils.getNowStrTime()
                self.redisConn.hset(config['redis_task_list_key'], taskID, json.dumps(data))
        return True

    def setOngoing(self, taskID):
        data = self.redisConn.hget(config['redis_task_list_key'], taskID)
        if data:
            data = json.loads(data)
            if data['status'] == "wait":
                data['status'] = "ongoing"
                data["updated_at"] = utils.getNowStrTime()
                data["start_time"] = utils.getNowStrTime()
                self.redisConn.hset(config['redis_task_list_key'], taskID, json.dumps(data))
        return True

    def createTask(self, landing_page, domain, basic_page, landing_type="page", info=""):
        taskID = "%s_%s" % (utils.getNowStrTime(f='%Y%m%d%H%M%S'), utils.getRandStr(4))
        data = {
            "created_at": utils.getNowStrTime(),
            "updated_at": utils.getNowStrTime(),
            "start_time": "",
            "end_time": "",
            "task_id": taskID,
            "landing_page": landing_page,
            "landing_type": landing_type,
            "status": "wait",
            "domain": domain,
            "info": info,
            "basic_page": basic_page,
        }
        return self.redisConn.hset(config['redis_task_list_key'], taskID, json.dumps(data))

    def getFinishTask(self):
        result = []
        taskList = self.redisConn.hvals(config['redis_task_list_key'])
        for item in taskList:
            itemObj = json.loads(item)
            if itemObj['status'] == "finish":
                result.append(itemObj)
        return result

    def getInnerList(self, taskID):
        key = '%s%s' % (config['redis_urls_result_queue_prefix_key'], taskID)
        listLen = self.redisConn.llen(key)
        result = []
        urlList = self.redisConn.lrange(key, 0, listLen)
        for item in urlList:
            itemObj = json.loads(item)
            if itemObj['http_code'] == 200:
                result.append(itemObj)
        return result
