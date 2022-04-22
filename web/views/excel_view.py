import logging

import xlrd
from django.http import FileResponse, JsonResponse
from django.utils import timezone
from rest_framework.views import APIView
from web.models import Devices
from web.utils.thread_pool import global_thread_pool
from web.utils.connection_utils import worker, q

logger = logging.getLogger('linux_collector')


class ExcelViewSet(APIView):
    """
    excel文件导入导出
    """
    dic = {"网络设备": "device", "服务器": "server", "3Par": "3Par", "device": "网络设备", "server": "服务器"}

    def upload_device(request):
        """
        获取前端传过来的excel文件，解析并入库
        """
        if request.method == "POST":
            category = request.POST.get('device_category')

            if category is None:
                return JsonResponse({'code': 1, 'msg': "上传失败，请指定模板类别上传!"})

            files = request.FILES.get('rest_file')
            file_type = files.name.split('.')[1]  # 拿到文件后缀
            file = files.file
            if file_type not in ['xlsx', 'xls']:
                return JsonResponse({'code': 1, 'msg': "文件格式错误，请上传xls或xlsx格式的文件!"})
            # 打开excel文件，并读取去内容
            ExcelFile = xlrd.open_workbook(filename=None, file_contents=file.read())
            sheet = ExcelFile.sheet_by_index(0)
            if sheet is None or ExcelViewSet.dic.get(sheet.name) is None:
                return JsonResponse({'code': 1, 'msg': "文件错误，请使用指定模板上传!"})
            # 根据sheet名称和category限制不能混合导入
            if category != ExcelViewSet.dic.get(sheet.name):
                return JsonResponse({'code': 1, 'msg': "文件错误，请使用相应模板上传!"})
            # 对导入的Excel先做一层过滤
            excel_duply = 0
            new_s = []  # 存储去重后的数据
            for index in range(1, sheet.nrows):  # 根据字典列表的device_name做去重操作
                # 获得行的列对象
                # row{0:'device_name',1:'device_ip',2:'protocal',3:'user_name',4:'user_psw',5:'super_psw'}
                row = sheet.row(index)
                obj = Devices.create(deal_cell(row[0]), deal_cell(row[1]), ExcelViewSet.dic[sheet.name],
                                     deal_cell(row[2]), deal_cell(row[3]), deal_cell(row[4]), deal_cell(row[5]))
                # obj = Devices.create(row[0].value, row[1].value, ExcelViewSet.dic[sheet.name], row[2].value,
                #                      row[3].value, row[4].value, row[5].value)
                if any(d.device_name == obj.device_name for d in new_s):
                    excel_duply = excel_duply + 1
                else:
                    new_s.append(obj)
            # 将导入数据与数据库进行比较，筛选出待新增和待更新的数据
            update_data = []
            create_data = []
            queryset = Devices.objects.filter(device_category=category).all()
            for device in new_s:
                # 根据设备名称查找记录
                flag = False
                for data in queryset:
                    if str(data.device_name) == str(device.device_name):
                        data.device_ip = device.device_ip
                        data.device_category = device.device_category
                        data.protocol = device.protocol
                        data.user_name = device.user_name
                        data.user_psw = device.user_psw
                        data.super_psw = device.super_psw
                        data.import_time = timezone.now()
                        update_data.append(data)
                        flag = True
                        break
                if not flag:
                    create_data.append(device)
            try:
                Devices.objects.bulk_update(update_data, Devices.get_bulk_update_names(), batch_size=5000)
                Devices.objects.bulk_create(create_data)
                names = []
                for one in create_data:
                    names.append(one.device_name)
                created_data = Devices.objects.filter(device_name__in=names, device_category=category).all()

                # 异步测试连通性
                device_list = list(created_data)
                device_list.extend(update_data)

                for device in device_list:
                    # 将需要异步处理的任务放入队列
                    q.put(device)
                    # 判断线程是否正在运行，没有则唤醒
                    # if not global_thread_pool.is_running('excel'):
                    global_thread_pool.executor.submit(worker)
                    # global_thread_pool.future_dict['excel'] = task1

                return JsonResponse({'code': 0, 'msg': '表格里存在' + str(excel_duply) + '重复记录，已被忽略。'
                                                       + '剩下的数据中,有' + str(len(create_data)) + '条被新增到数据库，另外'
                                                       + str(len(update_data)) + '条覆盖更新到数据库'})
            except Exception as e:
                logger.error('Failed to import device, cause: %s' % str(e))
                return JsonResponse({'code': 1, 'msg': '上传失败，失败详情为 :' + str(e)})
        return JsonResponse({'code': 1, 'msg': 'HTTP请求错误，请使用POST模式!'})

    def download_template(request):
        """
        根据前端传来的类别，下载相应的设备导入模板
        """
        category = request.GET.get('category')
        if category:
            reverse_cat = ExcelViewSet.dic[category]
            file_path = 'web/download/' + reverse_cat + '.xlsx'
            disposition = 'attachment; filename=' + reverse_cat + '.xlsx'
            try:
                file = open(file_path, 'rb')
                response = FileResponse(file)
                response['Content-Type'] = 'application/octet-stream'
                response['Content-Disposition'] = disposition.encode('utf-8', 'ISO-8859-1')
                return response
            except Exception as e:
                logger.error('Failed to download device template, cause: %s' % str(e))
                return JsonResponse({'code': 1, 'msg': '服务器上没有该模板文件，错误详情为: ' + str(e)})
        return JsonResponse({'code': 1, 'msg': '下载失败，请重新尝试!'})


def deal_cell(cell):
    # 表格的数据类型
    # ctype : 0 empty, 1 string, 2 number, 3 date, 4 boolean, 5 error
    ctype = cell.ctype
    value = cell.value
    # ctype为2且为浮点
    if ctype == 2 and value % 1 == 0.0:
        # 浮点转成整型
        value = int(value)
        # 转成整型后再转成字符串
        value = str(value)
    return value
