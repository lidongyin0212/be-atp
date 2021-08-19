# -*- coding: UTF-8 -*-

from django.contrib import admin
from django.urls import path
from django.conf.urls import url
from InterfaceTestManage import views

urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^login$', views.login),
    url(r'^register$', views.register),
    # url(r'^index$', views.getIndex),
    # url(r'^$', views.getIndex),
    # url(r'^welcome$', views.welcome),
]
