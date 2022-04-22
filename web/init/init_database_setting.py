from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import GenericAPIView

from web.golobal import APIResponse
from web.models import Settings
from web.serializer import SettingsSerializer


class SettingsDatabase(GenericAPIView):
    serializer_class = SettingsSerializer
    filter_backends = [DjangoFilterBackend]

    @staticmethod
    def get(request):
        try:
            Settings.objects.get(id=1)
        except Settings.DoesNotExist:
            Settings.objects.create(id=1, setting_name="采集信息保存路径", setting_val="/app/dzkfcollector/logs")
        try:
            Settings.objects.get(id=2)
        except Settings.DoesNotExist:
            Settings.objects.create(id=2, setting_name="服务器错误日志路径", setting_val="/error")
        return APIResponse(0, 'init Success!')
