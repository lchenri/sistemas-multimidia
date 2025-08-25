from django.urls import include
from django.urls import path, re_path
from . import views
app_name = 'server'
urlpatterns = [
    path('', views.index, name='index.html'),
]