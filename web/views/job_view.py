from django.db.models import Q
from django.http import JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import GenericAPIView
from web.golobal import APIResponse
from web.models import Jobs
from web.serializer import JobsSerializer
from web.utils.constant import SERVER_RUN, SERVER_START, SERVER_STOP, SERVER_SUCCESS, SERVER_FAIL


class JobViewSet(GenericAPIView):
    """
   巡检任务相关操作
   """
    queryset = Jobs.objects.select_related().all()
    serializer_class = JobsSerializer
    filter_backends = [DjangoFilterBackend]

    def post(self, request, *args, **kwargs):
        """
       创建任务
       """
        job_ser = self.get_serializer(data=request.data)  # 传入要修改的对象和数据
        if job_ser.is_valid():  # 校验数据
            dev_id = request.data.get('device')
            job_ser.create(validated_data=job_ser.validated_data, dev_id=dev_id)
            return APIResponse(0, '创建任务成功!', {'content': job_ser.data, 'page': 1, 'size': 20, 'total': 1}, 1)
        else:
            return APIResponse(1, '创建任务失败!')

    def get(self, request):
        """
        查询任务列表
        """
        qs = self.get_queryset()
        ser = self.get_serializer(instance=qs, many=True)
        return APIResponse(0, '查询任务列表成功!',
                           {'content': ser.data, 'page': 0, 'size': len(ser.data), 'total': len(ser.data)},
                           len(ser.data))

    # 获取当前的百分比,还有当前任务的id,传入新的接口中
    def dev_job(id, progress):
        job = Jobs.objects.get(id=id)
        if job.status == SERVER_START or job.status == SERVER_RUN:
            job.collect_progress = progress
            job.save()
            return True
        else:
            return False

    def progress(request, pk):
        if request.method == "GET":
            progress = request.GET.get('progress')
            if int(progress) >= 80:
                progress = "80"
            job = Jobs.objects.get(id=pk)
            job.collect_progress = progress
            job.save()
            if job.status == SERVER_START or job.status == SERVER_RUN:
                return JsonResponse({'code': 0, 'keep_do': True})
            else:
                return JsonResponse({'code': 0, 'keep_do': False})
        return JsonResponse({'code': 1, 'msg': 'HTTP请求错误，请使用GET模式!'})

    # 判断完成修改状态为成功
    def job_success(id):
        count = Jobs.objects.filter(Q(id=id) & Q(status=SERVER_STOP)).count()
        if not count:
            job = Jobs.objects.get(id=id)
            job.status = SERVER_SUCCESS
            job.save()
            return job.status
        else:
            return count

    # 判断失败修改状态为失败
    def job_fail(id):
        count = Jobs.objects.filter(Q(id=id) & Q(status=SERVER_STOP)).count()
        if not count:
            job = Jobs.objects.get(id=id)
            job.status = SERVER_FAIL
            job.save()
            return job.status
        else:
            return count

