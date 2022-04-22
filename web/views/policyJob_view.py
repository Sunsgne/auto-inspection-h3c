from django.http import StreamingHttpResponse
from rest_framework.generics import GenericAPIView
from web.models import PolicyJob
from web.golobal import APIResponse, MyPagination
from web.serializer import PolicyJobSerializer, PolicyJobFilter
from django_filters.rest_framework import DjangoFilterBackend
import logging

logger = logging.getLogger('linux_collector')


class PolicyJobViewSet(GenericAPIView):
    # 查询全部的策略表
    queryset = PolicyJob.objects.all().order_by('-update_time')
    # 设置序列化也就是返回数据的模板，按照给定的返回
    serializer_class = PolicyJobSerializer
    # 指定过滤器和过滤字段集合
    # 这个过滤器是框架自带的，后面的字段是Policies表中的过滤字段，这个过滤器的作用就是增加where语句，根据前端传来的值获取不同的数据
    filter_backends = [DjangoFilterBackend]
    filter_class = PolicyJobFilter
    pagination_class = MyPagination
    # filter_fields = ['file_name']

    def get(self, request):
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
                # 序列化返回(instance是表示使用哪个数据集合进行模式话处理，many=True表示获取到多个对象集合，默认是many=False只能获取到一个对象)
                policyJob = self.get_serializer(instance=pagers, many=True)
                return APIResponse(0, '成功获取筛选和排序后的策略采集结果列表!', {'content': policyJob.data,
                                                           'page': int(now_page), 'size': int(now_size),
                                                           'total': len(qs)}, len(qs))
            else:
                return APIResponse(0, '查询列表为空!',
                                   {'content': [], 'page': int(now_page), 'size': int(now_size), 'total': 0}, 0)
        except Exception as e:
            logger.error('get policy job list failed, cause: %s ' % str(e))
            return APIResponse(1, '查询列表出现异常，详细原因为：' + str(e))

    def download(request, id):
        """
        查询数据包列表
        """
        if request.method == "GET":
            # id = request.GET.get('id')
            policyJob = PolicyJob.objects.get(id=id)
            the_file_name = policyJob.file_path

            def file_iterator(file_name, chunk_size=512):
              try:
                with open(file_name, "rb") as f:
                    while True:
                        c = f.read(chunk_size)
                        if c:
                            yield c
                        else:
                            break
              except Exception as e:
                logger.error('download file failed, cause: %s ' % str(e))

            response = StreamingHttpResponse(file_iterator(the_file_name))
            logger.info('download file: %s' % the_file_name)
            response['Content-Type'] = 'application/octet-stream'
            response['Content-Disposition'] = 'attachment;filename="{0}"'.format(policyJob.file_name)
            return response
