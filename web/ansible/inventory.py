#!/usr/bin/python3

import argparse
import json
import sqlite3
from pathlib import Path
import logging
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# logger = logging.getLogger('linux_collector')
LOG_PATH = os.path.join(BASE_DIR, 'log')
# 如果地址日志文件夹不存在，则自动创建
if not os.path.isdir(LOG_PATH):
    os.mkdir(LOG_PATH)
logging.basicConfig(filename='%s/linux-collecter.log' % LOG_PATH,
                    format='%(levelname)-5s %(asctime)s [%(filename)-9s line %(lineno)-3s]: %(message)s',
                    level=logging.INFO)


def dict_factory(cursor, row):
    '''
    返回dict字典格式数据
    '''
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class ExampleInventory(object):

    def __init__(self):
        self.inventory = {}
        self.read_cli_args()
        try:
            # 建立sqlit3的连接
            conn = sqlite3.connect('%s/db.sqlite3'%BASE_DIR)
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            # Called with `--list`.
            if self.args.list:
                self.inventory = self.group(cursor)
            # Called with `--host [hostname]`.
            elif self.args.host:
                # Not implemented, since we return _meta info `--list`.
                self.inventory = self.hosts(cursor, self.args.host)
            # If no groups or vars are present, return empty inventory.
            else:
                self.inventory = self.empty_inventory()
            inventory_json = json.dumps(self.inventory)
            logging.info(inventory_json)
            print(inventory_json)
        finally:
            # 退出前关闭连接
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def group(self, cursor):
        sql = "select device_ip,user_name,user_psw,super_psw,id from web_devices"
        results = cursor.execute(sql)
        dev_info = results.fetchall()
        return self.device2host(dev_info)
        # pass

    def hosts(self, cursor, device_ip):

        sql = "select device_ip,user_name,user_psw,super_psw,id from web_devices where device_ip in (%s)" % device_ip
        results = cursor.execute(sql)
        dev_info = results.fetchall()   
        return self.device2host(dev_info)
        # pass

    def device2host(self, dev_info):
        all_dict = {}
        all_dict['all'] = {}
        all_dict['all']['hosts'] = []
        all_dict['_meta'] = {}
        all_dict['_meta']['hostvars'] = {}
        for host in dev_info:
            all_dict['all']['hosts'].append(host['device_ip'])
            all_dict['_meta']['hostvars'][host['device_ip']] = {}
            all_dict['_meta']['hostvars'][host['device_ip']]['ansible_ssh_user'] = host['user_name']
            all_dict['_meta']['hostvars'][host['device_ip']]['ansible_ssh_pass'] = host['user_psw']
            # all_dict['_meta']['hostvars'][host['device_ip']]['ansible_network_os'] = 'network.h3c.h3c_ignore'
            # all_dict['_meta']['hostvars'][host['device_ip']]['ansible_connection'] = 'ansible.netcommon.network_cli'
            all_dict['_meta']['hostvars'][host['device_ip']]['ansible_ssh_port'] = 22
            # if 'job_id' in host.keys():
            #   all_dict['_meta']['hostvars'][host['device_ip']]['job_id'] = host['job_id']
            if 'super_psw' in host.keys():
              all_dict['_meta']['hostvars'][host['device_ip']]['ansible_become_password'] = host['super_psw']
              all_dict['_meta']['hostvars'][host['device_ip']]['ansible_become'] = 'yes'
              all_dict['_meta']['hostvars'][host['device_ip']]['ansible_become_method'] = 'enable'
        # print(json.dumps(all_dict,indent=4))
        return all_dict

    # Empty inventory.
    def empty_inventory(self):
        return {'_meta': {'hostvars': {}}}

    # Read the command line args passed to the script.
    def read_cli_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--list', action='store_true')
        parser.add_argument('--host', action='store')
        self.args = parser.parse_args()


# Get the inventory.
ExampleInventory()
