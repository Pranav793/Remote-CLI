import os
import anylog_deploy.forms as forms
from django.http.response import HttpResponse
from django.shortcuts import render
from django.http import HttpResponseRedirect


THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))

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
            'other': {},

        }
        self.deployment_options = {}
        self.docker_password = None

    def file_config(self, request)->HttpResponse:
        """
        Select file to be used
            - config_file:str - config file to use for deployment
        :args:
            request:django.core.handlers.wsgi.WSGIRequest - type of request against the form
        :redirect:
            if not config_file == '' -- stay
            if config_file == new-file -- goto start asking config question s
            if config_file != new-file and config_file != '' -- deploy based on config
        """
        if len(os.listdir(THIS_FOLDER + '/configs/')) == 0:
            return HttpResponseRedirect('base-config/')
        elif request.method == 'POST':
            configs = forms.SelectConfig(request.POST)
            if configs.is_valid():
                config_file = request.POST.get('config_file')
                return render(request, "base_configs.html", {'form': configs})
            else:
                configs = forms.SelectConfig()
                return render(request, "base_configs.html", {'form': configs})

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
                self.docker_password = request.POST.get('password')
                if self.env_params['general']['node_type'] == 'none' or self.env_params['general']['node_type'] == '':
                    # Deploy AnyLog of type None
                    print(type(render(request, "base_configs.html", {'form': base_configs})))
                    return render(request, "base_configs.html", {'form': base_configs})
                else:
                    return HttpResponseRedirect('general-config/')
        else:
            base_configs = forms.BaseInfo()
            return render(request, "base_configs.html", {'form': base_configs})

    def general_info(self, request)->HttpResponse:
        """
        General configuration
            - node name
            - company
            - disable location
                if set to False:
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
        if request.method == 'POST':
            general_config = forms.GeneralInfo(request.POST)
            if general_config.is_valid():
                self.env_params['general']['node_name'] = request.POST.get('node_name')
                self.env_params['general']['comapny_name'] = request.POST.get('company_name')
                try:
                    disable_location = request.POST.get('disable_location')
                except:
                    disable_location = None

                if disable_location == 'on':
                    self.env_params['other']['disable_location'] = True
                else:
                    self.env_params['other']['disable_location'] = False
                    location = request.POST.get('location')
                    if location != '':
                        self.env_params['general']['location'] = location

                try:
                    authentication = request.POST.get('authentication')
                except:
                    authentication = None
                if authentication is None:
                    self.env_params['authentication']['authentication'] = 'off'
                else:
                    self.env_params['authentication']['authentication'] = 'on'

                self.env_params['authentication']['username'] = request.POST.get('username')
                self.env_params['authentication']['password'] = request.POST.get('password')
                self.env_params['authentication']['auth_type'] = request.POST.get('auth_type')

                print(self.deployment_options)
                if self.env_params['general']['node_type'] == 'operator':
                    return HttpResponseRedirect('db-operator-configs/')
                else:
                    return HttpResponseRedirect('db-configs/')
        else:
            general_config = forms.GeneralInfo()
            return render(request, "general_configs.html", {'form': general_config})

    def db_configs(self, request):
        """
        Configuration for non-Operator node -- only database information
        """
        if request.method == 'POST':
            db_configs = forms.DBConfigs(request.POST)
            if db_configs.is_valid():
                print(request.POST.get)
                return render(request, "db_configs.html", {'form': db_configs})
            else:
                return render(request, "db_configs.html", {'form': db_configs})
        else:
            db_configs = forms.DBConfigs()
            return render(request, "db_configs.html", {'form': db_configs})

    def operator_configs(self, request):
        """
        Configuration for both database and operator
        """
        if request.method == 'POST':
            db_operator_configs = forms.DBOperatorConfigs(request.POST)
            if db_operator_configs.is_valid():
                print(request.POST.get)
                return render(request, 'db_operator_configs.html', {'forms': db_operator_configs})
            else:
                return render(request, 'db_operator_configs.html', {'forms': db_operator_configs})
        else:
            db_operator_configs= forms.DBOperatorConfigs()
            return render(request, 'db_operator_configs.html', {'forms': db_operator_configs})

def index(request):
    if request.method == 'POST':
        user_info = forms.AnyLogDeployment()
        # Check the form data are valid or not
        if user_info.is_valid():
            return render(request, "base_configs.html", {'form': user_info})
            # # Proces the command
            # # command, output = process_anylog(request)
            #
            # return print_network_reply(request, user_info, command, output)
            #
            # # print to existing screen content of data (currently DNW)
            # # return render(request, "base_configs.html", {'form': user_info, 'node_reply': node_reply})
            #
            # # print to (new) screen content of data
            # # return HttpResponse(data)
    else:
        # Display the html form
        user_info = forms.AnyLogDeployment()

        return render(request, "base_configs.html", {'form': user_info})

