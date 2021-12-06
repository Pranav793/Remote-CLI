from django.urls import path
import anylog_deploy.views as views
import anylog_deploy.long_form as long_form
view_options = views.DeploymentViews()

urlpatterns = [
    path('', view_options.front_page, name='deployment-front'),
    path('deploy-anylog/', view_options.deploy_anylog, name='deploy-anylog'),
    path('basic-configs/', view_options.base_configs, name='basic-configs'),
    path('none-configs/', view_options.none_configs, name='none-configs'),
    path('general-configs/', view_options.general_configs, name='general-configs'),
    path('network-configs/', view_options.network_configs, name='network-configs'),
    path('generic-database-configs/', view_options.database_configs, name='generic-database-configs'),
    path('operator-database-configs/', view_options.operator_database_configs, name='operator-database-configs'),
    # path('mqtt-configs/', view_options.mqtt_configs, name='mqtt-configs/'),
    path('full-form/', long_form.full_view, name='full-form'),
]