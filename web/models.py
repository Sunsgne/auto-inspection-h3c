from django.db import models


# 设备表
class Devices(models.Model):
    id = models.AutoField(primary_key=True)  # id 会自动创建,可以手动写入
    device_name = models.CharField(max_length=64, null=True)  # 设备名称
    device_ip = models.CharField(max_length=32, null=False)  # 设备IP
    device_category = models.CharField(max_length=64, null=True)  # 设备类别
    device_modal = models.CharField(max_length=64, null=True)  # 设备型号
    protocol = models.CharField(max_length=16, null=False, default='ssh')  # 设备联通协议
    user_name = models.CharField(max_length=64, null=True, blank=True)  # 设备连接用户名
    user_psw = models.CharField(max_length=64, null=True, blank=True)  # 设备连接密码
    ping_status = models.IntegerField(null=False, default=0)  # 设备Ping状态,0不通，1通
    ssh_status = models.IntegerField(null=False, default=0)  # 设备SSH连接状态，0不通，1通
    import_time = models.DateTimeField('导入时间', auto_now_add=True, null=True)  # 导入时间
    super_psw = models.CharField(max_length=64, null=True, blank=True)  # 设备超管密码

    class Meta:
        unique_together = ("device_name", "device_category")

    @classmethod
    def create(cls, device_name, device_ip, device_category, protocol, user_name, user_psw, super_psw):
        device = cls(device_name=device_name, device_ip=device_ip, device_category=device_category, protocol=protocol, user_name=user_name, user_psw=user_psw, super_psw=super_psw)
        device.ssh_status = 0
        device.ping_status = 0
        return device

    @classmethod
    def get_bulk_update_names(cls):
        name_list = ['device_name', 'device_ip', 'device_category', 'protocol', 'user_name', 'user_psw', 'import_time', 'super_psw']
        return name_list

    @classmethod
    def get_bulk_update_conn(cls):
        name_list = ['ping_status', 'ssh_status']
        return name_list


# 采集策略任务，是采集任务的父任务，
class PolicyJob(models.Model):
    id = models.AutoField(primary_key=True)  # id 会自动创建,可以手动写入
    collect_policy = models.IntegerField(null=False)  # 采集策略ID
    file_name = models.CharField(max_length=128, null=False)  # 数据包文件名
    file_path = models.CharField(max_length=1024, null=False)  # 数据包文件路径
    size = models.CharField(max_length=16, null=True)  # 大小KB
    device_category = models.CharField(max_length=30, null=True)  # 采集模块，device:网络设备信息采集，server:服务器日志采集,3par:3par信息采集
    create_time = models.DateTimeField('创建时间', auto_now_add=True)  # 创建时间
    update_time = models.DateTimeField('最后修改时间', auto_now=True)  # 最后修改时间


# 采集任务表
class Jobs(models.Model):
    id = models.AutoField(primary_key=True)  # id 会自动创建,可以手动写入
    job_type = models.CharField(max_length=32, null=True)  # 任务类别
    device = models.ForeignKey(Devices, related_name='device_job', on_delete=models.CASCADE, null=True)  # 设备ID
    policyJob = models.ForeignKey(PolicyJob, related_name='policyjob_job', on_delete=models.CASCADE, null=True)  # 策略采集任务id
    # collect_policy = models.IntegerField(null=False)  # 采集策略ID
    collect_progress = models.CharField(max_length=32, null=True)  # 指令执行进度，百分比
    status = models.IntegerField(null=False)  # 采集任务执行状态,0创建成功,1执行中,2已取消,3执行成功,4执行失败
    start_time = models.DateTimeField('任务开始时间', auto_now_add=True, null=True)  # 任务开始时间
    end_time = models.DateTimeField('任务结束时间', auto_now=True)  # 任务结束时间
    is_recent = models.IntegerField(null=True)  # 是否为该设备最新任务,0否,1是


# 系统设置表
class Settings(models.Model):
    id = models.AutoField(primary_key=True)  # id 会自动创建,可以手动写入
    setting_name = models.CharField(max_length=64, null=False)  # 设置项名称
    setting_val = models.CharField(max_length=64, null=True)  # 设置项值
    update_time = models.DateTimeField('任务结束时间', auto_now=True)  # 修改时间


# 采集策略表
class Policies(models.Model):
    id = models.AutoField(primary_key=True)  # id 会自动创建,可以手动写入
    policy_name = models.CharField(max_length=64, null=False)  # 采集策略名称
    custom = models.IntegerField(null=False, default=0)  # 是否为预置策略,0不是，1是
    commands = models.ManyToManyField(to='Commands')  # 多对多关联，ORM自动生成中间表
    create_time = models.DateTimeField('策略创建时间', auto_now_add=True, null=True)  # 策略创建时间
    update_time = models.DateTimeField('策略更新时间', auto_now=True)  # 策略更新时间
    policy_category = models.IntegerField(null=False, default=0)  # 策略类别,0-CT，1-服务器，2-3Par
    pull_diag = models.IntegerField(null=False, default=0)  # 是否需要拉取诊断采集文件,0否,1是
    pull_log = models.IntegerField(null=False, default=0)  # 是否需要拉取日志采集文件,0否,1是


# 采集指令表
class Commands(models.Model):
    id = models.AutoField(primary_key=True)  # id 会自动创建,可以手动写入
    protocol = models.CharField(max_length=16, null=False, default='ssh')  # 采集指令协议
    content = models.CharField(max_length=1024, null=True)  # 采集指令
    gather_time = models.CharField(max_length=16, null=True)  # 是否打印执行时间
    inview = models.CharField(max_length=64, null=True)  # 视图名称，逗号连接
    outview = models.CharField(max_length=64, null=True)  # 视图退出，逗号连接
    depend_script = models.CharField(max_length=256, null=True)  # 依赖脚本名称
    depend_script2 = models.CharField(max_length=256, null=True)  # 依赖脚本名称
    yes_no = models.CharField(max_length=16, null=True)  # 需要手动输入'Y'或'N'
    import_time = models.DateTimeField('命令导入时间', auto_now_add=True, null=True)  # 命令导入时间



