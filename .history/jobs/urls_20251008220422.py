from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('job/<init:job_id>/',views.job_detail, name='job_detail'),
]
