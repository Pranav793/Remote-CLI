from django.urls import path
import anylog_deploy.views as views

view_options = views.FormViews()

urlpatterns = [
    # path('', view_options.file_config, name='index'),
    path('base-config/', view_options.basic_config, name='base-config'),
    path('general-config/', view_options.general_info, name='general-config'),
    path('db-configs/', view_options.db_configs, name='db-configs'),
    path('db-operator-configs/', view_options.operator_configs, name='db-operator-configs'),
    path('full/', views.index, name='full-info'),
]