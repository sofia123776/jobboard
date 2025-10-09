from django.apps import AppConfig
from django.contrib import admin
from .models import Job, Application


class JobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobs'

admin.site.register(Job)
admin.site.register(Application)
