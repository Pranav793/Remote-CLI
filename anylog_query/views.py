import sys
import os
from pathlib import Path
from django.shortcuts import render

import copy

# Import necessary modules
from django.shortcuts import render
from django.http import HttpResponse
import webbrowser

from djangoProject.settings import BASE_DIR


import anylog_query.json_api as json_api
import anylog_query.utils_io as utils_io
import anylog_query.anylog_conn.anylog_conn as anylog_conn

json_file = os.path.join(str(BASE_DIR) + os.sep + "anylog_query" + os.sep + "static" + os.sep + "json" + os.sep + "commands.json") # Absolute path
blobs_dir = os.path.join(str(BASE_DIR) + os.sep + "anylog_query" + os.sep + "static" + os.sep + "blobs" + os.sep + "current"+ os.sep) # Absolute path
keep_dir = os.path.join(str(BASE_DIR) + os.sep + "anylog_query" + os.sep + "static" + os.sep + "blobs" + os.sep + "keep"+ os.sep) # Dir for saved blobs - # Absolute path
blobs_local_dir = "blobs/current/"

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

conf_file_names = [
    "Autoexec",
    "Operator",
    "Publisher",
    "Query",
    "Master",
    "Standalone"
]

user_selections = {
        'connect_info' : None,
        'auth_usr' : None,
        'auth_pass' : None,
        'cmd_type' : None,
        'timeout' : None,
        'dbms' : None,
        'table' : None,
        'timezone' : None,
        'out_format' : None,
        'network' : None,
        'destination' : None,
        'command' : None,
}
# ---------------------------------------------------------------------------------------
# GET / POST  AnyLog command form
# ---------------------------------------------------------------------------------------
def form_request(request):

    form = request.POST.get("Form")         # The form used

    blobs_button = request.POST.get("Blobs")    # The blobs button was selected
    config_button = request.POST.get("Config")  # The Config button was selected
    client_button = request.POST.get("Client")  # Client button was selected

    if blobs_button or (form == "Blobs" and not client_button and not config_button):
        # Either the blobs Button was selected (on a different form) or the blobs Page is processed.
        return blobs_processes(request, blobs_button)

    if config_button:
        # config button was selected - go to the config page
        select_info = {}
        select_info["conf_file_names"] = conf_file_names
        select_info["file_name"] = "Autoexec"
        return render(request, "config.html", select_info)

    if form == "Config" and not client_button:

        select_info = {}
        select_info["conf_file_names"] = conf_file_names

        file_name = request.POST.get('file_name')
        if file_name:
            select_info["file_name"] = file_name        # will get the name of the config file at the node config dir
        connect_info = request.POST.get('connect_info')
        if connect_info:
            select_info["connect_info"] = connect_info.strip()

        if request.POST.get("Load"):
            reply = config_load_file(request)       # Load config file from local directory
            select_info["conf_file"] = reply
            return render(request, "config.html", select_info)
        if request.POST.get("Save"):
            reply = get_updated_config("none", -1, request)
            select_info["conf_file"] = reply
            node_result = config_save_file(request, reply)       # Save config file on local directory
            return render(request, "config.html", select_info)

        update_id = request.POST.get("delete")
        if update_id:
            reply = get_updated_config("delete", update_id, request)
        else:
            update_id = request.POST.get("insert_above")
            if update_id:
                reply = get_updated_config("insert_above", update_id, request)
            else:
                update_id = request.POST.get("insert_below")
                reply = get_updated_config("insert_below", update_id, request)
        if update_id:
            # Goto the webpage with the update
            select_info["conf_file"] = reply
            return render(request, "config.html", select_info)

    return client_processes(request, client_button)    # Client processes - the main form interacting with the network

# ---------------------------------------------------------------------------------------
# Client processes - the main form interacting with the network
# ---------------------------------------------------------------------------------------
def blobs_processes(request, blobs_button):

    global keep_dir         # Absolute Path - Saved blobss
    global blobs_dir        # Absolute Path - Copied blobss
    global blobs_local_dir  # "blobs/current/"

    select_info = {}

    keep_file = False
    delete_file = False
    watch_file = False
    file_name = None

    post_data = request.POST

    if blobs_button:
        # blobs_button was selected - Copy the files from the source servers

        copied_info = get_blobs(request)      # Copy blobs files from dest machines

    else:
        # process the form - delete or move the file

        if "Keep" in post_data:
            # move the file to "Keep" Directory
            keep_file = True
        elif "Delete" in post_data:
            delete_file = True
        if "Watch" in post_data:
            # move the file to "Keep" Directory
            watch_file = True

        for entry in post_data:
            if entry.startswith("file@"):
                if len(entry) > 5:
                    file_name = entry[5:]
                    if watch_file:
                        break       # Exit with the first file to watch
                    if delete_file:
                        utils_io.delete_file(blobs_dir + file_name)
                    elif keep_file:
                        # save the file in the "keep" directory
                        utils_io.copy_file(keep_dir + file_name, blobs_dir + file_name)


    copied_blobs = utils_io.get_files_in_dir(blobs_dir, True)     # Get the list of files that were copied

    # Go to the page - blobs.html

    select_info["column_names"] = ["blobs", "Size", "select"]

    select_info["rows"] = copied_blobs

    if watch_file and file_name:
        # Use the first flagged file
        active_file = blobs_local_dir + file_name
    elif len (copied_blobs):
        # Use the first file in the directory
        active_file = blobs_local_dir + copied_blobs[0][0]
    else:
        active_file = None

    if active_file:
        select_info["active_file"] = active_file        # Taken as - <source src="{% static "blobs/current/files.10_seconds.0.mp4" %}" type="blobs/mp4">

    return render(request, "blobs.html", select_info) # Process the blobs page

# ---------------------------------------------------------------------------------------
# Client processes - the main form interacting with the network
# ---------------------------------------------------------------------------------------
def client_processes(request, client_button):

    selection_output = False
    send_button = request.POST.get("Send")

    # Check the form is submitted or not
    if not client_button and request.method == 'POST' and send_button:
        # SEND THE COMMAND TO DESTINATION NODE

        user_cmd = request.POST.get("command")
        if len(user_cmd) > 5 and user_cmd.strip()[:4].lower() == "sql ":
            query_result = True
            if user_cmd.endswith(" selection"):
                sql_cmd = user_cmd[:-10].rstrip()
                if sql_cmd[-2:] == " >":
                    user_cmd = sql_cmd[:-2].rstrip()
                    selection_output = True     # Push the returned JSON value into a selection table
        else:
            query_result = False

        # Process the command
        output = process_anylog(request, user_cmd)        # SEND THE COMMAND TO DESTINATION NODE

        return print_network_reply(request, query_result, output, selection_output)

    else:
        # Display the html form

        command_button = request.POST.get("button")
        if command_button:
            select_info = command_button_selected(request, command_button)
        else:
            select_info = {}
            restore_user_selections(request.POST, select_info)

            if not client_button and request.method == 'POST':
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

        keep_user_selections(select_info)

        return render(request, "base.html", select_info)

# ---------------------------------------------------------------------------------------
# Command button was selected - get the command info and set the command on select_info
# so it can be placed on the command line
# ---------------------------------------------------------------------------------------
def command_button_selected(request, command_button):
    '''
    Return a select_info structure with the info selected by the button
    '''
    select_info = {}


    restore_user_selections(request.POST, select_info)

    # AnyLog command button was selected
    add_form_value(select_info, request)
    command_id = COMMAND_BY_BUTTON[command_button]
    cmd_info = ANYLOG_COMMANDS[command_id]

    if request.POST.get("help"):
        # Open the URL for help
        select_info["help"] = True
        help_url = "https://github.com/AnyLog-co/documentation/"
        if "help_url" in cmd_info and cmd_info["help_url"]:
            help_url += cmd_info["help_url"]

        webbrowser.open(help_url)
    else:
        user_cmd = cmd_info["command"]  # Set the command

        if len(user_cmd) > 5 and user_cmd[:4].lower().startswith("sql "):
            select_info["network"] = True  # Used to Flag the network bool on the page

            # add dbms name and table name
            dbms_name = request.POST.get('dbms')
            table_name = request.POST.get('table')

            if dbms_name:
                user_cmd = user_cmd.replace("[DBMS]", dbms_name, 1)
            if table_name:
                user_cmd = user_cmd.replace("[TABLE]", table_name, 1)

            # Add output format
            user_cmd = add_sql_instructions(request, user_cmd) # Add format and timezone


        else:
            select_info["network"] = False

        select_info["command"] = user_cmd
        rest_call = cmd_info["type"]
        if rest_call == "GET":
            select_info["rest_call"] = rest_call  # Set Put or Get
        else:
            select_info["rest_call"] = None

    return select_info

# ---------------------------------------------------------------------------------------
# Update SQL Instructions section
# Find the location after the "sql" and database name, and update the instructions if needed
# ---------------------------------------------------------------------------------------
def add_sql_instructions(request, user_cmd):


    added_instructions = {
        "timezone" : request.POST.get('timezone'),
        "format"    : request.POST.get('out_format')
    }

    cmd_list = user_cmd.split(' ', 2)

    if len(cmd_list) == 3:

        # Split by: sql, dbms_name, instructions + SQL
        cmd_lower = cmd_list[2].lower()
        index = cmd_lower.find("select ")

        if index != -1:
            if index == 0:
                instructions = ""       # No instructions
                instructions_lower = ""
            else:
                instructions = cmd_list[2][:index]
                instructions_lower = cmd_lower[:index]  # The existing instructions

            for key, value in added_instructions.items():
                # Add values from the Form
                if value:
                    if instructions_lower.find(key) == -1:
                        new_instruction = "%s = %s " % (key, value)
                        if len(instructions):
                            instructions = new_instruction + ("and " + instructions)
                        else:
                            instructions = new_instruction


            user_cmd = "sql " + cmd_list[1] + " " + instructions + cmd_list[2][index:]
    return user_cmd
# ---------------------------------------------------------------------------------------
# Process the AnyLog command form
# ---------------------------------------------------------------------------------------
def process_anylog(request, user_cmd):
    '''
    :param request: The info needed to execute command to the AnyLog network
    :param user_cmd: The command issued by the user - it appears in requests (request.POST.get("command")), but maybe was modified by the caller
    :return: The data to display on the output form
    '''

    post_data = request.POST

    # Get the needed info from the form
    conn_info = post_data.get('connect_info').strip()
    username = post_data.get('auth_usr').strip()
    password = post_data.get('auth_pass').strip()
    command = user_cmd

    timeout = post_data.get('timeout').strip()  # Change default timeout
    subset = post_data.get('subset') == "on" # Returns reply even if not oll nodes replied

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
            output = anylog_conn.get_cmd(conn=conn_info, command=command, authentication=authentication, remote=network, dest=destination, timeout=timeout, subset=subset)
    else:
        output = "Mising commmand"

    return output     # Data returned from AnyLog or an Error Message
# -----------------------------------------------------------------------------------
# Print network reply -
# Option 1 - a tree
# Option 2 - a table
# Option 3 - text
# -----------------------------------------------------------------------------------
def print_network_reply(request, query_result, data, selection_output):
    '''
    request - the form info
    query_result - a True/False value representing SQL query data set returned
    data - the query or command result
    selection_output - user issued a SQL statement with "> selection" at the end - indicating output to a selection table
    '''

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
        policies, error_msg = json_api.string_to_json(data)
        if policies:
            # Show as JSON
            data_list = []
            json_api.setup_print_tree(policies, data_list)
            select_info['text'] = data_list
            keep_user_selections(select_info)
            return render(request, 'output_tree.html', select_info)

        print_info = [("text", data)]  # Print the error msg as a string
    elif is_complex_struct(data):
        print_info = [("text", data)]   # Keep as is
    else:
        policies, table_info, print_info, error_msg = format_message_reply(data)
        if policies:
            if selection_output:
                # Show as a selection table
                keep_user_selections(select_info)
                return json_to_selection_table(request, select_info, policies)
            else:
                # Reply was a JSON policies or a query replied in JSON
                data_list = []
                json_api.setup_print_tree(policies, data_list)
                select_info['text'] = data_list
                keep_user_selections(select_info)
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
            keep_user_selections(select_info)
            return render(request, 'output_table.html', select_info)


    select_info['text'] = [("text", data)]        # Only TEXT
    keep_user_selections(select_info)
    return render(request, 'output_cmd.html', select_info)

# -----------------------------------------------------------------------------------
# Output to selection table
# Change the query reply from JSON to selection table format and call the report
# -----------------------------------------------------------------------------------
def json_to_selection_table(request, select_info, policies):
    # Show as a selection table
    policies_list = policies["Query"]
    one_policy = policies_list[0]
    column_names = []
    # Get the title for the table from the first policy
    for attr_name in one_policy.keys():
        column_names.append(attr_name)
    select_info['column_names'] = column_names

    # add the data as a columns per row
    rows = []
    for policy in policies_list:
        columns_val = []
        for attr_val in policy.values():
            columns_val.append(attr_val)
        rows.append(columns_val)

    select_info['rows'] = rows

    return render(request, 'output_selection.html', select_info)


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

# -----------------------------------------------------------------------------------
# Load config file from local directory
# -----------------------------------------------------------------------------------
def config_load_file(request):

    post_data = request.POST

    # Get the needed info from the form
    conn_info = post_data.get('connect_info').strip()

    authentication = anylog_conn.get_auth(request)


    file_name = post_data.get('file_name').strip()

    command = "get script %s" % file_name

    output = anylog_conn.get_cmd(conn=conn_info, command=command, authentication=authentication, remote=False,  dest="", timeout="", subset=False)
    if output:
        file_rows = output.split("\r\n")
        # organize each roow with id
        config_list = []
        for index, row in enumerate(file_rows):
            config_list.append({"index" : index, "row" : row})
    else:
        config_list = None
    return config_list


# -----------------------------------------------------------------------------------
# Save config file on local directory
# -----------------------------------------------------------------------------------
def config_save_file(request, file_rows):

    post_data = request.POST

    # Get the needed info from the form
    conn_info = post_data.get('connect_info').strip()

    authentication = anylog_conn.get_auth(request)

    file_name = post_data.get('file_name').strip()

    # Note 1 - the \r is used to take the info as one word in the network node
    # Note 2 - This command is passed in the message body as the header will not take file data with \r\n
    file_data = ("set script autoexec \r%s" % "\n".join([str(item["row"]) for item in file_rows]))

    command = "body"        # The command is passed in the message body


    output = anylog_conn.post_cmd(conn=conn_info, command=command, authentication=authentication, msg_data=file_data)

    return output
# -----------------------------------------------------------------------------------
# Update the config file based on the user request
# -----------------------------------------------------------------------------------
def get_updated_config(operation, update_id, request):

    post_info = request.POST

    config_list = []
    index = 0
    row_added = 0
    insert_below = False
    while True:

        if update_id == str(index):
            if operation == "delete":
                index += 1
                row_added = -1
                continue
            if operation == "insert_above":
                config_list.append({"index": index, "row": ""}) # insert new row
                row_added = 1
            if operation == "insert_below":
                insert_below = True

        key = "new_row.%s" % index
        if not key in post_info:
            break

        new_row = post_info[key]
        config_list.append({"index": index + row_added, "row": new_row})
        index = index + 1

        if insert_below:
            config_list.append({"index": index, "row": ""})  # insert new row
            row_added = 1
            insert_below = False

    return config_list

# -----------------------------------------------------------------------------------
# Get the blobs files from the dest machines
# -----------------------------------------------------------------------------------
def get_blobs(request):

    global blobs_dir

    post_data = request.POST

    # Get the needed info from the form
    conn_info = post_data.get('connect_info').strip()

    authentication = anylog_conn.get_auth(request)

    # Search for selected files

    copied_info = []        # Collect the files copied and the message if an error happened

    for entry in post_data:
        if entry.startswith("get@"):
            entry_list = entry.split('@')
            if len(entry_list) == 5:
                # Get the blobs file operator info and file name
                operator_ip = entry_list[1]
                operator_port = entry_list[2]
                destination = "%s:%s" % (operator_ip, operator_port)
                archive_path = entry_list[3]
                file_name = entry_list[4]

                command = "file get !!blobs_dir/%s/%s %s" % ( archive_path, file_name, blobs_dir)

                output = anylog_conn.get_cmd(conn=conn_info, command=command, authentication=authentication, remote=True,  dest=destination, timeout="", subset=False)

                copied_info.append((file_name, output))

    return copied_info


# -----------------------------------------------------------------------------------
# Keep the user selections
# -----------------------------------------------------------------------------------
def keep_user_selections(select_info):

    global user_selections

    for key, value in user_selections.items():
        if key in select_info:
            # This key was updated
            user_selections[key] = select_info[key]  # Keep the last selections
        else:
            user_selections[key] = None         # No selection


# -----------------------------------------------------------------------------------
# put back the last user selections
# -----------------------------------------------------------------------------------
def restore_user_selections(post_data, select_info):
    global user_selections

    for key, value in user_selections.items():
        if value:
            # This key was updated
            select_info[key] =value  # Keep the last selections


