from django.shortcuts import render

# Create your views here.
# Import necessary modules
from django.shortcuts import render
from anylog.forms import AnyLogCredentials
from django.http import HttpResponse

import anylog.anylog_conn.anylog_conn as anylog_conn

# ---------------------------------------------------------------------------------------
# GET / POST  AnyLog command form
# ---------------------------------------------------------------------------------------
def form_request(request):

    # Check the form is submitted or not
    if request.method == 'POST':
        user_info = AnyLogCredentials(request.POST)
        # Check the form data are valid or not
        if user_info.is_valid():
            # Proces the command
            data = process_anylog(request)

            # print to existing screen content of data (currently DNW)
            #return render(request, "form.html", {'form': user_info, 'data': data})

            # print to (new) screen content of data
            return HttpResponse(data)
    else:
        # Display the html form
        user_info = AnyLogCredentials()

        return render(request, "form.html", {'form': user_info})

# ---------------------------------------------------------------------------------------
# Process the AnyLog command form
# ---------------------------------------------------------------------------------------
def process_anylog(request):
    '''
    :param request: The info needed to execute command to the AnyLog network
    :return: The data to display on the output form
    '''
    authentication = ()
    remote = False

    # Get the needed info from the form
    conn_info = request.POST.get('conn_info')
    username = request.POST.get('username')
    password = request.POST.get('password')
    command = request.POST.get('command')


    authentication = ()
    if username != '' and password != '':
        authentication = (username, password)

    output = anylog_conn.get_cmd(conn=conn_info, command=command, authentication=authentication, remote=False)

    return output     # Data returned from AnyLog or an Error Message