from django.shortcuts import render
from django.http import HttpResponse
from anylog_deploy.forms import AnyLogDeployment

# Create your views here.
def index(request):
    if request.method == 'POST':
        user_info = AnyLogDeployment()
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
        user_info = AnyLogDeployment()

        return render(request, "base.html", {'form': user_info})


