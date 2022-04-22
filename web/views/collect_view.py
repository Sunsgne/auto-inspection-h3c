import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import GenericAPIView

from web.golobal import APIResponse
from web.models import Policies, Commands
from web.serializer import PolicyListSerializer, CommandsSerializer, PolicyReadSerializer, PolicyWriteSerializer


logger = logging.getLogger('linux_collector')


# 查看采集策略列表,只返回部分字段
class PolicyListViewSet(GenericAPIView):
    # 查询全部的策略表
    queryset = Policies.objects.all()
    # 设置序列化也就是返回数据的模板，按照给定的返回
    serializer_class = PolicyListSerializer
    # 指定过滤器和过滤字段集合
    # 这个过滤器是框架自带的，后面的字段是Policies表中的过滤字段，这个过滤器的作用就是增加where语句，根据前端传来的值获取不同的数据
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['policy_category']

    def get(self, request):
        # 获取到全部数据
        qs = self.get_queryset()
        # 根据过滤器过滤不需要的数据
        qs = self.filter_queryset(qs)
        # 序列化返回(instance是表示使用哪个数据集合进行模式话处理，many=True表示获取到多个对象集合，默认是many=False只能获取到一个对象)
        policies = self.get_serializer(instance=qs, many=True)
        return APIResponse(0, '查询采集策略列表成功!', {'content': policies.data}, len(policies.data))


# 基于主键查询采集策略详情,策略中的关联指令id转化为指令对象详细信息
class PolicyReadViewSet(GenericAPIView):
    queryset = Policies.objects.all()
    serializer_class = PolicyReadSerializer
    filter_backends = [DjangoFilterBackend]

    def get(self, request, pk):
        try:
            policy = self.get_object()
            one = self.get_serializer(instance=policy)
            return APIResponse(0, '查询采集策略详情成功!', {'content': one.data}, 1)
        except Exception as e:
            logger.error('get policy detail failed, cause: %s' % str(e))
            return APIResponse(1, '查询采集策略详情失败!')


# 增加单个采集策略,关联指令传id列表
class PolicyWriteViewSet(GenericAPIView):
    queryset = Policies.objects.all()
    # 这里使用了反序列化
    serializer_class = PolicyWriteSerializer
    filter_backends = [DjangoFilterBackend]

    def post(self, request):
        # 传入要添加的对象数据
        policy = self.get_serializer(data=request.data)

        # 数据校验
        # 这里的is_valid表示的是一套框架自带的校验流程，校验完成后如果没问题就可以将前端的数据保存
        if policy.is_valid():
            policy.save()
            return APIResponse(0, '新增采集策略成功!', {'content': policy.data}, 1)
        else:
            return APIResponse(1, '数据有误，新增采集策略失败!')


# 基于主键修改/删除采集策略,修改时关联指令传id列表
class PolicyWrite2ViewSet(GenericAPIView):
    queryset = Policies.objects.all()
    serializer_class = PolicyWriteSerializer
    filter_backends = [DjangoFilterBackend]

    def put(self, request, pk):
        try:
            old = self.get_object()
            new = self.get_serializer(instance=old, data=request.data)
            if new.is_valid():
                new.save()
                return APIResponse(0, '更新采集策略成功!', {'content': new.data}, 1)
            else:
                return APIResponse(1, '数据有误，更新采集策略失败!')
        except Exception as e:
            logger.error('update policy failed, cause: %s' % str(e))
            return APIResponse(1, '更新采集策略失败!')

    def delete(self, request, pk):
        try:
            self.get_object().delete()
            return APIResponse(0, '删除采集策略成功!', None, 1)
        except Exception as e:
            logger.error('delete policy failed, cause: %s' % str(e))
            return APIResponse(1, '删除采集策略失败!')


# 查看采集指令列表
class CommandsViewSet(GenericAPIView):
    queryset = Commands.objects.all()
    serializer_class = CommandsSerializer
