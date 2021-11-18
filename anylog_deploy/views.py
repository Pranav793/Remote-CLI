import django.http.response
from django.shortcuts import render
from django.http import HttpResponseRedirect
import anylog_deploy.forms as forms


class FormViews:
    def __init__(self):
        self.env_params = {}
        self.deployment_options = {}
        self.docker_password = None

    # Create your views here.
    def basic_config(self, request):
        """
        Basic configurations
            - build
            - node type
            - docker password
        """
        if request.method == 'POST':
            base_configs = forms.BaseInfo(request.POST)
            if base_configs.is_valid():
                self.env_params['BUILD'] = request.POST.get('build')
                self.env_params['NODE_TYPE'] = request.POST.get('node_type')
                self.docker_password = request.POST.get('password')
                if self.env_params['NODE_TYPE'] == 'none' or self.env_params['NODE_TYPE'] == '':
                    # Deploy AnyLog of type None
                    return render(request, "base.html", {'form': base_configs})
                else:
                    return HttpResponseRedirect('general-config/')
        else:
            base_configs = forms.BaseInfo()
            return render(request, "base.html", {'form': base_configs})

    def general_info(self, request):
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
        """
        if request.method == 'POST':
            general_config = forms.GeneralInfo(request.POST)
            if general_config.is_valid():
                self.env_params['NODE_NAME'] = request.POST.get('node_name')
                self.env_params['COMPANY_NAME'] = request.POST.get('company_name')
                try:
                    disable_location = request.POST.get('disable_location')
                except:
                    disable_location = None

                if disable_location == 'on':
                    self.deployment_options['disable_location'] = True
                else:
                    self.deployment_options['disable_location'] = False
                    location = request.POST.get('location')
                    if location != '':
                        self.env_params['LOCATION'] = location

                try:
                    authentication = request.POST.get('authentication')
                except:
                    authentication = None
                if authentication is None:
                    self.env_params['AUTHENTICATION'] = 'off'
                else:
                    self.env_params['AUTHENTICATION'] = 'on'

                self.env_params['USERNAME'] = request.POST.get('username')
                self.env_params['PASSWORD'] = request.POST.get('password')
                self.env_params['AUTH_TYPE'] = request.POST.get('auth_type')

                print(self.deployment_options)
                return render(request, "general_configs.html", {'form': general_config})
        else:
            general_config = forms.GeneralInfo()
            return render(request, "general_configs.html", {'form': general_config})

    def

def index(request):
    if request.method == 'POST':
        user_info = forms.AnyLogDeployment()
        # Check the form data are valid or not
        if user_info.is_valid():
            return render(request, "base.html", {'form': user_info})
            # # Proces the command
            # # command, output = process_anylog(request)
            #
            # return print_network_reply(request, user_info, command, output)
            #
            # # print to existing screen content of data (currently DNW)
            # # return render(request, "base.html", {'form': user_info, 'node_reply': node_reply})
            #
            # # print to (new) screen content of data
            # # return HttpResponse(data)
    else:
        # Display the html form
        user_info = forms.AnyLogDeployment()

        return render(request, "base.html", {'form': user_info})

