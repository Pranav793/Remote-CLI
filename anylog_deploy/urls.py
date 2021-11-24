from django.urls import path
import anylog_deploy.views as views
import anylog_deploy.long_form as long_form
view_options = views.FormViews()

urlpatterns = [
    path('', view_options.file_config, name='index'),
    path('deploy-anylog/', view_options.deploy_anylog, name='deploy-anylog'),
    path('base-configs/', view_options.basic_config, name='base-configs'),
    path('general-configs/', view_options.general_info, name='general-configs'),
    path('network-configs/', view_options.networking_info, name='network-configs'),
    path('db-configs/', view_options.db_info, name='db-configs'),
    path('empty-node-configs/', view_options.empty_node_info, name='empty-node-configs'),
    path('operator-configs/', view_options.operator_info, name='operator-configs'),
    path('mqtt-configs/', view_options.mqtt_info, name='mqtt-configs'),
    path('full-form/', long_form.full_view, name='full-form'),
]