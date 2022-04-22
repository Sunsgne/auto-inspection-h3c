import logging
import queue

import paramiko
from django import db
from pythonping import ping

from web.models import Devices

q = queue.Queue()
logger = logging.getLogger('linux_collector')


def worker():
    # 如果队列不为空，worker线程会一直从队列取任务并处理
    while not q.empty():
        # 每次唤醒线程执行数据库操作之前最好先关闭老的数据库连接
        db.close_old_connections()
        # 取出任务执行
        one = q.get()
        device = conn(one)

        try:
            # 根据id从数据库中找到相应的设备记录
            data = Devices.objects.get(id=device.id)
            # 若记录存在，则更新数据
            if data:
                # 注意，一定要执行save才能将修改信息保存到数据库
                device.save()
        except Devices.DoesNotExist:
            logger.error('device[name:%s, ip:%s] does not exist!' % (device.device_name, device.device_ip))
            continue


def conn(device):
    # ping连通性测试
    ping_res = conn_ping(device.device_ip)

    if ping_res:
        device.ping_status = 1
    else:
        device.ping_status = 0

    # 根据设备类型，判断是否进行ssh连通性测试
    # 网络设备进行ssh，服务器无需ssh
    if device.device_category != 'server':
        # ssh连通性测试
        ssh_res = conn_ssh(device)

        if ssh_res:
            device.ssh_status = 1
        else:
            device.ssh_status = 0

    return device


def conn_ping(ip):
    response_list = ping(target=ip, count=1, verbose=True)
    for res in response_list:
        if res.success:
            logger.info('ping %s is ok' % ip)
        else:
            logger.warning('ping %s is fail' % ip)

        return res.success


def conn_ssh(device):
    ssh = paramiko.SSHClient()
    # 跳过远程连接中选择‘是’的环节
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname=device.device_ip,
                    username=device.user_name,
                    password=device.user_psw,
                    allow_agent=False,
                    look_for_keys=False,
                    timeout=20.0,
                    banner_timeout=20.0,
                    auth_timeout=20.0)
    except Exception as e:
        logger.warning('ssh connect to ' + device.device_ip + ' fail, cause: ' + str(e))
        return False
    finally:
        # 关闭SSHClient
        ssh.close()

    logger.info('ssh connect to %s success' % device.device_ip)
    return True
