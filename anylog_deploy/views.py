import os
import anylog_deploy.forms as forms
from django.http.response import HttpResponse
from django.shortcuts import render
from django.http import HttpResponseRedirect
import anylog_deploy.anylog_conn.io_config as io_config

class FormViews:
    def __init__(self):
        self.env_params = {
            'general': {},
            'authentication': {},
            'networking': {},
            'database': {},
            'cluster': {},
            'partition': {},
            'mqtt': {},

        }
        self.config_file = None

    def __update_params(self, env_params:dict):
        """
        Update env params
        :args:
            env_params:dict - env params
        """
        for key in env_params:
            for ky in env_params[key]:
                if ky not in self.env_params[key]:
                    self.env_params[key][ky] = env_params[key][ky]

    def file_config(self, request)->HttpResponse:
        """
        Select file to be or to configure a new file
            - config_file:str - config file to use for deployment
        :args:
            request:django.core.handlers.wsgi.WSGIRequest - type of request against the form
        :redirect:
            if not config_file == '' -- stay
            if config_file == new-file -- goto start asking config question s
            if config_file != new-file and config_file != '' -- deploy based on config
        """
        if request.method == 'POST':
            full_path = None
            file_config = forms.SelectConfig(request.POST)
            print(file_config.is_valid())
            if file_config.is_valid():
                # ask for information regarding a new device
                if request.POST.get('new_config_file') is not None:
                    return HttpResponseRedirect('base-configs/')

                preset_config_file = request.POST.get('preset_config_file')
                external_config_file = request.POST.get('external_config_file')

                # extract configuration file (full path)
                if preset_config_file is not '':
                    full_path = os.path.expandvars(os.path.expanduser(preset_config_file))
                elif external_config_file != '':
                    full_path = os.path.expanduser(os.path.expanduser(external_config_file))
                    if not os.path.isfile(full_path):
                        return render(request, "config_file.html", {'form': file_config,
                                                                    'error': 'Failed to locate file "%s"' % full_path})
                # get env params from file
                if full_path is not None:
                    self.env_params = io_config.read_configs(config_file=full_path)
                    if 'Error' in self.env_params:
                        return render(request, "config_file.html", {'form': file_config, 'error': self.env_params})
                    else:
                        return HttpResponseRedirect('deploy-anylog/')
                else:
                    return render(request, "config_file.html", {'form': file_config})
        else:
            file_config = forms.SelectConfig()
            return render(request, "config_file.html", {'form': file_config})

    def deploy_anylog(self, request)->HttpResponse:
        if request.method == 'POST':
            return HttpResponse('Hello World')
        else:
            deployment_config = forms.DeployAnyLog()
            return render(request, "deploy_anylog.html", {'form': deployment_config})

    def basic_config(self, request)->HttpResponse:
        """
        Basic configurations
            - build
            - node type
            - docker password
        :args:
            request:django.core.handlers.wsgi.WSGIRequest - type of request against the form
        :redirect:
            if node_type == none goto list of configs
            if node_type != none goto general-config/
        """
        if request.method == 'POST':
            base_configs = forms.BaseInfo(request.POST)
            if base_configs.is_valid():
                self.env_params['general']['build'] = request.POST.get('build')
                self.env_params['general']['node_type'] = request.POST.get('node_type')
                if self.env_params['general']['node_type'] == 'none' or self.env_params['general']['node_type'] == '':
                    # Deploy AnyLog of type None
                    return render(request, "base_configs.html", {'form': base_configs})
                else:
                    return HttpResponseRedirect('../general-configs/')
        else:
            base_configs = forms.BaseInfo()
            return render(request, "base_configs.html", {'form': base_configs})

    # def general_info(self, request)->HttpResponse:
    #     """
    #     General configuration
    #         - node name
    #         - company
    #         - disable location
    #             if set to False:
    #             - location (optional)
    #         - enable authentication
    #             - username
    #             - password
    #             - user type
    #     :args:
    #         request:django.core.handlers.wsgi.WSGIRequest - type of request against the form
    #     :redirect:
    #         if node_type == operator goto db-operator-configs/
    #         if node_type != operator goto
    #     """
    #     env_params = self.env_params
    #     if request.method == 'POST':
    #         general_config = forms.GeneralInfo(request.POST)
    #         if general_config.is_valid():
    #             self.env_params['general']['node_name'] = request.POST.get('node_name')
    #             self.env_params['general']['comapny_name'] = request.POST.get('company_name')
    #
    #             try:
    #                 authentication = request.POST.get('authentication')
    #             except:
    #                 authentication = None
    #             if authentication is None:
    #                 self.env_params['authentication']['authentication'] = 'off'
    #             else:
    #                 self.env_params['authentication']['authentication'] = 'on'
    #
    #             self.env_params['authentication']['username'] = request.POST.get('username')
    #             self.env_params['authentication']['password'] = request.POST.get('password')
    #             self.env_params['authentication']['auth_type'] = request.POST.get('auth_type')
    #
    #             self.__update_params(env_params)
    #             print(self.env_params)
    #             return HttpResponseRedirect('../network-configs/')
    #     else:
    #         general_config = forms.GeneralInfo()
    #         return render(request, "general_configs.html", {'form': general_config})
    #
    # def networking_info(self, request)->HttpResponse:
    #     """
    #     Network related configurations
    #         - External & Local IP(s)
    #         - Ports (TCP, REST and Broker)
    #         - master_node
    #     """
    #     env_params = self.env_params
    #     if request.get == 'POST':
    #         networking_config = forms.NetworkingConfigs(request.POST)
    #         if networking_config.is_valid():
    #             self.env_params['networking']['ip'] = request.POST.get('external_ip')
    #             self.env_params['networking']['local_ip'] = request.POST.get('local_ip')
    #             self.env_params['networking']['anylog_tcp_port'] = request.POST.get('anylog_tcp_port')
    #             self.env_params['networking']['anylog_rest_port'] = request.POST.get('anylog_rest_port')
    #             self.env_params['networking']['anylog_broker_port'] = request.POST.get('anylog_broker_port')
    #             self.env_params['networking']['master_node'] = request.POST.get('master_node')
    #
    #             self.__update_params(env_params)
    #             if self.env_params['general']['node_type'] in ['operator', 'single-node']:
    #                 return HttpResponseRedirect('../operator-configs/')
    #             else:
    #                 return HttpResponseRedirect('../db-configs/')
    #     else:
    #         networking_config = forms.NetworkingConfigs()
    #         return render(request, "network_configs.html", {'form': networking_config})
    #
    # def db_info(self, request)->HttpResponse:
    #     """
    #     Configuration for non-Operator node -- only database information
    #         - db_type
    #         - db credentials (db_user)
    #         - db_port
    #     :args:
    #         request:django.core.handlers.wsgi.WSGIRequest - type of request against the form
    #     :redirect:
    #         if node_type == publisher goto mqtt-configs/
    #         else goto "root" to select config file
    #     """
    #     env_params = self.env_params
    #     if request.method == 'POST':
    #         db_configs = forms.DBConfigs(request.POST)
    #         if db_configs.is_valid():
    #             self.env_params['database']['db_type'] = request.POST.get('db_type')
    #             db_user = request.POST.get('db_user')
    #             db_addr = request.POST.get('db_addr')
    #             db_pass = request.POST.get('db_pass')
    #             self.env_params['database']['db_user'] = '%s@%s:%s' % (db_user, db_addr, db_pass)
    #             self.env_params['database']['db_port'] = request.POST.get('db_port')
    #
    #             self.__update_params(env_params)
    #             if self.env_params['general']['node_type'] == 'publisher':
    #                 return HttpResponseRedirect('../mqtt-configs/')
    #             return render(request, "db_configs.html", {'form': db_configs})
    #     else:
    #         db_configs = forms.DBConfigs()
    #         return render(request, "db_configs.html", {'form': db_configs})
    #
    # def operator_info(self, request)->HttpResponse:
    #     """
    #     Configuration for Operator / single-node and database
    #         - db_type
    #         - db credentials (db_user)
    #         - db_port
    #         -
    #     :args:
    #         request:django.core.handlers.wsgi.WSGIRequest - type of request against the form
    #     :redirect:
    #         goto mqtt
    #     """
    #     env_params = self.env_params
    #     if request.method == 'POST':
    #         db_configs = forms.DBOperatorConfigs(request.POST)
    #         if db_configs.is_valid():
    #             self.env_params['database']['db_type'] = request.POST.get('db_type')
    #             db_user = request.POST.get('db_user')
    #             db_addr = request.POST.get('db_addr')
    #             db_pass = request.POST.get('db_pass')
    #             self.env_params['database']['db_user'] = '%s@%s:%s' % (db_user, db_addr, db_pass)
    #             self.env_params['database']['db_port'] = request.POST.get('db_port')
    #             try:
    #                 self.env_params['cluster']['enable_cluster'] = request.POST.get('enable_cluster')
    #             except:
    #                 self.env_params['cluster']['enable_cluster'] = False
    #             else:
    #                 if self.env_params['cluster']['enable_cluster'] == 'on':
    #                     self.env_params['cluster']['enable_cluster'] = True
    #                 else:
    #                     self.env_params['cluster']['enable_cluster'] = False
    #
    #             self.env_params['cluster']['cluster_name'] = request.POST.get('cluster_name')
    #
    #             try:
    #                 self.env_params['partition']['enable_partition'] = self.POST.get('enable_partition')
    #             except:
    #                 self.env_params['partition']['enable_partition'] = False
    #             else:
    #                 if self.env_params['partition']['enable_partition'] == 'on':
    #                     self.env_params['partition']['enable_partition'] = True
    #
    #             self.env_params['partition']['partition_column'] = request.POST.get('partition_column')
    #             self.env_params['partition']['partition_interval'] = request.POST.get('partition_interval')
    #
    #             self.__update_params(env_params)
    #             return HttpResponseRedirect('../mqtt-configs/')
    #         else:
    #             return render(request, "operator_configs.html", {'form': db_configs})
    #     else:
    #         db_configs = forms.DBOperatorConfigs()
    #         return render(request, "operator_configs.html", {'form': db_configs})
    #
    # def mqtt_info(self, request)->HttpResponse:
    #     env_params = self.env_params
    #     if request.method == 'POST':
    #         mqtt_configs = forms.MqttConfigs(request.POST)
    #         if mqtt_configs.is_valid():
    #             try:
    #                 self.env_params['mqtt']['mqtt_enable'] = request.POST.get('mqtt_enable')
    #             except:
    #                 self.env_params['mqtt']['mqtt_enable'] = False
    #             else:
    #                 if self.env_params['mqtt']['mqtt_enable'] == 'on':
    #                     self.env_params['mqtt']['mqtt_enable'] = True
    #                 else:
    #                     self.env_params['mqtt']['mqtt_enable'] = False
    #
    #             mqtt_broker = request.POST.get('mqtt_broker')
    #             mqtt_user = request.POST.get('mqtt_user')
    #             if mqtt_user != '':
    #                 mqtt_broker = '%s@%s' % (mqtt_user, mqtt_broker)
    #             mqtt_pass = request.POST.get('mqtt_pass')
    #             if mqtt_pass != '':
    #                 mqtt_broker = '%s:%s' % (mqtt_broker, mqtt_pass)
    #             self.env_params['mqtt']['mqtt_conn_info'] = mqtt_broker
    #
    #             self.env_params['mqtt']['mqtt_port'] = request.POST.get('mqtt_port')
    #             self.env_params['mqtt']['mqtt_topic_name'] = request.POST.get('mqtt_topic_name')
    #             self.env_params['mqtt']['mqtt_topic_dbms'] = request.POST.get('mqtt_topic_dbms')
    #             self.env_params['mqtt']['mqtt_topic_table'] = request.POST.get('mqtt_topic_table')
    #             self.env_params['mqtt']['mqtt_column_timestamp'] = request.POST.get('mqtt_column_timestamp')
    #             self.env_params['mqtt']['mqtt_column_value_type'] = request.POST.get('mqtt_column_value_type')
    #             self.env_params['mqtt']['mqtt_column_value'] = request.POST.get('mqtt_column_value')
    #             self.__update_params(env_params)
    #             print(self.env_params)
    #             return render(request, "mqtt_configs.html", {'form': mqtt_configs})
    #     else:
    #         mqtt_configs = forms.MqttConfigs()
    #         return render(request, "mqtt_configs.html", {'form': mqtt_configs})

