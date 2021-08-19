# coding:utf-8
"""InterfaceAutoTest URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import url, include
from django.views import static  ##新增
from django.conf import settings  ##新增
from django.conf.urls import url

from InterfaceAutoTest.activator import process, process_report
# from InterfaceTestManage import urls
from django.views.generic.base import RedirectView

urlpatterns = [
    url(r'^favicon.ico$', RedirectView.as_view(url=r'static/favicon.ico')),
    url('', include("InterfaceTestManage.urls")),
    url('', include("UITestManage.urls")),
    # url('', include("AppTestManage.urls")),
    url('^result/(?P<function>(\w+))/(?P<filename>(.*))/?$', process_report),
    url('^(?P<app>(\w+))/(?P<function>(\w+))/?$', process),
    url('^(?P<app>(\w+))/(?P<function>(\w+))/(?P<id>(\w+))/?$', process),
    url('^(?P<app>(\w+))/(?P<function>(\w+))/(?P<id>(\w+))/(?P<scoure>(\w+))/?$', process),
    url('^(?P<app>(\w+))/(?P<function>(\w+))/(?P<id>(\w+))/(?P<sub_index>(\w+))/(?P<scoure>(\w+))/?$', process),
    url(r'^static/(?P<path>.*)$', static.serve, {'document_root': settings.STATIC_ROOT}, name='static'),

]
