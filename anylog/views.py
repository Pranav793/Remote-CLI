from django.shortcuts import render

# Create your views here.
# Import necessary modules
from django.shortcuts import render
from anylog.forms import AnyLogCredentials
from django.http import HttpResponse

import anylog.anylog_conn.anylog_conn as anylog_conn


ANYLOG_COMMANDS = {
    1: 'get status',                         # Get Node Status
    2: 'get event log where format=json',    # Get Event Log
    3: 'get error log where format=json',    # Get Error Log
    40: 'set rest log off',                  # Set REST Log Off
    41: 'set rest log on',                   # Set REST Log On
    5: 'get rest all',                       # Get REST
    6: 'get rest',                           # GET REST log
    7: 'get streaming',                      # Get Streaming
    8: 'get operator',                       # Get Operator
    9: 'get publisher',                      # Get Publishe
    10: 'query status all',                  # Get Query Status
    11: 'query status',                      # Get Last Query Status
    12: 'get rows count',                    # Get Rows Count
    13: 'get rows count where group=table',  # Get Rows Count by Table
}

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
            node_reply = process_anylog(request)

            # print to existing screen content of data (currently DNW)
            return render(request, "form.html", {'form': user_info, 'node_reply': node_reply})

            # print to (new) screen content of data
            # return HttpResponse(data)
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
    anylog_cmd = request.POST.get('anylog_cmd')
    network = request.POST.get('network')

    if network == 'on':
        network = True
    else:
        network = False
    post = request.POST.get('post')
    if post == 'on':
        post = True
    else:
        post = False

    if anylog_cmd is not None:
        anylog_cmd = int(anylog_cmd)
        if anylog_cmd == 40 or anylog_cmd == 41:
            post = True

        command = ANYLOG_COMMANDS[anylog_cmd]

    authentication = ()
    if username != '' and password != '':
        authentication = (username, password)

    print(command)
    if post is True:
        output = anylog_conn.post_cmd(conn=conn_info, command=command, authentication=authentication)
    else:
        output = anylog_conn.get_cmd(conn=conn_info, command=command, authentication=authentication, remote=network)

    # Data returned from AnyLog or an Error Message
    return output