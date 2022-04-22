from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import GenericAPIView
from web.golobal import APIResponse
from web.init.parse_commands import read_xml
from web.models import Commands, Policies
from web.serializer import PolicyWriteSerializer


# 初始化数据库
class InitDatabase(GenericAPIView):
    serializer_class = PolicyWriteSerializer
    filter_backends = [DjangoFilterBackend]

    @staticmethod
    def get(request):

        # 定义全量采集策略
        full_collection = Policies(id=1, policy_name='全量采集', custom=1)
        # 全量采集策略指令文档路径
        full_filepath = "web/init/om_cmds_all.xml"
        # 全量采集策略及指令初始化
        deal_data(full_collection, full_filepath, "all.")

        # 定义基础采集策略
        base_collection = Policies(id=2, policy_name='基础采集', custom=1)
        # 基础采集策略指令文档路径
        base_filepath = "web/init/om_cmds_basecmd.xml"
        # 基础采集策略及指令初始化
        deal_data(base_collection, base_filepath, "basecmd.")

        # 定义诊断采集策略
        diag_collection = Policies(id=3, policy_name='诊断采集', custom=1, pull_diag=1)
        # 诊断采集策略指令文档路径,无指令文档
        diag_filepath = ""
        # 诊断采集策略及指令初始化
        deal_data(diag_collection, diag_filepath, "")

        # 定义诊断及补充采集策略
        diag_completion = Policies(id=4, policy_name='诊断及补充采集', custom=1, pull_diag=1)
        # 诊断及补充采集策略指令文档路径
        completion_filepath = "web/init/om_cmds_diag_completion.xml"
        # 诊断及补充采集策略及指令初始化
        deal_data(diag_completion, completion_filepath, "diag_completion.")

        # 定义S125采集策略
        s125_collection = Policies(id=5, policy_name='S125采集', custom=1, pull_diag=1, pull_log=1)
        # S125采集策略指令文档路径
        s125_filepath = "web/init/om_cmds_S125.xml"
        # S125采集策略及指令初始化
        deal_data(s125_collection, s125_filepath, "S125.")

        # 定义无线采集策略
        wireless_collection = Policies(id=6, policy_name='无线采集', custom=1)
        # 无线采集策略指令文档路径
        wireless_filepath = "web/init/network.xml"
        # 无线采集策略及指令初始化
        deal_data(wireless_collection, wireless_filepath, "all.")

        # 定义H3C服务器采集策略
        h3c_server = Policies(id=7, policy_name='H3C服务器采集', custom=1, policy_category=1)
        # H3C服务器采集策略指令文档路径,无指令文档
        h3c_filepath = ""
        # H3C服务器采集策略及指令初始化
        deal_data(h3c_server, h3c_filepath, "")

        # 定义HPE服务器采集策略
        hpe_server = Policies(id=8, policy_name='HPE服务器采集', custom=1, policy_category=1)
        # HPE服务器采集策略指令文档路径,无指令文档
        hpe_filepath = ""
        # HPE服务器采集策略及指令初始化
        deal_data(hpe_server, hpe_filepath, "")

        # 定义3Par采集策略
        three_par = Policies(id=9, policy_name='3Par采集', custom=1, policy_category=2)
        # 3Par采集策略指令文档路径
        three_filepath = "web/init/om_cmds_3PAR.xml"
        # 3Par采集策略及指令初始化
        deal_data(three_par, three_filepath, "3PAR.")

        return APIResponse(0, 'init Success!')


def deal_data(policy, filepath, prefix):
    with transaction.atomic():
        policy.save()
        command_list = []
        if filepath:
            commands = read_xml(filepath, prefix)
            for one in commands:
                command = Commands.objects.create(content=one.content,
                                                  gather_time=one.gather_time,
                                                  inview=one.inview,
                                                  outview=one.outview,
                                                  depend_script=one.depend_script,
                                                  depend_script2=one.depend_script2,
                                                  yes_no=one.yes_no)
                command_list.append(command)

        policy.commands.set(command_list)
