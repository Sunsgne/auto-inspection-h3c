#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 核心类
# 用于读取YAML和JSON格式的文件
import logging

from ansible.parsing.dataloader import DataLoader
# 用于存储各类变量信息
from ansible.vars.manager import VariableManager
# 用于导入资产文件
from ansible.inventory.manager import InventoryManager
# 存储执行hosts的角色信息
from ansible.playbook.play import Play
# ansible底层用到的任务队列
from ansible.executor.task_queue_manager import TaskQueueManager
# 状态回调，各种成功失败的状态
from ansible.plugins.callback import CallbackBase
# from ansible_collections.network.h3c.plugins.callback.h3c import ResultsCollectorJSONCallback
# 新增下面两个调用
from ansible.module_utils.common.collections import ImmutableDict
from ansible import context
import ansible.constants as C

from dzkfcollector.settings import SERVICE_TFTP_IP, SERVICE_TFTP_FILE_PATH
from func_timeout import func_set_timeout, FunctionTimedOut
import shutil
import time
import os


host_dict = {}
logger = logging.getLogger('linux_collector')
status = False


def mkdir(path):
    '''
    创建目录
    :param path 指定的文件目录
    '''
    if os.path.isdir(path):
        pass
    else:
        os.makedirs(path)


class ResultsCollectorJSONCallback(CallbackBase):
    '''
       A sample callback plugin used for performing an action as results come in.
        '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # python3中重载父类构造方法的方式，在Python2中写法会有区别。
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.host_failed[result._host.get_name()] = result

    def v2_runner_on_ok(self, result):
        self.host_ok[result._host.get_name()] = result

    def v2_runner_on_unreachable(self, result):
        self.host_unreachable[result._host.get_name()] = result


class AdhocCli():
    '''
    使用python API调用ansible的执行计划
    '''

    def __init__(self, hosts, server_file_path, collect_policy, job_id, log_path='/var/log/ansible.log'):
        '''
        :param hosts 主机信息：[{'device_ip':'','user_name':'','user_psw':'','super_psw':''}]
        :param server_file_path 诊断日志保存路径
        :param collect_policy 采集策略id
        :param job_id 当前任务的id
        :param log_path  日志路径地址
        '''
        self.__hosts = hosts
        # 日志路径地址
        self.__log_path = log_path
        self.__server_file_path = server_file_path
        mkdir(self.__server_file_path)
        # 诊断采集执行超时时间：600s
        self.__diag_timeout = 600
        # 命令执行超时时间：60s
        self.__command_timeout = 60
        # 采集策略id
        self.__collect_policy = collect_policy
        # 任务id
        self.__job_id = job_id
        # 在这里传递一些参数
        context.CLIARGS = ImmutableDict(module_path=None, verbosity=5, forks=10, become=False,
                                        become_method=None, become_user=None, check=False, diff=False)

    def init_hosts(self, network_os):
        host_dict.clear()
        # 资产配置信息
        self.__DL = DataLoader()
        self.__IM = InventoryManager(loader=self.__DL, sources=None)
        for host in self.__hosts:
            host_dict.update({host['device_ip']:self.__job_id})
            self.__IM.add_host(host['device_ip'], group='all')
            self.__IM.get_host(host['device_ip']).vars['ansible_ssh_user'] = host['user_name']
            self.__IM.get_host(host['device_ip']).vars['ansible_ssh_pass'] = host['user_psw']
            # self.__IM.get_host(host['device_ip']).vars['ansible_connection'] = 'ansible.netcommon.network_cli'
            self.__IM.get_host(host['device_ip']).vars['ansible_network_os'] = network_os #'network.h3c.h3c_ignore'
            self.__IM.get_host(host['device_ip']).vars['ansible_ssh_port'] = 22
            self.__IM.get_host(host['device_ip']).vars['job_id'] = str(self.__job_id)

            if 'super_psw' in host.keys():
                self.__IM.get_host(host['device_ip']).vars['ansible_become'] = 'yes'
                self.__IM.get_host(host['device_ip']).vars['ansible_become_method'] = 'enable'
                self.__IM.get_host(host['device_ip']).vars['ansible_become_password'] = host['super_psw']

        self.__VM = VariableManager(loader=self.__DL, inventory=self.__IM)

    def run_diag(self):
        '''
        运行诊断采集命令
        '''
        # 初始化主机信息及配置信息;network_os采用'network.h3c.h3c'
        self.init_hosts('network.h3c.h3c')

        # 任务内容
        tasks = [dict(
            name="执行设备诊断采集命令",
            action=dict(module="network.h3c.h3c_diag", args=dict(command='display diagnostic-information',
                                                                 device_ip="{{ inventory_hostname }}",
                                                                 server_ip=SERVICE_TFTP_IP,
                                                                 timeout=self.__diag_timeout,
                                                                 # server_file_path= self.__server_file_path,
                                                                 prompt=['Save or display diagnostic information', '\(\*(\S*)\)\[\S*\]', 'The file already exists, overwrite it'],
                                                                 answer=['y', "use_promat:linux_ansible{0[0]}", 'y'])#第二个参数为生成的诊断日志文件名，{0[0]}为文件后缀
                       ))
        ]

        # play的执行对象和模块，这里设置hosts，其实是因为play把play_source和资产信息关联后，执行的play的时候它会去资产信息中设置的sources的hosts文件中
        # 找你在play_source中设置的hosts是否在资产管理类里面。
        play_source = dict(name="Ansible Play",  # 任务名称
                           hosts="all",  # 目标主机，可以填写具体主机也可以是主机组名称
                           # strategy="free",
                           gather_facts="no",  # 是否收集配置信息
                           connection="network.h3c.network_cli_diag",  # 在network_cli基础上，加强了对应答机制的处理
                           # tasks是具体执行的任务，列表形式，每个具体任务都是一个字典
                           tasks=tasks)
        try:
            results_callback = self.run(play_source)
        except FunctionTimedOut as e:
            logger.error(str(e))
            raise Exception

        # 对结果进行处理
        file_path = []
        for host, result in results_callback.host_ok.items():
            filename = result._result.get('stdout', None)
            src_filepath = os.path.join(SERVICE_TFTP_FILE_PATH, filename)
            dst_filepath = os.path.join(self.__server_file_path, filename)
            shutil.move(src_filepath, dst_filepath)
            file_path.append(dst_filepath)
        for host, result in results_callback.host_failed.items():
            if "'ret_code': '500'" in result._result['msg']:
                return status
            else:
                logger.error(result._result['msg'])
                raise Exception
        for host, result in results_callback.host_unreachable.items():
            if "'ret_code': '500'" in result._result['msg']:
                return status
            else:
                logger.error(result._result['msg'])
                raise Exception
        return file_path

    def run_commands(self, commands, progress_url):
        """
            ad-hoc 调用
            资产配置信息  这个是通过 InventoryManager和VariableManager 定义
            执行选项 这个是通过namedtuple来定义
            执行对象和模块 通过dict()来定义
            定义play 通过Play来定义
            最后通过 TaskQueueManager 的实例来执行play
            :return:
            """
        # 初始化主机信息及配置信息;network_os采用'network.h3c.h3c_ignore'，忽略普通错误
        self.init_hosts('network.h3c.h3c_ignore')

        # 任务内容
        tasks = [dict(
                     name="执行设备巡检命令",
                     action=dict(module="network.h3c.h3c_command", args=dict(command_jsons=commands, progress_url=progress_url, timeout=self.__command_timeout, job_id="{{ job_id }}")))
                ]
        # play的执行对象和模块，这里设置hosts，其实是因为play把play_source和资产信息关联后，执行的play的时候它会去资产信息中设置的sources的hosts文件中
        # 找你在play_source中设置的hosts是否在资产管理类里面。
        play_source = dict(name="Ansible Play",  # 任务名称
                           hosts="all",  # 目标主机，可以填写具体主机也可以是主机组名称
                           gather_facts="no",  # 是否收集配置信息
                           # strategy="free",
                           connection="ansible.netcommon.network_cli",
                           # tasks是具体执行的任务，列表形式，每个具体任务都是一个字典
                           tasks=tasks)
        try:
            results_callback = self.run(play_source)
        except FunctionTimedOut as e:
            logger.error(str(e))
            raise Exception

        # 对结果进行处理        # 将结果存入指定路径
        ct = time.time()
        local_time = time.localtime(ct)
        data_head = time.strftime("%Y%m%d%H%M%S", local_time)
        file_path = []
        for host, result in results_callback.host_ok.items():
            json_path = "{0}/ssh_{1}_{2}.json".format(self.__server_file_path, host, data_head)
            with open(json_path, 'a+', encoding='UTF-8') as json_file:
                json_file.write(result._result.get('stdout', None))
            file_path.append(json_path)
        for host, result in results_callback.host_failed.items():
            if "'ret_code': '500'" in result._result['msg']:
                return status
            else:
                logger.error(result._result['msg'])
                raise Exception
        for host, result in results_callback.host_unreachable.items():
            if "'ret_code': '500'" in result._result['msg']:
                return status
            else:
                logger.error(result._result['msg'])
                raise Exception
        return file_path

    # 增加超时处理，防止ansible api死循环
    @func_set_timeout(300)
    def run(self, play_source):
        '''
        运行ansible play
        '''
        # 定义play
        play = Play().load(play_source, variable_manager=self.__VM, loader=self.__DL)
        passwords = dict()  # 这个可以为空，因为在hosts文件中

        results_callback = ResultsCollectorJSONCallback()  # 实例化自定义callback

        TQM = TaskQueueManager(
            inventory=self.__IM,
            variable_manager=self.__VM,
            loader=self.__DL,
            passwords=passwords,
            stdout_callback=results_callback
        )
        # Actually run it
        try:
            TQM.run(play)  # most interesting data for a play is actually sent to the callback's methods
        finally:
            # we always need to cleanup child procs and the structures we use to communicate with them
            TQM.cleanup()
            if self.__DL:
                self.__DL.cleanup_all_tmp_files()

        # Remove ansible tmpdir
        shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)

        return results_callback
