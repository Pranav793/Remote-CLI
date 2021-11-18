import django.http.response
from django.shortcuts import render
from django.http import HttpResponseRedirect
import anylog_deploy.forms as forms


class FormViews:
    def __init__(self):
        self.params = {}
        self.docker_password = None

    # Create your views here.
    def basic_config(self, request):
        if request.method == 'POST':
            base_configs = forms.BaseInfo(request.POST)
            if base_configs.is_valid():
                self.params['BUILD'] = request.POST.get('build')
                self.params['NODE_TYPE'] = request.POST.get('node_type')
                self.docker_password = request.POST.get('password')
                if self.params['NODE_TYPE'] == 'none' or self.params['NODE_TYPE'] == '':
                    # Deploy AnyLog of type None
                    return render(request, "base.html", {'form': base_configs})
                else:
                    return HttpResponseRedirect('general-config/')
        else:
            base_configs = forms.BaseInfo()
            return render(request, "base.html", {'form': base_configs})


    def general_info(self, request):
        if request.method == 'POST':
            general_config = forms.GeneralInfo(request.POST)
            if general_config.is_valid():
                self.params['NODE_NAME'] = request.POST.get('node_name')
                self.params['COMPANY_NAME'] = request.POST.get('company_name')
                location = request.POST.get('location')
                if location != '':
                    self.params['LOCATION'] = location
                try:
                    authentication = request.POST.get('authentication')
                except:
                    authentication = None
                if authentication is None:
                    self.params['AUTHENTICATION'] = 'off'
                else:
                    self.params['AUTHENTICATION'] = 'on'
                self.params['USERNAME'] = request.POST.get('username')
                self.params['PASSWORD'] = request.POST.get('password')
                self.params['AUTH_TYPE'] = request.POST.get('auth_type')

                print(self.params)
                return render(request, "base.html", {'form': general_config})
        else:
            general_config = forms.GeneralInfo()
            return render(request, "base.html", {'form': general_config})


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

