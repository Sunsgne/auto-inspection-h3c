import json
import logging
import os
import zipfile

from django.db.models import Q
from django.http import JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import GenericAPIView

import web
from dzkfcollector.settings import SERVICE_TFTP_IP, SERVICE_MAP_FILE_PATH
from web.ansible.playbook import PlaybookCli
from web.golobal import MyPagination, APIResponse
from web.models import Devices, Jobs, Policies, Settings, PolicyJob
from web.serializer import DevicesSerializer, DeviceSerializer
import web.utils.logs_green
import web.utils.logs_red
import web.utils.filezip
from web.utils.constant import SERVER_RUN, SERVER_START, SERVER_STOP
from web.utils.thread_pool import global_thread_pool
import queue
import time
from web.views.job_view import JobViewSet
import threading

lock = threading.RLock()

q = queue.Queue()
logger = logging.getLogger('linux_collector')
head_path = SERVICE_MAP_FILE_PATH


class DeviceLogViewSet(GenericAPIView):

    """
    设备批量操作
    """
    queryset = Jobs.objects.select_related().all()
    serializer_class = DevicesSerializer
    filter_backends = [DjangoFilterBackend]
    def post(self, request):
        """
               批量采集任务
        # """
        try:
            # 获取前端传的值，采集id和所有的设备
            req_data = json.loads(request.body.decode())
            # 设备id
            data = req_data[0]["data"]
            # 设备采集策略id
            collect_policy = req_data[0]["collect_policy"]
            # 采集类型
            device_category = req_data[0]["device_category"]
            dev_id = []
            for i in data:
                id = i['id']
                dev_id.append(id)
            # 去查询设备是否在运行中或者已经创建
            jobs_querys = Jobs.objects.values().filter(Q(device__id__in=dev_id) & (Q(status=SERVER_START) | Q(status=SERVER_RUN))).last()
            # 如果任务没有被创建
            if not jobs_querys:
                # 将所有的设备的详情查询出来
                dev_queryset = Devices.objects.values("device_ip", "user_name", "user_psw", "id").filter(id__in=dev_id)
                # 将数据序列化
                dev_list = DeviceSerializer(instance=dev_queryset, many=True).data
                # 获取当前时间
                starttime = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
                # 获取文件存放路径
                setting = Settings.objects.get(id=1).setting_val
                # 添加文件路径头
                settings = head_path + setting
                # 判断文件夹路径是否存在
                if os.path.isdir(settings):
                    pass
                else:
                    os.makedirs(settings)
                # 在文件目录下打包
                zip_path = '%s/%s_%s.%s' % (settings, starttime, collect_policy, "zip")
                zip_name = '%s_%s.%s' % (starttime, collect_policy, "zip")
                zf = zipfile.ZipFile(zip_path, mode='w', compression=zipfile.ZIP_DEFLATED)
                zf.close()
                # 创建一个父任务
                policies_job = PolicyJob.objects.create(collect_policy=collect_policy, file_name=zip_name,
                                                        device_category=device_category, file_path=zip_path)
                for dev in dev_list:
                    # 遍历设备，每个设备创建单独的线程
                    job_id = create_job(dev['id'], policies_job.id)
                    future = global_thread_pool.executor.submit(worker, dev, policies_job, zip_path, settings, job_id)
                return APIResponse(0, '任务创建成功!', {'content': dev_queryset, 'page': 0, 'size': 20, 'total': 1}, 1)
            else:
                return APIResponse(1, '已选设备中存在正在执行采集的设备，请勿重复选择！')
        except Exception as e:
            logger.error("Jobs not run :"+str(e))
            return APIResponse(1, '执行异常：' + str(e))

    def put(self, request):
        """
        批量停止采集
        """
        # 获取到传入的设备id
        req_data = json.loads(request.body.decode())
        s1 = []
        for i in req_data:
            id = i['id']
            s1.append(id)
        try:
            # 获取当前运行中的任务数量
            count = Jobs.objects.filter(Q(id__in=s1) & (Q(status=SERVER_START) | Q(status=SERVER_RUN))).count()
            if count:
                # 将当前任务状态修改为停止
                Jobs.objects.filter(Q(id__in=s1) & (Q(status=SERVER_START) | Q(status=SERVER_RUN))).update(status=SERVER_STOP)
                msg = ("成功停止"+str(count)+"台设备")
            else:
                msg = "请选择运行中的设备"
            return JsonResponse({'code': 0, 'msg': msg})
        except Exception as e:
            logger.error('stop jobs failed, cause: %s' % str(e))
            return JsonResponse({'code': 1, 'msg': '停止失败，错误详情为：' + str(e)})


def worker(dev, policies_job, zip_path, settings, job_id):
    # 调用方法执行，返回文件地址集合
    file_name = job_log(dev, policies_job, settings, job_id)
    lock.acquire()
    # 对zip文件追加打包
    web.utils.filezip.file_zip(zip_path, file_name, policies_job)
    lock.release()


def job_log(device, policies_job, settings, job_id):
        dev = []
        dev.append(device)
        policies_jobid = policies_job.id
        # job_id = create_job(device['id'], policies_jobid)
        Jobs.objects.filter(Q(id=job_id)).update(status=SERVER_RUN)
        collect_policy = int(policies_job.collect_policy)
        policies = Policies.objects.get(id=collect_policy)
        if policies.policy_name == "HPE服务器采集":
            green = web.utils.logs_green.get_info(dev, job_id)
            return green
        elif policies.policy_name == "H3C服务器采集":
            red = web.utils.logs_red.get_info(dev, job_id)
            return red
        commands_list = policies.commands.values("protocol", "content", "gather_time", "inview", "outview",
                                                 "depend_script", "depend_script2", "yes_no").all()
        commands = []
        if commands_list:
            for command in commands_list:
                command_json = json.dumps(command)
                commands.append(command_json)
        file_path = []
        try:
            # 判断commands指令是否存在
            if commands:
                if policies.policy_name == "3Par采集":
                    adhocCli = PlaybookCli(dev, settings)
                    par = adhocCli.run_3par_commands(commands,
                                                     'http://%s:9992/api/web/jobs/%s/progress?progress={0}' % (
                                                     SERVICE_TFTP_IP, job_id))
                    if not par:
                        return file_path
                    else:
                        file_path = file_path + par
                else:
                    adhocCli = PlaybookCli(dev, settings)
                    adh = adhocCli.run_commands(commands,
                                                'http://%s:9992/api/web/jobs/%s/progress?progress={0}' % (
                                                SERVICE_TFTP_IP, job_id))
                    # 判断任务是否已经停止
                    if not adh:
                        file_path = []
                        return file_path
                    else:
                        file_path = file_path + adh
            # 正常就返回路径；添加到集合里
            # 日志采集
            if policies.pull_diag == 1:
                adhocCli = PlaybookCli(dev, settings)
                diag = adhocCli.run_diag()
                if not diag:
                    file_path = []
                    return file_path
                else:
                    file_path = file_path+diag
        except Exception as e:
            logger.error('execute collection jobs failed, cause: %s' % str(e))
            # 失败抛异常
            for fn in file_path:
                # 判断文件是否存在
                if os.path.exists(fn):
                    os.remove(fn)
            # 更新失败状态,返回
            file_path = []
            JobViewSet.job_fail(job_id)
            return file_path
        # 更新成功，返回
        JobViewSet.dev_job(job_id, '100')
        JobViewSet.job_success(job_id)
        return file_path


def create_job(devid, policies_jobid):
    job = Jobs.objects.filter(device=devid, is_recent=1).last()
    if job:
        job.is_recent = 0
        job.save()
    dev = Devices.objects.get(id=devid)
    plicies_job = PolicyJob.objects.get(id=policies_jobid)
    newjobs = Jobs.objects.create(device=dev, policyJob=plicies_job, collect_progress="0", status=SERVER_START, is_recent=1)
    return newjobs.id
