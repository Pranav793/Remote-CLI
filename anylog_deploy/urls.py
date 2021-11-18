from django.urls import path
import anylog_deploy.views as views

fv = views.FormViews()

urlpatterns = [
    path('', fv.basic_config, name='index'),
    path('general-config/', fv.general_info, name='general-config'),
    path('full/', views.index, name='full-info'),
]