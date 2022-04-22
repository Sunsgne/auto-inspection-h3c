#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-
import logging

import requests
import re

import time
import os
import sys
from dzkfcollector.settings import SERVICE_MAP_FILE_PATH
from web.models import Jobs, Settings
from web.utils.constant import SERVER_RUN
from web.views.job_view import JobViewSet

logger = logging.getLogger('linux_collector')
head_path = SERVICE_MAP_FILE_PATH


def get_info(info_rows, job_id):
    file_path = []
    for info_row in info_rows:
        dev_ip = info_row['device_ip']
        username = info_row['user_name']
        password = info_row['user_psw']
        settings = Settings.objects.get(id=2)
        error_path = settings.setting_val+dev_ip
        settings = Settings.objects.get(id=1)
        pass_path = head_path+settings.setting_val+"/"
        starttime = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        start_time = time.strftime('%Y%m%d', time.localtime(time.time()))  # 文件夹
        path_file = head_path+error_path+r'/error_green_download%s' % start_time+"/"
        try:
            jobstu = Jobs.objects.get(id=job_id)
            jobstu.status = SERVER_RUN
            jobstu.save()
            url = 'https://%s/redfish/v1/managers/1/activehealthsystem' % dev_ip
            headers = {'Content-Type': 'application/json', 'X-Api-Version': '4',
                       'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'}
            req = requests.session()
            # 禁用代理
            req.trust_env = False
            logger.info('url is : %s' % url)
            response = req.get(url=url, auth=(username, password), headers=headers, stream=True, verify=False)
            rep = response.text.replace(',', '\n')
            logger.info('response is : %s' % rep)
            for line in rep.split('\n'):
                if re.findall('RecentWeek', line, re.IGNORECASE):
                    lines = line.split(':')
                    lineurl = lines[2].split('"')
                    urls = 'https://%s' % dev_ip + lineurl[1]
                    start = time.time()
                    status = JobViewSet.dev_job(job_id, 10)
                    if not status:
                        return file_path
                    r = req.get(urls, stream=True, auth=(username, password), headers=headers, verify=False)
                    if r.text == 'bb_dl_disabled':
                        if not os.path.exists(path_file):
                            os.makedirs(path_file)
                        with open(path_file + '/%s_%s_error.log' % (starttime, dev_ip), 'a') as f:
                            f.write(r.text + '  ' + 'Please try again later')
                        JobViewSet.job_fail(job_id)
                    else:
                        path = pass_path
                        if not os.path.exists(path):
                            os.makedirs(path)
                        size = 0
                        file_name = '%s_%s.%s' % (dev_ip, starttime, "ahs")
                        with open(path + file_name, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=1024):
                                if chunk:
                                    f.write(chunk)
                                    f.flush()
                                    size += len(chunk)
                            if int(size/1024/1024) == 0:
                                if not os.path.exists(path_file):
                                    os.makedirs(path_file)
                                JobViewSet.job_fail(job_id)
                                with open(path_file + '/%s_%s_error.log' % (starttime, dev_ip), 'a') as f:
                                    f.write(str('post sds log is 0MB!'))
                            else:
                                status = JobViewSet.dev_job(job_id, 60)
                                if not status:
                                    return file_path
                                end = time.time()
                                fr = '\r' + '[{0} progress downloading]:{1}{2}MB,times:{3}秒'.format((dev_ip),'█'*(int(size/1024/1024)),float(size/1024/1024),round((end-start),2))

                                sys.stdout.write(fr)
                                sys.stdout.flush()
                                status = JobViewSet.dev_job(job_id, 100)
                                if not status:
                                    return file_path
                                file_path.append(path+file_name)
                                logger.info('device[%s] collect success %s' % (dev_ip, path+file_name))
                                JobViewSet.job_success(job_id)
                                return file_path
            JobViewSet.job_fail(job_id)
        except Exception as e:
            if not os.path.exists(path_file):
                os.makedirs(path_file)
            JobViewSet.job_fail(job_id)
            with open(path_file + '/%s_%s_error.log' % (starttime, dev_ip), 'a') as f:
                f.write(str(e))
            return file_path
