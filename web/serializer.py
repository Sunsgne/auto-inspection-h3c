import django_filters
from rest_framework import serializers

from web.models import *


class DevicesSerializer(serializers.ModelSerializer):
    # 这个方法相当于覆盖掉
    import_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = Devices
        fields = '__all__'


# 这个相当于过滤器
class DevicesFilter(django_filters.FilterSet):
    # icontains表示模糊查询（包含），并且忽略大小写
    # iexact表示精确匹配, 并且忽略大小写`
    # exact表示精确匹配
    id = django_filters.NumberFilter(lookup_expr='exact')
    # device_name = django_filters.CharFilter(lookup_expr='icontains')
    device_category = django_filters.CharFilter(lookup_expr='icontains')
    # device_name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Devices
        fields = ['id',  'device_category']


# 设备序列化
class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        # 模型也就是指定表
        model = Devices
        # 查看采集策略列表时,返回ip,用户名密码,策略类别即可,无需传输其余字段
        fields = ['device_ip', 'user_name', 'user_psw', 'id']


# 策略列表序列化
class PolicyListSerializer(serializers.ModelSerializer):
    class Meta:
        # 模型也就是指定表
        model = Policies
        # 查看采集策略列表时,返回id,策略名称,是否为预置策略,策略类别即可,无需传输其余字段
        fields = ['id', 'policy_name', 'custom', 'policy_category']


# 策略反序列化
class PolicyWriteSerializer(serializers.ModelSerializer):
    class Meta:
        # 通过extra_kwargs,设置采集策略中的指令为非必填字段
        extra_kwargs = {'commands': {'required': False, 'allow_empty': True}}
        # extra_kwargs = {'commands': {'required': False, 'write_only': True}}
        model = Policies
        fields = '__all__'


# 策略序列化器
class PolicyReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Policies
        # 通过depth = 1,将采集策略中的关联指令id转化为指令对象详细信息
        # depth为只读模式,只适合序列化,不适合反序列化
        depth = 1
        fields = '__all__'


class CommandsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commands
        fields = '__all__'


class SettingsSerializer(serializers.ModelSerializer):
    update_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = Settings
        fields = '__all__'


class SettingsFilter(django_filters.FilterSet):
    id = django_filters.NumberFilter(lookup_expr='exact')
    setting_name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Settings
        fields = ['id', 'setting_name']


class JobsSerializer(serializers.ModelSerializer):
    start_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    end_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = Jobs
        fields = '__all__'
        depth = 1

    def create(self, validated_data, dev_id):
        device_obj = Devices.objects.get(id=dev_id)
        return Jobs.objects.create(device=device_obj, **validated_data)


class PolicyJobSerializer(serializers.ModelSerializer):
    # 这个方法相当于覆盖掉
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    update_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = PolicyJob
        fields = '__all__'


# 这个相当于过滤器
class PolicyJobFilter(django_filters.FilterSet):
    # icontains表示模糊查询（包含），并且忽略大小写
    # iexact表示精确匹配, 并且忽略大小写`
    # exact表示精确匹配
    device_category = django_filters.CharFilter(lookup_expr='iexact')

    class Meta:
        model = PolicyJob
        fields = ['device_category']
