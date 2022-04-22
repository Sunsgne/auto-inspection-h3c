from django.conf.urls import url
from django.urls import path


from web.init.init_database import InitDatabase
from web.init.init_database_setting import SettingsDatabase
from web.views.collect_view import PolicyListViewSet, PolicyReadViewSet, PolicyWriteViewSet, PolicyWrite2ViewSet
from web.views.device_view import DeviceViewSet, DeviceListViewSet
from web.views.excel_view import ExcelViewSet
from web.views.job_view import JobViewSet
from web.views.joblog_view import DeviceLogViewSet
from web.views.settings_view import SettingsViewSet
from web.views.policyJob_view import PolicyJobViewSet


urlpatterns = [
    # 设备相关路由
    # 设备详情增删查
    url(r'^web/device/$', DeviceViewSet.as_view()),
    url(r'^web/device/(?P<pk>\d+)/$', DeviceViewSet.as_view()),
    # 设备列表批量操作、条件分页查询路由
    url(r'^web/devicelist/$', DeviceListViewSet.as_view()),
    # 设备批量删除路由
    url(r'^web/devicelist/bulk_del/$', DeviceListViewSet.bulk_del),
    # 设备批量执行任务
    url(r'^web/devicelog/(?P<pk>\d+)$', DeviceLogViewSet.as_view()),
    # 设备批量停止任务
    url(r'^web/devicelog/$', DeviceLogViewSet.as_view()),
    # 设备批量连通性测试路由
    url(r'^web/devicelist/bulk_conn/$', DeviceListViewSet.batch_conn),
    # 系统设置路由
    url(r'^web/settings/$', SettingsViewSet.as_view()),
    url(r'^web/settings/(?P<pk>\d+)/$', SettingsViewSet.as_view()),
    # 设备导入路由
    url(r'^web/import/$', ExcelViewSet.upload_device),
    url(r'web/download_template', ExcelViewSet.download_template),
    # 巡检任务相关路由
    url(r'^web/jobs/$', JobViewSet.as_view()),
    # 巡检任务-设备采集进度相关路由
    url(r'^web/jobs/(?P<pk>\d+)/progress$', JobViewSet.progress),
    # 策略列表路由
    url(r'^web/policylist$', PolicyListViewSet.as_view()),
    url(r'^web/policy/add$', PolicyWriteViewSet.as_view()),
    url(r'^web/policy/get/(?P<pk>\d+)$', PolicyReadViewSet.as_view()),
    url(r'^web/policy/update_del/(?P<pk>\d+)$', PolicyWrite2ViewSet.as_view()),

    # 策略任务采集结果
    url(r'^web/policyJob/$', PolicyJobViewSet.as_view()),
    path('web/policyJob/download/<int:id>/', PolicyJobViewSet.download),

    # 数据库初始化路由
    path('web/init/database', InitDatabase.as_view()),
    path('web/setting/database', SettingsDatabase.as_view())
]

