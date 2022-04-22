#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-
import logging

import requests
import json
import time
import os
import sys

from dzkfcollector.settings import SERVICE_MAP_FILE_PATH

from web.models import Jobs, Settings
from web.utils.constant import SERVER_RUN
from web.views.job_view import JobViewSet

head_path = SERVICE_MAP_FILE_PATH

requests.packages.urllib3.disable_warnings()

logger = logging.getLogger('linux_collector')


# info_rows:用户名和密码，collect_policy:当前设备使用的策略id
def get_info(info_rows, job_id):
    file_path = []
    for info_row in info_rows:
        dev_ip = info_row['device_ip']
        username = info_row['user_name']
        password = info_row['user_psw']
        settings = Settings.objects.get(id=2)
        error_path =head_path+settings.setting_val+"/"
        settings = Settings.objects.get(id=1)
        pass_path = head_path+settings.setting_val+"/"
        starttime = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        start_time = time.strftime('%Y%m%d', time.localtime(time.time()))  # 文件夹
        try:
            status = JobViewSet.dev_job(job_id, 0)
            if not status:
                break
            jobstu = Jobs.objects.get(id=job_id)
            jobstu.status = SERVER_RUN
            jobstu.save()
            url_api = 'https://%s/api/session?username=%s&password=%s' % (dev_ip, username, password)
            url_log = 'https://%s/api/health/sds/log' % dev_ip
            url_status = 'https://%s/api/health/sds/status' % dev_ip
            reqs = requests.session()
            reqs.trust_env = False
            logger.info('url is : %s' % url_api)
            response = reqs.post(url_api, verify=False)
            # 获取session页面的response和cookie
            token_api = json.loads(response.text)
            cookies_dict = requests.utils.dict_from_cookiejar(response.cookies)
            cookie_api = "; ".join([str(x) + "=" + str(y) for x, y in cookies_dict.items()])
            if response.status_code == 200:
                if 'cc' in list(token_api):
                    headers = {
                        'X-CSRFTOKEN': str(token_api['CSRFToken']),
                        'Cookie': cookie_api,
                        'Content-Type': 'application/json',
                    }
                    body = {
                        "start_date": "0",
                        "end_date": "0",
                        "ContactName": "",
                        "PhoneNumber": "",
                        "EmailNumber": "",
                    }
                    # 获取log页面的response
                    result = reqs.post(url=url_log, data=json.dumps(body), headers=headers, verify=False)
                    i = 0
                    while i != 100:
                        # 这个循环里面需要接口
                        response_status = reqs.get(url=url_status, headers=headers, verify=False)
                        token_status = json.loads(response_status.text)
                        i = token_status['sds_status']
                        # 获取当前的百分比,还有当前任务的id,传入新的接口中
                        # 返回一个Ture或者False来判断是否要继续执行
                        if i <= 80:
                            status = JobViewSet.dev_job(job_id, i)
                            if status:
                                time.sleep(10)
                            else:
                                break
                        else:
                            status = JobViewSet.dev_job(job_id, 80)
                            if status:
                                print('%s Compress  %s%%' % (dev_ip, i))
                            else:
                                break
                    token_log = json.loads(result.text)
                    if token_log['cc'] == 0:
                        if 'filename' not in list(token_log.keys()):
                            JobViewSet.job_fail(job_id)
                            path_file = error_path+r'error_red_download%s' % start_time
                            if not os.path.exists(path_file):
                                os.makedirs(path_file)
                            with open(path_file + '/%s_%s_error.log' % (starttime, dev_ip), 'a') as f:
                                f.write(str('post sds log failed!\n'))
                            return file_path
                        else:
                            status =JobViewSet.dev_job(job_id, i)
                            if not status:
                                continue
                            else:
                                JobViewSet.dev_job(job_id, 80)
                                filenameurl = str(token_log['filename'])
                                url_loginfo = 'http://%s/sds/%s' % (dev_ip, filenameurl)
                                start = time.time()
                                req = reqs.get(url=url_loginfo, headers=headers, timeout=10, stream=True)
                                size = 0
                                chunk_size = 1024
                                content_size = int(req.headers.get('Content-Length', -1))
                                path = pass_path
                                if not os.path.exists(path):
                                    # 这个地方创建文件夹
                                    os.makedirs(path)
                                file_name ='%s_%s.%s' % (dev_ip, starttime, "sds")
                                with open(path + file_name, 'wb') as f:
                                    for chunk in req.iter_content(chunk_size=1024):
                                        if chunk:  # filter out keep-alive new chunks
                                            f.write(chunk)
                                            f.flush()
                                            size += len(chunk)
                                            end = time.time()
                                        fr = '\r' + '[{0} progress downloading]:{1}{2}%,times: {3}秒'.format((dev_ip),'█'*(int(size * 50/content_size)), float(size* 100/content_size),round((end - start),2))
                                        sys.stdout.write(fr)
                                        sys.stdout.flush()
                                file_path.append(path + file_name)
                                JobViewSet.dev_job(job_id, '100')
                                logger.info('device[%s] collect success %s' % (dev_ip, path+file_name))
                                JobViewSet.job_success(job_id)
                                return file_path
                    else:
                        JobViewSet.job_fail(job_id)
                        path_file = error_path+r'error_red_download%s' % start_time
                        if not os.path.exists(path_file):
                            os.makedirs(path_file)
                        with open(path_file + '/%s_%s_error.log' % (starttime, dev_ip), 'a') as f:
                            f.write(str('post sds log failed!'))
                        return file_path
                else:
                    JobViewSet.job_fail(job_id)
                    path_file = error_path+r'error_red_download%s' % start_time
                    if not os.path.exists(path_file):
                        os.makedirs(path_file)
                    with open(path_file + '/%s_%s_error.log' % (starttime, dev_ip), 'a') as f:
                        f.write('Parameters error!\n')
                    return file_path
            else:
                JobViewSet.job_fail(job_id)
                path_file = error_path+r'error_red_download%s' % start_time
                if not os.path.exists(path_file):
                    os.makedirs(path_file)
                with open(path_file + '/%s_%s_error.log' % (starttime, dev_ip), 'a') as f:
                    f.write(str('get token failed!\n'))
                return file_path
        except Exception as e:
            JobViewSet.job_fail(job_id)
            path_file = error_path + r'error_red_download%s' % start_time
            if not os.path.exists(path_file):
                os.makedirs(path_file)
            with open(path_file + '/%s_%s_error.log' % (starttime, dev_ip), 'a') as f:
                f.write(str(e))
            return file_path
