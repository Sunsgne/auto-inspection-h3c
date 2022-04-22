import time
import os
from ansible.plugins.callback import CallbackBase

# tftp服务器文件存放路径
SERVICE_TFTP_FILE_PATH = '/var/lib/tftpboot/'


class CallbackModule(CallbackBase):
    '''
    ansible的callback插件，独立于Django架构，无法直接引用Django工程中的其他python模块
    '''

    def __init__(self, *args, **kwargs):
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}
        super(CallbackModule, self).__init__()

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.host_failed[result._host.get_name()] = result

    def v2_runner_on_ok(self, result):
        self.host_ok[result._host.get_name()] = result

    def v2_runner_on_unreachable(self, result):
        self.host_unreachable[result._host.get_name()] = result

    def v2_playbook_on_stats(self, stats):
        ct = time.time()
        local_time = time.localtime(ct)
        data_head = time.strftime("%Y%m%d%H%M%S", local_time)
        for host, result in self.host_ok.items():
            # 仅在对模块network.h3c.h3c_command操作时，将回显结果进行记录
            if 'h3c_command' in result._task.action:
                path = "{0}ssh_{1}_{2}.json".format(SERVICE_TFTP_FILE_PATH, host, data_head)
                with open(path, 'w', encoding='UTF-8') as json_file:
                    json_file.write(result._result.get('stdout', None))
            # 模块为network.h3c.h3c_diag时，记录保存路径
            elif 'h3c_diag' in result._task.action:
                filename = result._result.get('stdout', None)
                path = os.path.join(SERVICE_TFTP_FILE_PATH, filename)
            self._display.display('h3c_result:%s %s %s' % (host, 'success', path))
        for host, result in self.host_failed.items():
            self._display.display('h3c_result:%s %s %s' % (host, 'failed', result._result.get('msg', None)))
        for host, result in self.host_unreachable.items():
            self._display.display('h3c_result:%s %s %s' % (host, 'unreachable', result._result.get('msg', None)))
