# coding=utf-8


def env(key, default=None):
    path = "env"
    with open(path) as file_obj:
        for line in file_obj:
            lineStr = str(line)
            if "=" in str(lineStr):
                lineArr = lineStr.split('=')
                filed = lineArr[0].strip()
                value = lineArr[1].strip()
                value = value.strip('"')
                if key == filed:
                    return value
    return default


def get_path(path):
    root = env("ROOT_PATH", "/var/www/spider_server/")
    return "%s/%s" % (root.strip("/"), path.strip(("/")))


config = {
    "debug": True,
    "redis": {
        'host': env("REDIS_HOST"),
        'port': int(env("REDIS_PORT")),
        'db': env("REDIS_DB", 6),
        'password': env("REDIS_PASSWORD"),
    },
    "log_path": env("LOG_PATH", get_path("log/")),
    "log_max_num": env("LOG_MAX_NUM", 30),
    "root_path": env("ROOT_PATH", "/var/www/spider_server"),
    # Waiting for crawling queue
    "redis_urls_waite_queue_prefix_key": "spider_wait_queue_",
    # Crazy the only collection of URL
    "redis_urls_fingerprint_prefix_key": "spider_fingerprint_",
    # Crazy result collection
    "redis_urls_result_queue_prefix_key": "spider_result_queue_",
    # Task list key
    "redis_task_list_key": "spider_task_list",
    # The thread queue, the first thread must be main, to distinguish whether it is the first queue
    "spider_thread_list": ["main", "thread1", "thread2"],
    # The maximum waiting time of crawlers, when the limited time exceeds the limited time,
    # it is considered to be crawling.
    "spider_wait_times": 10
}
