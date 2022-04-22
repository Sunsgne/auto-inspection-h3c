import logging

from django.db.models import Q
from django.http import JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import GenericAPIView

from web.utils.connection_utils import conn_ping, conn_ssh, q, worker
from web.serializer import *
from web.golobal import APIResponse, MyPagination
from web.utils.thread_pool import global_thread_pool


logger = logging.getLogger('linux_collector')


class DeviceViewSet(GenericAPIView):
    """
    单设备相关操作，基于主键操作
    """
    queryset = Devices.objects.all()
    serializer_class = DevicesSerializer
    filter_backends = [DjangoFilterBackend]

    def get(self, request, pk):
        """
        单设备详情的查询
        """
        device = self.get_object()
        device_ser = self.get_serializer(instance=device)
        return APIResponse(0, '查询设备详情成功!', {'content': device_ser.data, 'page': 0, 'size': 20, 'total': 1}, 1)

    def post(self, request):
        """
        新增设备
        """
        device_ser = self.get_serializer(data=request.data)  # 传入要修改的对象和数据
        if device_ser.is_valid():  # 校验数据
            device = device_ser.save()

            # 异步测试连通性
            # 判断线程是否正在运行，没有则唤醒
            if not global_thread_pool.is_running('conn'):
                task1 = global_thread_pool.executor.submit(add_conn, device)
                global_thread_pool.future_dict['conn'] = task1

            return APIResponse(0, '新增设备成功!', {'content': device_ser.data, 'page': 0, 'size': 20, 'total': 1}, 1)
        else:
            return APIResponse(1, '新增设备失败，可能是名称重复或其他数据格式错误！')

    def put(self, request, pk):
        """
        单设备修改
        """
        try:
            device = self.get_object()
            dev_serializer = self.get_serializer(instance=device, data=request.data)
            if dev_serializer.is_valid():
                new = dev_serializer.save()

                # 异步测试连通性
                # 判断线程是否正在运行，没有则唤醒
                if not global_thread_pool.is_running('conn'):
                    task1 = global_thread_pool.executor.submit(update_conn, new)
                    global_thread_pool.future_dict['conn'] = task1

                return APIResponse(0, '更新设备成功!', {'content': dev_serializer.data, 'page': 0, 'size': 20, 'total': 1}, 1)
            else:
                return APIResponse(1, '数据格式错误，更新设备失败！')
        except Exception as e:
            logger.error('update device failed, cause: %s' % str(e))
            return APIResponse(1, '数据修改异常，异常原因是：' + str(e))

    def delete(self, request, pk):
        """
        删除指定设备
        """
        self.get_object().delete()
        return APIResponse(0, '删除成功!')


def add_conn(device):
    # 操作数据库标志
    flag = False

    # ping连通性测试
    ping_res = conn_ping(device.device_ip)

    if ping_res:
        device.ping_status = 1
        flag = True

    # 根据设备类型，判断是否进行ssh连通性测试
    # 网络设备进行ssh，服务器无需ssh
    if device.device_category != 'server':
        # ssh连通性测试
        ssh_res = conn_ssh(device)

        if ssh_res:
            device.ssh_status = 1
            flag = True

    if flag:
        device.save()


def update_conn(device):
    # 操作数据库标志
    flag = False

    # ping连通性测试
    ping_res = conn_ping(device.device_ip)

    if ping_res:
        if device.ping_status == 0:
            device.ping_status = 1
            flag = True
    else:
        if device.ping_status == 1:
            device.ping_status = 0
            flag = True

    # 根据设备类型，判断是否进行ssh连通性测试
    # 网络设备进行ssh，服务器无需ssh
    if device.device_category != 'server':
        # ssh连通性测试
        ssh_res = conn_ssh(device)

        if ssh_res:
            if device.ssh_status == 0:
                device.ssh_status = 1
                flag = True
        else:
            if device.ssh_status == 1:
                device.ssh_status = 0
                flag = True

    if flag:
        device.save()


class DeviceListViewSet(GenericAPIView):
    """
    设备批量操作
    """
    queryset = Devices.objects.all().order_by('-import_time')
    serializer_class = DevicesSerializer
    # 指定过滤器和过滤字段集合
    filter_backends = [DjangoFilterBackend]
    filter_class = DevicesFilter
    pagination_class = MyPagination

    def assembleList(self, data):
        """
        反向关联查询，并找出唯一值拼装
        """
        devids = [i['id'] for i in data]
        queryset = Jobs.objects.all().filter(Q(device_id__in=devids) & Q(is_recent=1))
        for i in data:
            flag = False
            for s in queryset:
                if i['id'] == s.device_id:
                    i['job'] = JobsSerializer(instance=s).data
                    flag = True
                    break
            if not flag:
                i['job'] = ''
        return data

    def get(self, request):
        """
        查询设备所有列表，支持条件查询和分页(分页从第1页开始)
        """
        qs = self.get_queryset()
        qs = self.filter_queryset(qs)
        now_page = request.GET.get('page')
        now_size = request.GET.get('size')
        device_name = request.GET.get('device_name')
        if device_name:
            qs = qs.filter(Q(device_name__contains=device_name)|Q(device_ip__contains=device_name))
        try:
            self.request.GET._mutable = True  # 为了适应前端page不能从1开始
            if now_page:
                self.request.GET['page'] = int(now_page) + 1
            else:
                self.request.GET['page'] = 1
                now_page = 0
                now_size = 10
            # 页数超出范围，该处会抛出异常Invalid page.
            pagers = self.paginate_queryset(qs)
            if pagers:
                serializer_obj = self.get_serializer(instance=pagers, many=True)
                assemble_data = self.assembleList(serializer_obj.data)
                return APIResponse(0, '成功获取筛选和排序后的设备列表!', {'content': assemble_data,
                                                           'page': int(now_page), 'size': int(now_size),
                                                           'total': len(qs)}, len(qs))
            else:
                return APIResponse(0, '查询列表为空!',
                                   {'content': [], 'page': int(now_page), 'size': int(now_size), 'total': len(qs)}, len(qs))
        except Exception as e:
            # 解决页面偶现无效页问题，若为无效页，则返回空列表
            if 'Invalid page.' == str(e):
                return APIResponse(0, '查询列表为空!',
                                   {'content': [], 'page': int(now_page), 'size': int(now_size), 'total': len(qs)}, len(qs))
            else:
                logger.error('get device list failed, cause: %s ' % str(e))
                return APIResponse(1, '查询列表出现异常')

    def bulk_del(request):
        """
        批量删除设备
        """
        if request.method == "POST":
            # 如果dictData 解析结果为str 则需要 eval() 函数转化成字典
            values = eval(request.body.decode())
            ids = values['ids']
            try:
                queryset = Devices.objects.filter(id__in=ids).all()
                # 过滤采集中的设备，采集中的设备不允许删除
                jobs_queryset = Jobs.objects.filter(Q(device__id__in=ids) & ((Q(status=0) | Q(status=1)))).all().values('device__id')
                not_delete = []
                for device in queryset:
                    for job in jobs_queryset:
                        if job['device__id'] == device.id:
                            not_delete.append(device)
                            break
                    if device not in not_delete:
                        device.delete()
                if not_delete:
                    return JsonResponse({'code': 1, 'msg': '采集中的设备不允许删除，其余设备删除成功！', 'data': '', 'total': len(ids)-len(not_delete)})
                else:
                    return JsonResponse({'code': 0, 'msg': '批量删除设备成功!', 'data': '', 'total': len(ids)})
            except Exception as e:
                logger.error('Delete devices in bulk failed, cause: %s ' % str(e))
                return JsonResponse({'code': 1, 'msg': '数据库操作错误，错误详情为：' + str(e)})
        return JsonResponse({'code': 1, 'msg': 'HTTP请求错误，请使用POST模式!'})

    def batch_conn(request):
        """
        批量测试设备连通性
        """
        if request.method == "POST":
            values = eval(request.body.decode())
            ids = values['ids']
            try:
                queryset = Devices.objects.filter(id__in=ids).all()
                for device in queryset:
                    # 异步测试连通性
                    # 将需要异步处理的任务放入队列
                    q.put(device)
                    # 判断线程是否正在运行，没有则唤醒
                    # if not global_thread_pool.is_running('worker'):
                    global_thread_pool.executor.submit(worker)
                    # global_thread_pool.future_dict['worker'] = future

                return JsonResponse({'code': 0, 'msg': '批量测试设备连通性成功!', 'count': len(ids)})
            except Exception as e:
                logger.error('devices batch connectivity fails, cause: %s' % str(e))
                return JsonResponse({'code': 1, 'msg': '批量测试设备连通性失败!'})
        return JsonResponse({'code': 1, 'msg': 'HTTP请求错误，请使用POST模式!'})
