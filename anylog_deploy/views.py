import os
import re
import time

import anylog_deploy.forms as forms
from django.http.response import HttpResponse
from django.shortcuts import render
from django.http import HttpResponseRedirect
import anylog_api.io_config as io_config
import anylog_api.docker_deployment as docker_deployment
CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'configs')

NODE_TYPES = [
    'none',
    'rest',
    'master',
    'operator',
    'publisher',
    'query',
    'single-node',
    'single-node-publisher'
]


class DeploymentViews:
    def front_page(self, request)->HttpResponse:
        """
        Page offering to either use an existing config file or create config file & deploy configs
        :HTML file:
            deployment_front_page.html
        :args:
            request:django.core.handlers.wsgi.WSGIRequest - type of request against the form
        :params:
            config_params:forms.SelectConfig - call to correlated forms
            self.env_params:dict - environment params
            self.config_file:str  - configuration file
                preset_config_file:str - a config file selected from configs/
                external_config_file:str - manual input of config file
        :redriect:
            --> stay - if not is set
            --> deploy_anylog.html - if selecting an existing config file
            --> base_configs.html - if "Configure New Node" button
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
        preset_config_file = ''
        external_config_file = ''

        if request.method == 'POST':
            config_params = forms.SelectConfig(request.POST)
            if config_params.is_valid():
                preset_config_file = request.POST.get('preset_config_file') # config file in configs/
                external_config_file = request.POST.get('external_config_file') # manual input of config file
                external_config_file = os.path.expandvars(os.path.expanduser(external_config_file))

                if preset_config_file != '' and os.path.isfile(preset_config_file):
                    self.config_file = preset_config_file
                elif external_config_file != '' and os.path.isfile(external_config_file):
                    self.config_file = external_config_file
        if self.config_file is not None:
            return HttpResponseRedirect('deploy-anylog/')
        else:
            config_params = forms.SelectConfig()
            return render(request, "deployment_front_page.html", {'form': config_params})\

    def deploy_anylog(self, request)->HttpResponse:
        """
        Once user either selects a config file or completes config form(s) user select what to deploy & executes
        :HTML file:
            deploy_anylog.html
        :args:
            request:django.core.handlers.wsgi.WSGIRequest - type of request against the form
        :params:
            deploy_config:forms.DeployAnyLog - call to correlated forms
            status:bool - status
            messages:list - list of error messages
            update_anylog:bool - whether to update AnyLog (AnyLog gets deployed by default)
            psql:bool - whether to deploy Postgres
            grafana:bool - whether to deploy Grafana
        :redriect:
            --> stay w/ message
            --> deployment_front_page.html when pressing "Start Over" button
        """
        status = True
        messages = []
        base_configs = forms.BaseInfo()
        docker_password = None
        update_anylog = False
        psql = False
        grafana = False

        # Extract configuration information
        if self.config_file is None:
            try:
                self.config_file = os.path.join(CONFIG_FILE_PATH, '%s.ini' % self.env_params['general']['node_name'])
            except:
                return render(request, 'deploy_anylog.html',
                              {'form': base_configs,
                               'node_reply': 'Missing NODE_NAME in set parameters. Please start over'})
            else:
                messages = io_config.write_configs(config_data=self.env_params, config_file=self.config_file)
                if messages is not None:
                    return render(request, 'deploy_anylog.html', {'form': base_configs, 'node_reply': messages})


        if os.path.isfile(self.config_file): # extract values from config file
            env_params = io_config.read_configs(config_file=self.config_file)
            if not io_config.validate_config(env_params=env_params):
                return render(request, 'deploy_anylog.html',
                              {'form': base_configs, 'node_reply': 'Failed to validate one or more params'})

        # Extract values from forms
        if request.method == 'POST':
            deploy_config = forms.DeployAnyLog(request.POST)
            if deploy_config.is_valid():
                docker_password = request.POST.get('password')
                if request.POST.get('update_anylog') is not None:
                    update_anylog = True
                # Deploy Postgres is checked
                if request.POST.get('psql') is not None:
                    if 'DB_USER' not in env_params:
                        messages.append("Missing database credentials. Setting db_user to: 'anylog@127.0.0.1:demo'")
                        env_params['DB_USER'] = 'anylog@127.0.0.1:demo'
                    status, errors = docker_deployment.deploy_postgres_container(user_info=env_params['DB_USER'],
                                                                                 timezone='utc')
                    if status is False and len(errors) != 0:
                        for error in errors:
                            messages.append(error)
                    elif status is False:
                        messages.append('Failed to deploy Postgres container')
                    else:
                        time.sleep(15)
                # Deploy Grafana is checked
                if request.POST.get('grafana'):
                    errors = docker_deployment.deploy_grafana_container()
                    if errors is not []:
                        for error in errors:
                            messages.append(error)
                # Deploy AnyLog
                if status is True:
                    status, errors = docker_deployment.deploy_anylog_container(env_params=env_params, timezone='utc',
                                                                               docker_password=docker_password,
                                                                               update_anylog=update_anylog)
                    if errors is not []:
                        for error in errors:
                            messages.append(error)

        deploy_config = forms.DeployAnyLog()
        return render(request, 'deploy_anylog.html', {'form': deploy_config, 'node_reply': messages})

    def base_configs(self, request)->HttpResponse:
        """
        Build and node_tye setup
        :HTML file:
            base_configs.html
        :args:
            request:django.core.handlers.wsgi.WSGIRequest - type of request against the form
        :params:
            basic_config:forms.BasicInfo - call to correlated forms
        :redirect:
            - if NODE_TYPE == none: empty-node-configs
            - if NODE_TYPE != none and NODE_TYPE != '': general-configs
            - other: stay
        """
        if request.method == 'POST':
            basic_config = forms.BaseInfo(request.POST)
            if basic_config.is_valid():
                self.env_params['general']['build'] = request.POST.get('build')
                self.env_params['general']['node_type'] = request.POST.get('node_type')
                if self.env_params['general']['node_type'] == 'none':
                    return HttpResponseRedirect('../none-configs/')
                else:
                    return HttpResponseRedirect('../general-configs/')
        else:
            basic_config = forms.BaseInfo()
            return render(request, 'base_configs.html', {'form': basic_config})

    def none_configs(self, request)->HttpResponse:
        """
        Configuration options for an empty node
        :HTML file:
            empty_node_configs.html
        :args:
            request:django.core.handlers.wsgi.WSGIRequest - type of request against the form
        :params:
            db_info:dict - database connection information
                - username
                - address
                - password
            messages:list - list of error messages
            none_config:forms.NoneConfig - call to form questions related to node of type None
        :redirect:
            --> stays if missing NODE_NAME
            --> goes to deploy-anylog/ when at least NODE_NAME is set

        """
        db_info = {
            'db_user': None,
            'db_addr': None,
            'db_pass': None
        }
        none_config = forms.NoneConfigs()

        if request.method == 'POST':
            none_config = forms.NoneConfigs(request.POST)
            if none_config.is_valid():
                self.env_params['general']['node_name'] = request.POST.get('node_name')
                self.env_params['database']['db_type'] = request.POST.get('db_type')
                self.env_params['database']['db_port'] = request.POST.get('db_port')
                for param in db_info:
                    db_info[param] = request.POST.get(param)
                if all(db_info[param] != '' for param in db_info):
                    self.env_params['database']['db_user'] = '%s@%s:%s' % (db_info['db_user'], db_info['db_addr'],
                                                                           db_info['db_pass'])
                return HttpResponseRedirect('../deploy-anylog/')

        return render(request, 'empty_node_configs.html', {'form': none_config})






