from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework import status
from django.db import DatabaseError


# 响应体封装
class APIResponse(Response):
    def __init__(self, code=0, msg='Get Success!', data=None, total=0, status=None, headers=None,
                 content_type=None, **kwargs):
        dic = {'code': code, 'msg': msg, 'total': total}
        if data:
            dic['data'] = data

        dic.update(kwargs)  # 这里使用update
        super().__init__(data=dic, status=status,
                         template_name=None, headers=headers,
                         exception=False, content_type=content_type)


# 全局异常处理
def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if response is None:
        view = context['view']
        print('[%s]: %s' % (view, exc))
        if isinstance(exc, DatabaseError):
            response = Response({'code': 1, 'msg': '服务器内部错误'}, status=status.HTTP_507_INSUFFICIENT_STORAGE)
        else:
            response = Response({'code': 1, 'msg': '未知错误'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return response


# 分页封装(并非所有接口都需使用，不做全局处理，使用处引用即可)
class MyPagination(PageNumberPagination):
    page_size = 10
    page_query_param = 'page'
    page_size_query_param = 'size'
    max_page_size = 500
