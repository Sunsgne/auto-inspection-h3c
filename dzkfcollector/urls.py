
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import TemplateView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

openapi_info = openapi.Info(
    title="Linux采集器API文档",
    default_version='v1',
    description="Linux采集器API文档",
    contact=openapi.Contact(email="ych@h3c.com"),
)
schema_view = get_schema_view(
    openapi_info,
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # 所有通过api访问的url,交给应用路由处理
    path('api/', include('web.urls')),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('', TemplateView.as_view(template_name="index.html"))
]
