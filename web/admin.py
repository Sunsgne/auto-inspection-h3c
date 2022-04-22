# 将mysql数据库放入admin管理界面
from django.contrib import admin
from web.models import Devices, Jobs, Policies, Settings, Commands


class AuthorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email')
    search_fields = ('first_name', 'last_name')


admin.site.register(Devices)
admin.site.register(Jobs)
admin.site.register(Policies)
admin.site.register(Settings)
admin.site.register(Commands)
