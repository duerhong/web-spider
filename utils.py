# coding=utf-8
import datetime
import hashlib
import os
import shutil
from urllib.parse import urlparse
import pytz
from config import config


def logRollback(path, limit=12, mode=1):
    try:
        fileList = []
        if os.path.isdir(path):
            list = os.listdir(path)
            for item in list:
                dirs = "%s/%s" % (path, item)
                if mode == 1 and os.path.isdir(dirs):
                    fileList.append(item)
                elif mode == 2 and os.path.isfile(dirs):
                    fileList.append(item)
        fileList = sorted(fileList, reverse=True)
        idx = 0
        for path_name in fileList:
            idx = idx + 1
            filepath = "%s/%s" % (path, path_name)
            if idx > limit:
                if mode == 1:
                    if os.path.isdir(filepath):
                        shutil.rmtree(filepath, True)
                elif mode == 2:
                    if os.path.isfile(filepath):
                        os.remove(filepath)
    except Exception as e:
        return None


def log(info, logFile="error.log", logTab=0):
    preFix = logTab * "\t"
    tz = pytz.timezone('Asia/Shanghai')
    if config['debug']:
        print(info)
    logFile = '%s/%s/%s' % (config['log_path'], str(datetime.datetime.now(tz).strftime('%Y-%m-%d')), logFile)
    if not os.path.exists(logFile):
        for i in range(3):
            try:
                os.makedirs(os.path.dirname(logFile))
            except Exception as e:
                pass
    with open(logFile, 'a+', encoding="utf-8") as f:
        now = datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
        f.writelines("【%s】 - %s%s\n" % (now, preFix, info))
    logRollback(config['log_path'], config['log_max_num'], 1)


def byUrlGetDomain(url):
    return urlparse(url).netloc


def md5(text):
    m = hashlib.md5()
    m.update(text.encode('utf-8'))
    return m.hexdigest()


def getNowStrTime(f='%Y-%m-%d %H:%M:%S', zone="Asia/Shanghai"):
    tz = pytz.timezone(zone)
    return str(datetime.datetime.now(tz).strftime(f))


def getRandStr(strLen=6):
    import random
    import string
    """
    Get a random string with a specified length
    :param strLen:
    :return:
    """
    return ''.join(random.sample(string.digits + string.ascii_letters, strLen))


def saveSitemap(urls, task):
    import time
    path = "data/sitemap"
    if not os.path.exists(path):
        os.makedirs(path)
    fullPath = "%s/%s.xml" % (path, task)

    fw = open(fullPath, 'w', encoding="utf-8")
    fw.write('<?xml version="1.0" encoding="UTF-8"?>')
    fw.write('\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
             'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
             'xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9 '
             'http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">')
    for url in urls:
        fw.write('\n\t<url>')
        fw.write("\n\t\t<loc>%s</loc>" % url)
        fw.write("\n\t\t<lastmod>" + time.strftime('%Y-%m-%d', time.localtime(time.time())) + "</lastmod>")
        fw.write("\n\t\t<changefreq>daily</changefreq>")
        fw.write("\n\t\t<priority>1.00</priority>")
        fw.write('\n\t</url>')
    fw.write('\n</urlset>')
    return True


def saveCsv(header, data, task):
    import csv
    path = "data/csv"
    if not os.path.exists(path):
        os.makedirs(path)
    fullPath = "%s/%s.csv" % (path, task)
    f = open(fullPath, mode='w', encoding='utf-8', newline='')
    csv_writer = csv.DictWriter(f, fieldnames=header)
    csv_writer.writeheader()

    for item in data:
        csv_writer.writerow(item)
    return True
