from django.contrib import admin
from .models import Job, Application, Company, UserProfile, JobAlert

# Register your models here.
admin.site.register(Job)
admin.site.register(Application)
admin.site.register(Company)
admin.site.register(UserProfile)
admin.site.register(JobAlert)
