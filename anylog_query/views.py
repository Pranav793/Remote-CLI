import sys
import os
from django.shortcuts import render

import copy

# Import necessary modules
from django.shortcuts import render
from django.http import HttpResponse
import webbrowser

from djangoProject.settings import BASE_DIR


import anylog_query.json_api as json_api
import anylog_query.anylog_conn.anylog_conn as anylog_conn

json_file = os.path.join(str(BASE_DIR) + os.sep + "anylog_query" + os.sep + "static" + os.sep + "json" + os.sep + "commands.json")

data, error_msg = json_api.load_json(json_file)

if not error_msg:
    ANYLOG_COMMANDS = data["commands"]
else:
    sys.exit('Failed to load commands file from: %s\r\nError: %s\r\n' % (json_file, error_msg))

must_have_keys = [      # These keys are tested in each coimmand in the JSON file
    'button',
    'command',
    'type',
    'group',
    'help_url'
]

COMMANDS_GROUPS = ["All"]
if ANYLOG_COMMANDS:
    for command in ANYLOG_COMMANDS:
        for key in must_have_keys:
            # test all keys exists
            if not key in command:
                if key != "help_url":
                    sys.exit("Missing key: '%s' in commands.json file at entry: %s" % (key, str(command)))
            if key == "group":
                value = command[key]
                if not value in COMMANDS_GROUPS:
                    COMMANDS_GROUPS.append(command[key])


'''
COMMANDS_GROUPS = [
    "All",
    "Status",
    "Queries",
    "Logs",
    "Southbound",
    "Northbound",
    "Blockchain",
    "Other",
]
'''

COMMAND_BY_BUTTON = {}
for index, entry in enumerate(ANYLOG_COMMANDS):
    COMMAND_BY_BUTTON[entry['button']] = index     # Organize commands as f(button)


# ---------------------------------------------------------------------------------------
# GET / POST  AnyLog command form
# ---------------------------------------------------------------------------------------
def form_request(request):

    send = request.POST.get("Send")

    # Check the form is submitted or not
    if request.method == 'POST' and send:

        # Proces the command
        output = process_anylog(request)

        user_cmd = request.POST.get("command")
        if len(user_cmd) > 5 and user_cmd.strip()[:4].lower() == "sql ":
            query_result = True
        else:
            query_result = False


        return print_network_reply(request, query_result, output)

    else:
        # Display the html form
        select_info = {}
        button = request.POST.get("button")
        if button:
            add_form_value(select_info, request)
            command_id = COMMAND_BY_BUTTON[button]
            cmd_info = ANYLOG_COMMANDS[command_id]

            if request.POST.get("help"):
                # Open the URL for help
                select_info["help"] = True
                help_url = "https://github.com/AnyLog-co/documentation/"
                if "help_url" in cmd_info and cmd_info["help_url"]:
                    help_url += cmd_info["help_url"]

                webbrowser.open(help_url)
            else:
                user_cmd = cmd_info["command"]             # Set the command

                if len (user_cmd) > 5 and user_cmd[:4].lower().startswith("sql "):
                    select_info["network"] = True     # Used to Flag the network bool on the page

                    # add dbms name and table name
                    dbms_name = request.POST.get('dbms')
                    table_name = request.POST.get('table')

                    if dbms_name:
                        user_cmd = user_cmd.replace("[DBMS]", dbms_name, 1)
                    if table_name:
                        user_cmd = user_cmd.replace("[TABLE]", table_name, 1)

                    timezone = request.POST.get('timezone')


                    # Add output format
                    out_format = request.POST.get('out_format')
                    cmd_list = user_cmd.split(' ',3)
                    if len(cmd_list) > 3:
                        if out_format == "table":
                            sql_instruct = "format = table "
                            select_info["out_format"] = "table"  # Keep selection menue on table
                        else:
                            sql_instruct = "format = json "
                            select_info["out_format"] = None        # Keep selection menue on JSON

                        if timezone:
                            sql_instruct += "and timezone = %s " % timezone
                            select_info["timezone"] = timezone
                        else:
                            select_info["timezone"] = None

                        user_cmd = user_cmd.replace(cmd_list[2], sql_instruct + cmd_list[2])
                else:
                    select_info["network"] = False

                select_info["command"] = user_cmd
                rest_call = cmd_info["type"]
                if rest_call == "GET":
                    select_info["rest_call"] = rest_call        # Set Put or Get
                else:
                    select_info["rest_call"] = None

        else:
            if request.method == 'POST':
                # Send was not selected - keep the older selected values
                add_form_value(select_info, request)  # add the values of the last form to the select_info
            else:
                select_info["rest_call"] = "GET"

                buttons_type = request.POST.get('cmd_type')  # These are the type of commands buttons that will be displayed
                if buttons_type:
                    select_info["cmd_type"] = buttons_type  # These are the type of commands buttons that will be displayed
                else:
                    select_info["cmd_type"] = "Logs"  # These are the type of commands buttons that will be displayed

        # Add info which is not selected but is used by the form
        select_info["commands_list"] = ANYLOG_COMMANDS
        select_info["commands_groups"] = COMMANDS_GROUPS

        return render(request, "base.html", select_info)
# ---------------------------------------------------------------------------------------
# Process the AnyLog command form
# ---------------------------------------------------------------------------------------
def process_anylog(request):
    '''
    :param request: The info needed to execute command to the AnyLog network
    :return: The data to display on the output form
    '''

    post_data = request.POST

    # Get the needed info from the form
    conn_info = post_data.get('connect_info').strip()
    username = post_data.get('auth_usr').strip()
    password = post_data.get('auth_pass').strip()
    command = post_data.get('command').strip()

    network = post_data.get('network') == "on"
    rest_call = post_data.get('rest_call')

    destination =  post_data.get('destination').strip()

    if command:
        authentication = ()
        if username != '' and password != '':
            authentication = (username, password)

        if rest_call == "post":
            output = anylog_conn.post_cmd(conn=conn_info, command=command, authentication=authentication)
        else:
            output = anylog_conn.get_cmd(conn=conn_info, command=command, authentication=authentication, remote=network, dest=destination)
    else:
        output = "Mising commmand"

    return output     # Data returned from AnyLog or an Error Message
# -----------------------------------------------------------------------------------
# Print network reply -
# Option 1 - a tree
# Option 2 - a table
# Option 3 - text
# -----------------------------------------------------------------------------------
def print_network_reply(request, query_result, data):

    select_info = {}
    add_form_value(select_info, request)        # add the values of the last form to the select_info

    select_info['title'] = 'Network Command'
    select_info["commands_list"] = ANYLOG_COMMANDS
    select_info["commands_groups"] = COMMANDS_GROUPS

    if not data:
        if query_result:
            print_info = [("text",'{"reply" : "Empty data set"}')]
        else:
            print_info = None
    elif data.startswith("Failed to"):
        print_info = [("text", data)]  # Print the error msg as a string
    elif query_result and data[:8] != "{\"Query\"":
        print_info = [("text", data)]  # Print the error msg as a string
    elif is_complex_struct(data):
        print_info = [("text", data)]   # Keep as is
    else:
        policy, table_info, print_info, error_msg = format_message_reply(data)
        if policy:
            # Reply was a JSON policy or a query replied in JSON
            data_list = []
            json_api.setup_print_tree(policy, data_list)
            select_info['text'] = data_list
            return render(request, 'output_tree.html', select_info)

        if query_result:
            # Failed to map the result to JSON
            print_info = [("text", data)]  # Print the query reply as a string
        elif table_info:
            # Reply is structured as a table

            if 'header' in table_info:
                select_info['header'] = table_info['header']
            if 'table_title' in table_info:
                select_info['table_title'] = table_info['table_title']
            if 'rows' in table_info:
                select_info['rows'] = table_info['rows']
            return render(request, 'output_table.html', select_info)


    select_info['text'] = print_info        # Only TEXT

    return render(request, 'output_cmd.html', select_info)


# -----------------------------------------------------------------------------------
# Determine if the data is not mapped to a simple table or JSON
# -----------------------------------------------------------------------------------
def is_complex_struct( data ):
    index =  data.find("\r\n\r\n")
    if index != -1:
        complex = True
    else:
        complex = False
    return complex
# -----------------------------------------------------------------------------------
# add the values of the last form to the select_info
# -----------------------------------------------------------------------------------
def add_form_value(select_info, request):
    post_data = request.POST
    for key, value in post_data.items():
        select_info[key] = value
    if  select_info["rest_call"] == "post":
        select_info["rest_call"] = None
    if  select_info["out_format"] == "json":
        select_info["out_format"] = None

# -----------------------------------------------------------------------------------
# Based on the message reply - organize as a table or as an attrubute values list
# -----------------------------------------------------------------------------------
def format_message_reply(msg_text):
    '''
    Return 4 values depending on the type of message:
    policy
    table_info (header, title and rows)
    Text List (entries are attr - val pairs)
    '''

    # If the message is a dictionary or a list - return the dictionary or the list

    policy = None
    error_msg = None
    if msg_text[0] == '{' and msg_text[-1] == '}':
        policy, error_msg = json_api.string_to_json(msg_text)

    elif msg_text[0] == '[' and msg_text[-1] == ']':
        policy, error_msg = json_api.string_to_list(msg_text)

    if policy:
        return [policy, None, None, error_msg]  # return the dictionary or the list


    # Make a list of strings to print
    data = msg_text.replace('\r', '')
    text_list = data.split('\n')


    # Test id the returned message is formatted as a table
    table_data = {}
    is_table = False
    for index, entry in enumerate(text_list):
        if entry and index:
            table_struct = entry.strip()
            if table_struct[0] == '-' and table_struct[-1] == '|':
                # Identified a table
                is_table = True
                columns_list = entry.split('|')
                columns_size = []
                for column in columns_list:
                    if len(column):
                        columns_size.append(len(column))     # An array with the size of each column
                header = []
                offset = 0
                for column_id, size in enumerate(columns_size):
                    header.append(text_list[index - 1][offset:offset + size])
                    offset += (size + 1)                # Add the field size and the separator (|)

                table_data['header'] = header
                if index > 1 and len(text_list[index -2]):
                    table_data['table_title'] = text_list[index -2]         # Get the title if available
                break
        if index >= 5:
            break  # not a table

    if is_table:
        # a Table setup and print
        table_rows = []
        for y in range(index + 1, len(text_list)): # Skip the dashed separator to the column titles
            row = text_list[y]
            if row:
                columns = []
                offset = 0
                for column_id, size in enumerate(columns_size):
                    columns.append(row[offset:offset + size])
                    offset += (size + 1)  # Add the field size and the separator (|)

                table_rows.append(columns)

        table_data['rows'] = table_rows
        return [None, table_data, None, None]

    # Print Text

    data_list = []     # Every entry holds type of text ("text" or "Url) and the text string

    set_table = False

    for entry in text_list:

        # Setup URL Link (reply to help command + a link to the help page)
        if entry[:6] == "Link: ":
            if set_table:
                data_list[-1][3] = "table_end"
                set_table = False

            index = entry.rfind('#')  # try to find name of help section
            if index != -1:
                section = entry[index + 1:].replace('-', ' ')
            else:
                section = ""
            data_list.append(("url", entry[6:], section))
        else:
            # Split text to attribiute value using colon
            if entry:
                key_val = entry.split(':', 2)
                if len(key_val) == 1 or len(key_val) == 3:
                    if set_table:
                        data_list[-1][3] = "table_end"
                        set_table = False
                    data_list.append(["text",entry] )
                elif len(key_val) == 2:
                    # Set as a table in the HTML
                    data_list.append(["key_val", key_val[0], key_val[1], "table"])
                    if not set_table:
                        data_list[-1][3] = "table_start"
                        set_table = True

    if set_table:
        data_list[-1][3] = "table_end"

    return [None, None, data_list, None]

