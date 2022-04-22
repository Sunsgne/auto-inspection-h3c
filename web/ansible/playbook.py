import os
import re
import time
import logging
from dzkfcollector.settings import BASE_DIR, SERVICE_TFTP_IP

# yml文件存放路径
yaml_file_path = os.path.expandvars('$HOME') + '/yml/'
if not os.path.isdir(yaml_file_path):
    os.makedirs(yaml_file_path)

logger = logging.getLogger('linux_collector')

class PlaybookCli():
    def __init__(self, hosts, server_file_path):
        '''
        :param hosts 主机信息：[{'device_ip':'','user_name':'','user_psw':'','super_psw':''}]
        :param server_file_path 诊断日志保存路径
        :param collect_policy 采集策略id
        '''
        # 主机信息集：[{'device_ip':'','user_name':'','user_psw':'','super_psw':''}]
        self.__hosts = hosts
        self.__server_file_path = server_file_path
        if not os.path.isdir(self.__server_file_path):
            os.makedirs(self.__server_file_path)
        # 诊断采集执行超时时间：600s
        self.__diag_timeout = 600
        # 命令执行超时时间：60s
        self.__command_timeout = 60

    def run_diag(self):
        '''
        运行诊断采集
        '''
        for host in self.__hosts:
            ip = host['device_ip']
            ct = time.time()
            local_time = time.localtime(ct)
            data_head = time.strftime("%Y%m%d%H%M%S", local_time)
            temp_file_path = yaml_file_path + '%s_%s_playbook.yaml' % (ip, data_head)
            with open(temp_file_path, 'w') as file:
                file.write('---\n')
                file.write('- hosts: %s\n' % ip)
                file.write('  connection: network.h3c.network_cli_diag\n')
                file.write('  gather_facts: no\n')
                file.write('  vars:\n')
                file.write('    ansible_network_os: network.h3c.h3c\n')
                file.write('  tasks:\n')
                file.write('  - network.h3c.h3c_diag:\n')
                file.write('      command: display diagnostic-information\n')
                file.write("      server_ip: '%s'\n" % SERVICE_TFTP_IP)
                file.write("      device_ip: '%s'\n" % ip)
                file.write("      prompt: \n" )
                file.write("        - 'Save or display diagnostic information'\n" )
                file.write("        - '\(\*(\S*)\)\[\S*\]'\n" )
                file.write("        - 'The file already exists, overwrite it'\n" )
                file.write("      answer:\n" )
                file.write("        - 'y'\n" )
                file.write("        - 'use_promat:linux_ansible{0[0]}'\n" )
                file.write("        - 'y'\n" )
                file.write('      timeout: %s\n' % self.__diag_timeout)
        return self.run(temp_file_path)

    def run_3par_commands(self, commands, progress_url):
        '''
        运行3par设备巡检命令
        '''
        return self.run_h3c_commands(commands, progress_url, 'network.h3c.h3c_3par',False)

    def run_commands(self, commands, progress_url):
        '''
        运行普通网络设备巡检命令
        '''
        return self.run_h3c_commands(commands, progress_url, 'network.h3c.h3c_ignore')

    def run_h3c_commands(self, commands, progress_url, network_os,check_device=True):
        '''
          运行命令采集
        '''
        for host in self.__hosts:
            ip = host['device_ip']
            ct = time.time()
            local_time = time.localtime(ct)
            data_head = time.strftime("%Y%m%d%H%M%S", local_time)
            temp_file_path = yaml_file_path + '%s_%s_playbook.yaml'%(ip,data_head)
            with open(temp_file_path,'w') as file:
              file.write('---\n')
              file.write('- hosts: %s\n' % ip)
              file.write('  connection: network_cli\n')
              file.write('  gather_facts: no\n')
              file.write('  vars:\n')
              file.write('    ansible_network_os: %s\n'%network_os)
              file.write('  tasks:\n')
              file.write('  - network.h3c.h3c_command:\n')
              file.write('      command_jsons:\n')
              for command in commands:
                file.write("        - '%s'\n"%command)
              file.write("      progress_url: '%s'\n"%progress_url)
              file.write('      check_device: %s\n' % check_device)
              file.write('      timeout: %s\n'%self.__command_timeout)
            return self.run(temp_file_path)
    
    def run(self, temp_file_path):
        '''
        cmd命令调用playbook
        '''
        try:
            cmd = 'ansible-playbook  %s -i %s/web/ansible/inventory.py ' % (temp_file_path, BASE_DIR)
            logger.info('run cmd: %s'%cmd)
            res = os.popen(cmd)
            output_str = res.read()
            logger.info(output_str)
            # 正则获取处理结果信息，callback.h3c.py中的处理
            pattern = r'h3c_result:(\S+) (\S+) (.*?)\s*$'
            ret = re.search(pattern, output_str)
            if ret:
                result = ret.group(2)
                if 'success' == result:
                    # 执行成功
                    path_list = []
                    path_list.append(ret.group(3))
                    return path_list
                else:
                    error_result = ret.group(3)
                    if '500' in error_result:
                        # 取消执行
                        return False
                    # 执行失败
                    raise Exception(ret.group(3))
        finally:
            # 执行完后，清除临时yaml文件
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.info("removed temp file:%s"%temp_file_path)
