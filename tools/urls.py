from django.urls import path
from . import views

app_name = 'tools'

urlpatterns = [
    path('', views.index, name='index'), # 관리툴 첫화면
]