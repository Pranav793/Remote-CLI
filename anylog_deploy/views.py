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
            self.env_params:dict - environment params
            self.config_file:str  - configuration file
                preset_config_file:str - a config file selected from configs/
                external_config_file:str - manual input of config file
            config_params:forms.SelectConfig - call to front page form
        :redirect:
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

                if preset_config_file != '':
                    self.config_file = preset_config_file
                elif external_config_file != '':
                    self.config_file = os.path.expandvars(os.path.expanduser(external_config_file))
                else:
                    config_params = forms.SelectConfig()
                    return render(request, "deployment_front_page.html", {'form': config_params})

                if not os.path.isfile(self.config_file):
                    return render(request, "deployment_front_page.html",
                                  {'form': config_params, 'node_reply': 'Failed to locate file "%s"' % self.config_file})
                else:
                    return HttpResponseRedirect('deploy-anylog/')

        config_params = forms.SelectConfig()
        if self.config_file is None:
            return render(request, "deployment_front_page.html", {'form': config_params})
        if not os.path.isfile(self.config_file):
            return render(request, "deployment_front_page.html",
                          {'form': config_params, 'node_reply': 'Failed to locate file "%s"' % self.config_file})
        else:
            return HttpResponseRedirect('deploy-anylog/')

    def deploy_anylog(self, request)->HttpResponse:
        """
        Once user either selects a config file or completes config form(s) - user selects what to deploy & executes
        :HTML file:
            deploy_anylog.html
        :args:
            request:django.core.handlers.wsgi.WSGIRequest - type of request against the form
        :params:
            status:bool - status
            messages:list - list of error messages
            env_params:dict - params from config file
            update_anylog:bool - whether to update AnyLog (AnyLog gets deployed by default)
            docker_passwd:str - docker password
            deploy_config:forms.DeployAnyLog - call to correlated form
        :redirect:
            --> stay w/ message
            --> deployment_front_page.html when pressing "Start Over" button
        """
        status = True
        messages = []
        base_configs = forms.BaseInfo()
        docker_passwd = None
        update_anylog = False

        # Extract configuration information
        if os.path.isfile(self.config_file): # extract values from config file
            env_params = io_config.read_configs(config_file=self.config_file)
        elif all(x == {} for x in self.env_params.values()):
            return render(request, 'deploy_anylog.html', {'form': base_configs, 'node_reply': 'Missing configurations'})
        else:
            try:
                self.config_file = os.path.join(CONFIG_FILE_PATH, '%s.ini' % self.env_params['general']['node_name'])
            except:
                messages.append('Missing NODE_NAME in set parameters')
            else:
                messages = io_config.write_configs(config_data=self.env_params, config_file=self.config_file)
        if messages != []:
            return render(request, 'deploy_anylog.html', {'form': base_configs, 'node_reply': messages})
        else:
            env_params = io_config.read_configs(config_file=self.config_file)

        print(env_params)
        # Extract values from forms
        if request.method == 'POST':
            deploy_config = forms.DeployAnyLog(request.POST)
            if deploy_config.is_valid():
                docker_passwd = request.POST.get('password')
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
                                                                               docker_password=docker_passwd,
                                                                               update_anylog=update_anylog)
                    if errors is not []:
                        for error in errors:
                            messages.append(error)

        deploy_config = forms.DeployAnyLog()
        if len(messages) != 0:
            return render(request, 'deploy_anylog.html', {'form': deploy_config, 'node_reply': messages})
        return render(request, 'deploy_anylog.html', {'form': deploy_config})

    def base_configs(self, request)->HttpResponse:
        """
        For a new deployment, get the build and node type respectively
        :HTML file:
            base_configs.html
        :args:
            request:django.core.handlers.wsgi.WSGIRequest - type of request against the form
        :params:
            messages:list - list of error messages
        :redirect:
            --> NODE_TYPE == 'none' - empty-node-configs/
            --> NODE_TYPE != 'None' - general-configs/
            --> stay if there's an error || nothing is set
        """
        messages = []
        if request.meth.POST == 'POST':
            basic_configs = forms.BaseInfo(request.POST)
            if basic_configs.is_valid():
                self.env_params['general']['build'] = request.POST.get('build')
                self.env_params['general']['node_type'] = request.POST.get('node_type')
                if self.env_params['general']['build'] == '':
                    messages.append('Missing BUILD information')
                if self.env_params['general']['node_type'] == '':
                    messages.append('Missing NODE_TYPE information')

        basic_configs = forms.BaseInfo()
        if len(messages) > 0:
            return render(request, "base_configs.html", {'form': basic_configs, 'node_reply': messages})
        elif self.env_params['general']['node_type'] == 'none':
            return HttpResponseRedirect('../empty-node-configs/')
        elif self.env_params['general']['node_type'] not in ['', 'none'] and self.env_params['general']['build'] != '':
            return HttpResponseRedirect('../general-configs/')
        else:
            return render(request, "base_configs.html", {'form': basic_configs, 'node_reply': messages})

    def none_configs(self, request)->HttpResponse:
        """
        Deployment questions for an empty node
        :args:
            request:django.core.handlers.wsgi.WSGIRequest - type of request against the form
        :params:
            messages:list - list of error messages
            db_conn_info:dict - object for db connection information
            empty_configs:forms.NoneConfigs - call to correlated form
        :redirect:
        """
        status = False
        messages = []
        db_conn_info = {'db_user': '', 'db_addr': '', 'db_pass': ''}

        if request.method == 'POST':
            empty_configs = forms.NoneConfigs()
            if empty_configs.is_valid():
                self.env_params['general']['node_name'] = request.POST.get('node_name')
                self.env_params['database']['db_type'] = request.POST.get('db_type')
                self.env_params['database']['db_port'] = request.POST.get('db_port')
                for option in list(db_conn_info.keys()):
                    if request.POST.get(option) != '':
                        db_conn_info[option] = request.POST.get(option)
                if all(db_conn_info[key] != '' for key in list(db_conn_info.keys())):
                    self.env_params['database']['db_user'] = '%s@%s:%s' % (db_conn_info['db_user'],
                                                                           db_conn_info['db_addr'],
                                                                           db_conn_info['db_pass'])

                else:
                    messages.append('Missing one or more parameters for database connection information')
                if len(messages) > 0:
                    return render(request, 'empty_node_configs.html', {'form': db_configs, 'node_reply': messages})
                else:
                    return HttpResponseRedirect('deploy-anylog/')

        db_configs = forms.NoneConfigs()
        return render(request, 'empty_node_configs.html', {'form': db_configs})