import json
from config import config
import utils

from task import SpiderTask
task = SpiderTask()

# List of task that has been crawled
taskList = task.getFinishTask()
print(json.dumps(taskList, indent=4))

# get inner link list
key = config['redis_urls_result_queue_prefix_key']
taskID = "20230422114925_Tfvr"
innerList = task.getInnerList(taskID)
print(json.dumps(innerList, indent=4))

urlList = []
for url in innerList:
    urlList.append(url['standard_url'])
# export sitemap.xml
utils.saveSitemap(urlList, taskID)

# export csv file
headers = innerList[0].keys()
utils.saveCsv(headers, innerList, taskID)