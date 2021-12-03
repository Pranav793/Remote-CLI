import os
import re
import time

import anylog_deploy.forms as forms
from django.http.response import HttpResponse
from django.shortcuts import render
from django.http import HttpResponseRedirect
import anylog_api.io_config as io_config
import anylog_api.docker_process as docker_process
CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'configs')


class FormViews:
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
            - preset_config_file:str - config file to use for deployment
                from config/ directory
            OR
            - external_config_file:str - config file to use for deployment
                    if unable to locate file, returns error
            OR
            - There's a button to setup a new configuration file
        :args:
            request:django.core.handlers.wsgi.WSGIRequest - type of request against the form
        :redirect:
            if not config_file == '' -- stay
            if config_file == new-file -- goto start asking config question s
            if config_file != new-file and config_file != '' -- deploy based on config
        """
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
        if request.method == 'POST':
            full_path = None
            file_config = forms.SelectConfig(request.POST)
            if file_config.is_valid():
                preset_config_file = request.POST.get('preset_config_file')
                external_config_file = request.POST.get('external_config_file')
                if preset_config_file == external_config_file == '':
                    file_config = forms.SelectConfig()
                    return render(request, "config_file.html", {'form': file_config})
                elif preset_config_file != '':
                    full_path = os.path.expandvars(os.path.expanduser(preset_config_file))
                elif external_config_file != '':
                    full_path = os.path.expanduser(os.path.expanduser(external_config_file))
                    if not os.path.isfile(full_path):
                        return render(request, "config_file.html",
                                      {'form': file_config, 'node_reply': 'Failed to locate file "%s"' % full_path})
                self.config_file = full_path
                return HttpResponseRedirect('deploy-anylog/')
        else:
            file_config = forms.SelectConfig()
            return render(request, "config_file.html", {'form': file_config})

    def deploy_anylog(self, request)->HttpResponse:
        """
        Deployment process for AnyLog
            1. check if self.env_params is empty - if not create config_file (and set to self.config_file)
            2. use self.config_file to exteact env_params
            if request.method == POST
                1. extract values
                2. go into docker deployment process
        """
        # Write env params to file or
        status = True
        messages = []
        docker_password = None
        update_anylog = False
        psql = False
        grafana = False
        deployment_configs = forms.DeployAnyLog()
         
        # Create config file if DNE (ie new deployment)
        if self.config_file is None:
            self.config_file = os.path.join(CONFIG_FILE_PATH, '%s.ini' % self.env_params['general']['node_name'])
            print(self.env_params)
            message = io_config.write_configs(config_data=self.env_params, config_file=self.config_file)
            if message is not None:
                messages.append(message)
                print(messages)

        # Read config file and set to env_params
        if os.path.isfile(self.config_file):
            env_params = io_config.read_configs(config_file=self.config_file)
        else:
            messages.append('Failed to location %s' % self.config_file)

        if env_params == {}: 
            env_params = self.env_params

        if 'NODE_TYPE' not in env_params:
            messages.append('Missing NODE_TYPE in configurations')
        elif env_params['NODE_TYPE'] not in ['none', 'rest', 'master', 'operator', 'publisher', 'query', 'single-node']:
            messages.append('Invalid node type: %s' % env_params['NODE_TYPE'])
        
        # Extract info from POST
        if request.method == 'POST' and messages == []:
            deployment_configs = forms.DeployAnyLog(request.POST)
            if deployment_configs.is_valid():
                docker_password = request.POST.get('password')
                if request.POST.get('update_anylog') is not None:
                    update_anylog = True
                if request.POST.get('psql') is not None:
                    if 'DB_USER' not in env_params:
                        messages.append("No database credentials, setting credentials to 'anylog@127.0.0.1:demo'")
                    psql = True
                if request.POST.get('grafana'):
                    grafana = True

            status = True 
            if psql is True:
                status, errors = docker_process.deploy_postgres(config_file=self.config_file, timezone='utc')
                if errors is not []:
                    for error in errors:
                        messages.append(error)
                time.sleep(15)

            if grafana is True:
                errors = docker_process.deploy_grafana()
                if errors is not []:
                    for error in errors:
                        messages.append(error)

            if status is True:
                status, errors = docker_process.deploy_anylog(config_file=self.config_file, docker_password=docker_password,
                                                              timezone='utc', update_anylog=update_anylog)
                if errors is not []:
                    for error in errors:
                        messages.append(error)

        return render(request, 'deploy_anylog.html', {'form': deployment_configs, 'node_reply': messages})
        # if messages != []:
        #     return render(request, 'deploy_anylog.html', {'form': deployment_configs, 'node_reply': messages})
        # else:
        #     return render(request, 'deploy_anylog.html', {'form': deployment_configs})

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
                if self.env_params['general']['node_type'] == 'none':
                    # THe reason we go to db-configs is because a user may want to deploy
                    return HttpResponseRedirect('../empty-node-configs/')
                else:
                    return HttpResponseRedirect('../general-configs/')
        else:
            base_configs = forms.BaseInfo()
            return render(request, "base_configs.html", {'form': base_configs})

    def empty_node_info(self, request)->HttpResponse:
        """
        Basic configuration for an empty node
            - db_type
            - db credentials (db_user)
            - db_port
            - node_name (used for docker container name)
        :args:
            request:django.core.handlers.wsgi.WSGIRequest - type of request against the form
        :redirect:
            if node_type == publisher goto mqtt-configs/
            else goto "root" to select config file
        """
        env_params = self.env_params
        if request.method == 'POST':
            db_configs = forms.NoneConfigs(request.POST)
            if db_configs.is_valid():
                self.env_params['general']['node_name'] = request.POST.get('node_name')
                self.env_params['database']['db_type'] = request.POST.get('db_type')
                db_conn_info = {'db_user': '', 'db_addr': '', 'db_pass': ''}
                for option in list(db_conn_info.keys()):
                    if request.POST.get(option) != '':
                        db_conn_info[option] = request.POST.get(option)
                if all(db_conn_info[key] != '' for key in list(db_conn_info.keys())):
                    self.env_params['database']['db_user'] = '%s@%s:%s' % (db_conn_info['db_user'],
                                                                           db_conn_info['db_addr'],
                                                                           db_conn_info['db_pass'])
                self.env_params['database']['db_port'] = request.POST.get('db_port')
                self.__update_params(env_params)
                self.config_file = os.path.join(CONFIG_FILE_PATH, '%s.ini' % self.env_params['general']['node_name'])
                message = io_config.write_configs(config_data=self.env_params, config_file=self.config_file)
                return HttpResponseRedirect('../deploy-anylog/')
        else:
            db_configs = forms.NoneConfigs()
            return render(request, "empty_node_configs.html", {'form': db_configs})

    def general_info(self, request)->HttpResponse:
        """
        General configuration
            - node name
            - company
            - location (optional)
            - enable authentication
                - username
                - password
                - user type
        :args:
            request:django.core.handlers.wsgi.WSGIRequest - type of request against the form
        :redirect:
            if node_type == operator goto db-operator-configs/
            if node_type != operator goto
        """
        env_params = self.env_params
        if request.method == 'POST':
            general_config = forms.GeneralInfo(request.POST)
            if general_config.is_valid():
                self.env_params['general']['node_name'] = request.POST.get('node_name')
                self.env_params['general']['company_name'] = request.POST.get('company_name')
                if request.POST.get('location') != '':
                    self.env_params['general']['location'] = request.POST.get('location')

                self.env_params['authentication']['authentication'] = 'false'
                if request.POST.get('authentication') is not None:
                    self.env_params['authentication']['authentication'] = 'true'

                self.env_params['authentication']['username'] = request.POST.get('username')
                if self.env_params['authentication']['authentication'] == 'true' and self.env_params['authentication']['username'] == '':
                    self.env_params['authentication']['username'] = 'anylog'

                self.env_params['authentication']['password'] = request.POST.get('password')
                if self.env_params['authentication']['authentication'] == 'true' and self.env_params['authentication']['password'] == '':
                    self.env_params['authentication']['password'] = 'demo'

                self.env_params['authentication']['auth_type'] = request.POST.get('auth_type')

                self.__update_params(env_params)
                return HttpResponseRedirect('../network-configs/')
        else:
            general_config = forms.GeneralInfo()
            return render(request, "general_configs.html", {'form': general_config})

    def networking_info(self, request)->HttpResponse:
        """
        Network related configurations
            - External & Local IP(s)
            - Ports (TCP, REST and Broker)
            - master_node
        """
        env_params = self.env_params
        if request.method == 'POST':
            networking_config = forms.NetworkingConfigs(request.POST)
            if networking_config.is_valid():
                self.env_params['networking']['ip'] = request.POST.get('external_ip')
                self.env_params['networking']['local_ip'] = request.POST.get('local_ip')
                anylog_tcp_port = request.POST.get('anylog_tcp_port')
                anylog_rest_port = request.POST.get('anylog_rest_port')
                anylog_broker_port = request.POST.get('anylog_broker_port')
                master_node = request.POST.get('master_node')

                # validate Master node info & no duplicate ports
                error_msg = ''
                if not bool(re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:[2-9][0-9][4-9][0-9]$', master_node)):
                    error_msg += 'Invalid format for master node (Format: IP:PORT)<br/>'
                if anylog_tcp_port == anylog_rest_port or anylog_tcp_port ==  anylog_broker_port or anylog_rest_port == anylog_broker_port:
                    error_msg += 'No two ports can have the same value'
                if error_msg != '':
                    return render(request, "network_configs.html", {'form': networking_config, 'node_reply': error_msg})

                self.env_params['networking']['master_node'] = master_node
                self.env_params['networking']['anylog_tcp_port'] = anylog_tcp_port
                self.env_params['networking']['anylog_rest_port'] = anylog_rest_port
                if anylog_broker_port != '': 
                    self.env_params['networking']['anylog_broker_port'] = anylog_broker_port

                self.__update_params(env_params)
                if self.env_params['general']['node_type'] in ['operator', 'single-node', 'rest']:
                    return HttpResponseRedirect('../operator-configs/')
                else:
                    return HttpResponseRedirect('../db-configs/')
        else:
            networking_config = forms.NetworkingConfigs()
            return render(request, "network_configs.html", {'form': networking_config})

    def db_info(self, request)->HttpResponse:
        """
        Configuration for non-Operator node -- only database information
            - db_type
            - db credentials (db_user)
            - db_port
        :args:
            request:django.core.handlers.wsgi.WSGIRequest - type of request against the form
        :redirect:
            if node_type == publisher goto mqtt-configs/
            else goto "root" to select config file
        """
        env_params = self.env_params
        if request.method == 'POST':
            db_configs = forms.DBConfigs(request.POST)
            if db_configs.is_valid():
                self.env_params['database']['db_type'] = request.POST.get('db_type')
                db_user = request.POST.get('db_user')
                db_addr = request.POST.get('db_addr')
                db_pass = request.POST.get('db_pass')
                self.env_params['database']['db_user'] = '%s@%s:%s' % (db_user.lower(), db_addr, db_pass)
                self.env_params['database']['db_port'] = request.POST.get('db_port')

                self.__update_params(env_params)

                # if self.env_params['general']['node_type'] == 'publisher':
                #     return HttpResponseRedirect('../mqtt-configs/')
                return HttpResponseRedirect('../deploy-anylog/')
        else:
            db_configs = forms.DBConfigs()
            return render(request, "db_configs.html", {'form': db_configs})

    def operator_info(self, request)->HttpResponse:
        """
        Configuration for Operator / single-node and database
            - db_type
            - db credentials (db_user)
            - db_port
            -
        :args:
            request:django.core.handlers.wsgi.WSGIRequest - type of request against the form
        :redirect:
            goto mqtt
        """
        env_params = self.env_params
        if request.method == 'POST':
            error_msg = ''
            db_configs = forms.DBOperatorConfigs(request.POST)
            if db_configs.is_valid():
                self.env_params['database']['db_type'] = request.POST.get('db_type')
                db_user = request.POST.get('db_user')
                db_addr = request.POST.get('db_addr')
                db_pass = request.POST.get('db_pass')
                self.env_params['database']['db_user'] = '%s@%s:%s' % (db_user, db_addr, db_pass)
                self.env_params['database']['db_port'] = request.POST.get('db_port')
                self.env_params['cluster']['enable_cluster'] = False
                if request.POST.get('enable_cluster') is not None:
                    self.env_params['cluster']['enable_cluster'] = True

                self.env_params['cluster']['cluster_name'] = request.POST.get('cluster_name')

                if self.env_params['cluster']['enable_cluster'] is True and self.env_params['cluster']['cluster_name'] == '':
                    error_msg += 'Missing cluster name<br/>'

                self.env_params['partition']['enable_partition'] = False
                try:
                    if self.POST.get('enable_partition') is not None:
                        self.env_params['partition']['enable_partition'] = True
                except AttributeError:
                    pass

                self.env_params['partition']['partition_column'] = request.POST.get('partition_column')
                self.env_params['partition']['partition_interval'] = request.POST.get('partition_interval')

                if self.env_params['partition']['enable_partition']  is True:
                    if self.env_params['partition']['partition_column'] == '':
                        error_msg += "Missing partition column<br/>"
                    if self.env_params['partition']['partition_interval'] == '':
                        error_msg += "Missing partitioning interval<br/>"

                self.__update_params(env_params)
                if error_msg != '':
                    return render(request, "operator_configs.html", {'form': db_configs, 'node_reply': error_msg})
                # return HttpResponseRedirect('../mqtt-configs/')
                return HttpResponseRedirect('../deploy-anylog/')
            else:
                return render(request, "operator_configs.html", {'form': db_configs})
        else:
            db_configs = forms.DBOperatorConfigs()
            return render(request, "operator_configs.html", {'form': db_configs})

    def mqtt_info(self, request)->HttpResponse:
        env_params = self.env_params
        if request.method == 'POST':
            error_msg = ''
            mqtt_configs = forms.MqttConfigs(request.POST)
            if mqtt_configs.is_valid():
                self.env_params['mqtt']['mqtt_enable'] = False
                if request.POST.get('mqtt_enable') is not None:
                    self.env_params['mqtt']['mqtt_enable'] = True

                mqtt_broker = request.POST.get('mqtt_broker')
                if self.env_params['mqtt']['mqtt_enable'] is True and mqtt_broker == '':
                    error_msg += 'Missing broker information<br/>'
                mqtt_user = request.POST.get('mqtt_user')
                if mqtt_user != '':
                    mqtt_broker = '%s@%s' % (mqtt_user, mqtt_broker)
                mqtt_pass = request.POST.get('mqtt_pass')
                if mqtt_pass != '':
                    mqtt_broker = '%s:%s' % (mqtt_broker, mqtt_pass)
                self.env_params['mqtt']['mqtt_conn_info'] = mqtt_broker

                self.env_params['mqtt']['mqtt_port'] = request.POST.get('mqtt_port')
                if self.env_params['mqtt']['mqtt_enable'] is True and self.env_params['mqtt']['mqtt_port'] == '':
                    error_msg += 'Missing broker port information<br/>'

                self.env_params['mqtt']['mqtt_topic_name'] = request.POST.get('mqtt_topic_name')
                if self.env_params['mqtt']['mqtt_enable'] is True and self.env_params['mqtt']['mqtt_topic_name'] == '':
                    error_msg += "Missing topic name - user can set topic to '*' to get all topics from broker<br/>"

                self.env_params['mqtt']['mqtt_topic_dbms'] = request.POST.get('mqtt_topic_dbms')
                self.env_params['mqtt']['mqtt_topic_table'] = request.POST.get('mqtt_topic_table')
                self.env_params['mqtt']['mqtt_column_timestamp'] = request.POST.get('mqtt_column_timestamp')
                self.env_params['mqtt']['mqtt_column_value_type'] = request.POST.get('mqtt_column_value_type')
                self.env_params['mqtt']['mqtt_column_value'] = request.POST.get('mqtt_column_value')

                self.__update_params(env_params)
                if error_msg != '':
                    return render(request, "mqtt_configs.html", {'form': mqtt_configs, 'node_reply': error_msg})

                return HttpResponseRedirect('../deploy-anylog/')
        else:
            mqtt_configs = forms.MqttConfigs()
            return render(request, "mqtt_configs.html", {'form': mqtt_configs})

