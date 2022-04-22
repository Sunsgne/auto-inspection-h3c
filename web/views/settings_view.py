from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import GenericAPIView

from web.golobal import APIResponse, MyPagination
from web.models import Settings
from web.serializer import SettingsSerializer, SettingsFilter


class SettingsViewSet(GenericAPIView):
    """
    系统设置相关
    """
    queryset = Settings.objects.all()
    serializer_class = SettingsSerializer
    filter_backends = [DjangoFilterBackend]
    filter_class = SettingsFilter
    pagination_class = MyPagination

    def get(self, request):
        """
        查询设置项所有列表，支持条件查询和分页(分页从第1页开始)
        """
        qs = self.get_queryset()
        qs = self.filter_queryset(qs)
        now_page = request.GET.get('page')
        now_size = request.GET.get('size')
        try:
            self.request.GET._mutable = True  # 为了适应前端page不能从1开始
            if now_page:
                self.request.GET['page'] = int(now_page) + 1
            else:
                self.request.GET['page'] = 1
                now_page = 0
                now_size = 10
            pagers = self.paginate_queryset(qs)
            if pagers:
                serializer_obj = self.get_serializer(instance=pagers, many=True)
                return APIResponse(0, '成功获取筛选和排序后的设置项列表!', {'content': serializer_obj.data,
                                                            'page': int(now_page), 'size': int(now_size), 'total': len(qs)}, len(qs))
            else:
                return APIResponse(0, '查询列表为空!', {'content': [], 'page': int(now_page), 'size': int(now_size), 'total': 0}, 0)
        except Exception as e:
            return APIResponse(1, '查询列表出现异常，详细原因为：' + str(e))

    def post(self, request):
        """
        新增设置项
        """
        settings_ser = self.get_serializer(data=request.data)  # 传入要修改的对象和数据
        if settings_ser.is_valid():  # 校验数据
            settings_ser.save()
            return APIResponse(0, '新增设置项成功!', {'content': settings_ser.data, 'page': 1, 'size': 20, 'total': 1}, 1)
        else:
            return APIResponse(1, '新增设置项失败!')

    def put(self, request, pk):
        """
        修改设置项
        """
        settings = self.get_object()
        settings_serializer = self.get_serializer(instance=settings, data=request.data)
        if settings_serializer.is_valid():
            settings_serializer.save()
            return APIResponse(0, '更新设置项成功!', {'content': settings_serializer.data, 'page': 1, 'size': 20, 'total': 1}, 1)
        else:
            return APIResponse(1, '数据格式错误，更新设置项失败!')

    # def delete(self, request, pk):
    #     """
    #     删除指定设备
    #     """
    #     self.get_object().delete()
    #     return APIResponse(0, '删除成功!')
