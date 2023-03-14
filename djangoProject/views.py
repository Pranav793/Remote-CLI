import sys
import os

import pyqrcode

# Import necessary modules
from django.shortcuts import render
import webbrowser

from djangoProject.settings import BASE_DIR

import djangoProject.json_api as json_api
import djangoProject.utils_io as utils_io
import djangoProject.anylog_conn.anylog_conn as anylog_conn

json_dir_ = os.path.join(str(BASE_DIR) + os.sep + "djangoProject" + os.sep + "static" + os.sep + "json" + os.sep) # Absolute path
setting_file = os.path.join(str(BASE_DIR) + os.sep + "djangoProject" + os.sep + "static" + os.sep + "json" + os.sep + "settings.json") # Absolute path
pem_dir = os.path.join(str(BASE_DIR) + os.sep + "djangoProject" + os.sep + "static" + os.sep + "pem" + os.sep) # Absolute path to certificates

blobs_dir = os.path.join(str(BASE_DIR) + os.sep + "djangoProject" + os.sep + "static" + os.sep + "blobs" + os.sep + "current"+ os.sep) # Absolute path
keep_dir = os.path.join(str(BASE_DIR) + os.sep + "djangoProject" + os.sep + "static" + os.sep + "blobs" + os.sep + "keep"+ os.sep) # Dir for saved blobs - # Absolute path
blobs_local_dir = "blobs/current/"

m_file_ = None          # Updated with the file name with the monitoring options
monitoring_info_ = None  # The json file with the monitoring info

setting_info_, error_msg = json_api.load_json(setting_file)      # Read the setting.json file

SETTING_CER = {}        # Maintain certificate info
CLIENT_INFO = None      # Maintain client html page defaults
commands_file_name = "commands.json"                        # Default file name for commands

if setting_info_:
    if "certificates" in setting_info_:
        SETTING_CER =  setting_info_["certificates"]
        if not isinstance(SETTING_CER, dict):
            sys.exit('\r\nSetting (certificates) are in a wrong format: %s\r\n' % (setting_file))
    if "client" in setting_info_:
        CLIENT_INFO = setting_info_["client"]
        if not isinstance(CLIENT_INFO, dict):
            sys.exit('\r\nSetting (client) is in a wrong format: %s\r\n' % (setting_file))
        if "buttons" in CLIENT_INFO:
            commands_file_name = CLIENT_INFO["buttons"] # replace "commands.json" with a different name

    if "monitor" in setting_info_:
        # Get the list of files that is with monitoring info
        monitor_files_ = setting_info_["monitor"]
        if len(monitor_files_) and isinstance(monitor_files_, list) and isinstance(monitor_files_[0], list) and len(monitor_files_[0]) == 2:
            m_file_ = monitor_files_[0][1]
            monitoring_info_, error_msg = json_api.load_json(json_dir_ + m_file_)  # R
    else:
        monitor_files_ = None


anylog_conn.set_certificate_info(SETTING_CER, pem_dir)       # Set the certificate info in anylog_conn.py

json_file = json_dir_ + commands_file_name         # Add the default name or the name derived from the setting.js file
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
    for command_ in ANYLOG_COMMANDS:
        for key in must_have_keys:
            # test all keys exists
            if not key in command_:
                if key != "help_url":
                    sys.exit("Missing key: '%s' in commands.json file at entry: %s" % (key, str(command_)))
            if key == "group":
                value = command_[key]
                if not value in COMMANDS_GROUPS:
                    COMMANDS_GROUPS.append(command_[key])


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

user_selections_ = [
        'connect_info',
        'auth_usr',
        'auth_pass',
        'cmd_type',
        'timeout',
        'dbms',
        'table',
        'timezone',
        'out_format',
        'network',
        'destination',
        'command',
        'monitor',
        'm_connect_info',       # Monitor page connect info
        'm_refresh',            # Monitor refresh rate in seconds
]

url_chars_ = {
    ' ': '%20',
    '"': '%22',
    '<': '%3c',
    '>': '%3e',
    '#': '%23',
    '%': '%25',
    '\'': "%27",
    '{': '%7b',
    '}': '%7d',
    '|': '%7c',
    '\\': '%5c',
    '^': '%5e',
    '~': '%7e',
    '[': '%5b',
    ']': '%5d',
    '`': '%60'
}

# ---------------------------------------------------------------------------------------
# GET / POST  AnyLog command form
# ---------------------------------------------------------------------------------------
def form_request(request):

    form = request.POST.get("Form")         # The form used

    blobs_button = request.POST.get("Blobs")    # The blobs button was selected
    config_button = request.POST.get("Config")  # The Config button was selected
    client_button = request.POST.get("Client")  # Client button was selected
    code_button = request.POST.get("Code")      # Create QrCode from the command
    setting_button = request.POST.get("Setting")
    monitor_button = request.POST.get("Monitor")

    if setting_button:
        # Update the setting form (settings.html)
        return setting_options(request)

    form_setting_info(request)      # Get info from the setting form (settings.html - if it was updated)

    if monitor_button:
        # Update the setting form (settings.html)
        return monitor_nodes(request)


    if code_button:
        return code_options(request)

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
# Base64 info - https://stackabuse.com/encoding-and-decoding-base64-strings-in-python/
# ---------------------------------------------------------------------------------------
def blobs_processes(request, blobs_button):

    global keep_dir         # Absolute Path - Saved blobss
    global blobs_dir        # Absolute Path - Copied blobss
    global blobs_local_dir  # "blobs/current/"

    select_info = {}

    transfer_selections(request, select_info)  # Move selections from old form to the current form

    keep_file = False
    delete_file = False
    watch_file = False

    width = 320
    height = 240
    java_class = None

    files_list = []  # A list of files to watch

    post_data = request.POST

    blobs_selected = None

    if blobs_button:
        # blobs_button was selected - Copy the files from the source servers

        blobs_selected = get_blobs(request)      # Copy blobs files from dest machines
        select_info["blobs_selected"] = blobs_selected      # Save the info to apply on Refresh

    else:
        # process the form - delete or move the file

        if "blobs_selected" in post_data:
            blobs_selected = post_data.get('blobs_selected')
            if isinstance(blobs_selected, str):
                blobs_selected, err_msg = json_api.string_to_list(blobs_selected)
                # blobs_selected = ast.literal_eval(blobs_selected)
            if blobs_selected:
                select_info["blobs_selected"] = blobs_selected  # Save the info to apply on Refresh

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
                        index = file_name.rfind('.')
                        if index > 0 and index < (len(file_name) - 1):
                            file_type = file_name[index+1:]
                            if file_type == "msg" or file_type == "blob":
                                # Read the file and add the base64 conversion string
                                disk_data = utils_io.read_file(blobs_dir + file_name)
                                if disk_data:
                                    file_data = "data:image/png;base64," + disk_data
                                else:
                                    file_data = ""
                            else:
                                file_data = ""

                            # Save the files to show: File Name + File Type + The file name + path in the local directory, file data (for png), list of functions (like shape.rect)
                            files_list.append((file_name, file_type,  blobs_local_dir + file_name, file_data, []))

                    if delete_file:
                        utils_io.delete_file(blobs_dir + file_name)
                    elif keep_file:
                        # save the file in the "keep" directory
                        utils_io.copy_file(keep_dir + file_name, blobs_dir + file_name)


    copied_blobs = utils_io.get_files_in_dir(blobs_dir, True)     # Get the list of files that were copied

    functions = {}

    column_names = ["Blobs", "Size"]
    if blobs_selected and len(blobs_selected):
        # add Info from the selected blobs (adding info from the SQL query and the selection using -->  description (columns: ip and bbox as diagram and score)
        # Add IP
        columns_count = 4
        column_names.append("IP")
        for index, selection in enumerate(blobs_selected):
            if not index:
                # On the first selection, update the title
                info_list = selection[2]        # The INfo from the SQL Query
                if len (info_list) > 5:
                    for entry in info_list[5:]:
                        name_val = entry.split('@')     # Split between the nme and the value

                        # Test if the name includes a function (like bbox as shape.rect)
                        name_method = name_val[0].split('*')
                        col_name = name_method[0]
                        if len(name_method) == 2:
                            method_name = name_method[1]

                            functions[col_name] = method_name       # Add the function - like RECTENGALE over a jpeg

                            #select_info["function"] = functions.append(col_name, method_name)   # Add the function - like RECTENGALE over a jpeg

                        column_names.append(col_name[0].upper() + col_name[1:]) # Add the column name without the function (if available after the *, example: bbox as shape.rect)
                        columns_count += 1



                for blob in  copied_blobs:
                    # Add empty fields to all blobs displayed
                    blob.append("")     # For the IP
                    for index in range (4,columns_count):
                        blob.append("")     # For columns specified using: --> description (columns: ip and bbox as shape.rect and score)

            # Find the row an update with the data from the SQL table
            info_list = selection[2]
            ip = info_list[0].split('@')[1]
            dbms_name = info_list[2].split('@')[1]
            table_name = info_list[3].split('@')[1]
            file_name = dbms_name + '.' + table_name + '.' + info_list[4].split('@')[1]  # Same as disk file name
            for file_blob in copied_blobs:
                if file_blob[0].startswith(file_name):       # Because of the .transfer prefix
                    file_blob[2] = ip
                    # Add extra fields
                    if len(info_list) > 5:
                        for index, entry in enumerate(info_list[5:]):
                            name_val = entry.split('@')  # Split between the nme and the value
                            if len (name_val) == 2:
                                value = name_val[1]
                                file_blob[3 + index] = value    # Set the Value from the SQL stmt

                                # Add the functions info if images were selected to display
                                if files_list and len(files_list) == 1:     # If 1 image selected
                                    width = 1600
                                    height = 1200
                                    java_class = "map"
                                    name_func = name_val[0].split('*')
                                    if len (name_func) == 2:
                                        # Include a function like: bbox as shape.rect (bbox*shape.rect)
                                        function = name_func[1]
                                        for selected_file in files_list:
                                            if selected_file[0].startswith(file_name):
                                                if function.startswith("shape."):
                                                    if value:
                                                        # If coordinates are provided
                                                        if value[0] == "[" and value[-1] == "]":
                                                            value = value[1:-1].strip()     # remove paren
                                                        selected_file[4].append((function, value))  # Add bbox*shape.rect + value
                                                break
                    break



    # Go to the page - blobs.html

    select_info["width"] = width
    select_info["height"] = height
    select_info["class"] = java_class

    select_info["functions"] = functions        # Apply a function like a rectangle over the image

    column_names.append("Select")
    select_info["column_names"] = column_names

    select_info["rows"] = copied_blobs          # The files in the directory placed in a selection list

    select_info["watch"] = files_list           # The files selected to watch


    return render(request, "blobs.html", select_info) # Process the blobs page

# ---------------------------------------------------------------------------------------
# Client processes - the main form interacting with the network
# ---------------------------------------------------------------------------------------
def client_processes(request, client_button):

    selection_output = False
    get_columns = None
    get_descr = None
    send_button = request.POST.get("Send")

    # Check the form is submitted or not
    if not client_button and request.method == 'POST' and send_button:
        # SEND THE COMMAND TO DESTINATION NODE

        user_cmd = request.POST.get("command").strip()
        if len(user_cmd) > 5 and user_cmd[:4].lower() == "sql ":
            query_result = True


            user_cmd, selection_output, get_columns, get_descr = get_additional_instructions(user_cmd)
        else:
            query_result = False

        # Process the command
        output = process_anylog(request, user_cmd, False)        # SEND THE COMMAND TO DESTINATION NODE


        return print_network_reply(request, query_result, output, selection_output, get_columns, get_descr)

    else:
        # Display the html form

        command_button = request.POST.get("button")
        if command_button:
            select_info = command_button_selected(request, command_button)
        else:
            select_info = {}
            transfer_selections(request, select_info)   # Move selections from old form to the current form

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


        return render(request, "base.html", select_info)

# ---------------------------------------------------------------------------------------
# Additional instruction in the command line identified by: -->
# Example:
# sql ntt extend=(+node_name, @ip, @port, @dbms_name, @table_name) and format = json and timezone = utc  select  file, class, bbox, score, status  from deeptector where score > 0   order by score
# --> selection (columns: ip using ip and port using port and dbms using dbms_name and table using table_name and file using file) --> description (columns: ip, class, bbox as diagram, score)
# ---------------------------------------------------------------------------------------
def get_additional_instructions(user_cmd):

    selection_output = False
    get_columns = None
    descr_info = None
    updated_command = None

    commands_list = user_cmd.split("-->")

    if len(commands_list) == 1:
        updated_command = commands_list[0].strip()
    if len(commands_list) > 1:
        updated_command = commands_list[0].strip()

        for instruction in commands_list[1:]:

            instruct = instruction.strip()
            if instruct.startswith("selection"):
                if len(instruct) > 12:
                    instruct = instruct[9:].strip()[1:-1]       # Remove the parenthesis of the selected columns
                    selection_output, get_columns = get_file_copy_info(instruct)    # The info needed to copy a blob
            elif instruct.startswith("description"):
                if len(instruct) > 13:
                    instruct = instruct[11:].strip()[1:-1]       # Remove the parenthesis of the selected columns
                    descr_info = get_descr_info(instruct)        # info to show with blob data

    return  [updated_command, selection_output, get_columns, descr_info]

# ---------------------------------------------------------------------------------------
# Process the following:  -->  description (columns: ip and bbox as diagram and score)
# ---------------------------------------------------------------------------------------
def get_descr_info(descr_cmd):
    descr_list = []
    if descr_cmd.startswith("columns: "):
        paren_info = descr_cmd[9:].strip()
        columns_list = paren_info.split("and")
        for column in columns_list:
            column = column.strip()
            column_sections = column.split(" as ")
            if len(column_sections) == 1:
                descr_list.append([column , None])      # Column name
            elif len(column_sections) == 2:
                descr_list.append([column_sections[0].rstrip(), column_sections[1].lstrip()])  # Column name

    return descr_list
# ---------------------------------------------------------------------------------------
# If the query is an input to a file copy - get the column name that holds the file name
# Process the following:  --> selection (columns: ip using ip and port using port and file using file)
# ---------------------------------------------------------------------------------------
def get_file_copy_info(selection_cmd):
    '''
    user_cmd - provided by the user

    return:
        command - the command without the suffix: > (file id in column file)
        selection_output - bool to determine if redirection exists
        id_column - the column that includes the id of the file (Hash value or file name)
    '''

    get_columns = ["ip", "port", "dbms", "table", "file", "date"]  # These are the info that is needed to bring the blobs

    pull_columns = {}           # Columns to leverage in pulling the image
    query_columns = None
    selection_output = True
    # Get the column name
    # The format is (columns: ip using [column name of ip] and port using [column name of port] and file using [column name of file])
    if selection_cmd.startswith("columns: "):
        paren_info = selection_cmd[9:].strip()
        columns_list = paren_info.split("and")
        # needs to describe IP, Port, file name, table name, File Name (or Hash)

        for entry in columns_list:
            column_info = entry.strip().split()     # X using [column name]
            if len(column_info) != 3 or column_info[1] != "using":
                selection_output = False
                break
            try:
                index = get_columns.index(column_info[0])
            except:
                selection_output = False
                break
            pull_columns[get_columns[index]] = column_info[2] # Keep  THE COLUMN NAME TO MACH THE QUERY COLUMN NAME

        if selection_output:
            # Test if all columns are detailed in the query
            # Note: date is optional - it is used to find the file if stored in a file system
            for column_name in get_columns:
                if not column_name in pull_columns:
                    if column_name != "date":       # DATE is optional
                        selection_output = False
                        break

            if selection_output:
                query_columns = list(pull_columns.values())


    return [selection_output, query_columns]

# ---------------------------------------------------------------------------------------
# Command button was selected - get the command info and set the command on select_info
# so it can be placed on the command line
# ---------------------------------------------------------------------------------------
def command_button_selected(request, command_button):
    '''
    Return a select_info structure with the info selected by the button
    '''
    select_info = {}


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

        if setting_info_ and "client" in setting_info_ and "help" in setting_info_["client"]:
            help_type = setting_info_["client"]["help"]     # Should be url (show the url) or open (open the url)
        else:
            help_type = "url"       # Default show the URL
        if help_type == "open":
            webbrowser.open(help_url)               # Form will open the help page
        else:
            select_info["help_url"] = help_url      # Form will print URL
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
def process_anylog(request, user_cmd, is_monitored):
    '''
    :param request: The info needed to execute command to the AnyLog network
    :param user_cmd: The command issued by the user - it appears in requests (request.POST.get("command")), but maybe was modified by the caller
    :return: The data to display on the output form
    '''

    post_data = request.POST

    # Get the needed info from the form
    if is_monitored:
        conn_info = post_data.get('m_connect_info')
        username = post_data.get('m_auth_usr')
        password = post_data.get('m_auth_pass')
    else:
        conn_info = post_data.get('connect_info')
        username = post_data.get('auth_usr')
        password = post_data.get('auth_pass')

    conn_info = conn_info.strip() if conn_info != None else ""
    username = username.strip() if username != None else ""
    password = password.strip() if password != None else ""


    command = user_cmd

    timeout = post_data.get('timeout').strip()  # Change default timeout
    subset = post_data.get('subset') == "on" # Returns reply even if not oll nodes replied

    if is_monitored:
        # Ignore the network flag - always on the local node
        network = False
    else:
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
        output = "Missing command"

    return output     # Data returned from AnyLog or an Error Message
# -----------------------------------------------------------------------------------
# Print network reply -
# Option 1 - a tree
# Option 2 - a table
# Option 3 - text
# -----------------------------------------------------------------------------------

def print_network_reply(request, query_result, data, selection_output, get_columns, get_descr):
    '''
    request - the form info
    query_result - a True/False value representing SQL query data set returned
    data - the query or command result
    selection_output - user issued a SQL statement with "> selection" at the end - indicating output to a selection table
    get_columns - the name of the columns that includes the IP, Port, dbms name and file name to retrieve he file
    get_descr - additional columns to describe the blobs

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
            return render(request, 'output_tree.html', select_info)

        print_info = [("text", data)]  # Print the error msg as a string
    elif is_complex_struct(data):
        print_info = [("text", data)]   # Keep as is
    else:
        policies, table_info, print_info, error_msg = format_message_reply(data)
        if policies:
            if selection_output:
                # Show as a selection table
                return json_to_selection_table(request, select_info, policies, get_columns, get_descr)

            else:
                # Reply was a JSON policies or a query replied in JSON
                data_list = []
                json_api.setup_print_tree(policies, data_list)
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


    select_info['text'] = [("text", data)]        # Only TEXT
    return render(request, 'output_cmd.html', select_info)

# -----------------------------------------------------------------------------------
# Output to selection table
# Change the query reply from JSON to selection table format and call the report
# Example:
# sql ntt extend=(+node_name, @ip, @port, @dbms_name, @table_name) and format = json and timezone = utc  select  file, class, bbox, score, status  from deeptector where score > 0   order by score --> selection (columns: ip using ip and port using port and dbms using dbms_name and table using table_name and file using file) -->  description (columns: ip and bbox as diagram and score)
# -----------------------------------------------------------------------------------
def json_to_selection_table(request, select_info, returned_data, get_columns, get_descr):

    # Show as a selection table
    '''
    select_info - info directing the page
    returned_data - the data returned from the network
    id_column - the name of the column that includes the file name
    get_columns - the list of columns needed to retieve the blobs
    get_descr - additional columns to describe the blobs
    '''
    needed_columns = ["+ip@", "+port@", "+dbms@", "+table@", "+file@", "+date@"]


    data_list = returned_data["Query"]

    one_policy = data_list[0]
    column_names = []

    # Get the returned column names from the first returned policy
    for column_id, attr_name in enumerate(one_policy.keys()):
        column_names.append(attr_name)

    select_info['column_names'] = column_names

    # for each policy - get 1) the data returned on selection and 2) the data to show the user
    rows = []
    for json_data in data_list:

        # THE INFO TO NEEDED TO BRING THE BLOB DATA (IP + PORT + DBMS + TABLE + FILE ID
        selection = ""      # Set the data returned when selected
        try:
            for index, column_name in enumerate(get_columns):   # get columns include the columns names on the returned data
                value = json_data[column_name]
                if index < len(needed_columns):
                    selection += needed_columns[index] + value
                else:
                    break   # needed data
        except:
            pass    # No sufficient info

        columns_val = []        # Collect the column values to display
        for attr_val in json_data.values():
            columns_val.append(attr_val)

        # ADDITIONAL FILE DESCRIPTION INFO
        description = ""
        if get_descr:
            for column_info in get_descr:
                # in the --> description, get the list of columns to use + the method to apply
                col_name = column_info[0]
                if col_name in json_data:
                    method_name = column_info[1]     # Method to apply with the col value (like BOX/RECTENGALE over the coordinates)
                    description += ("+" + col_name)
                    if method_name:
                        description += ("*" + method_name)
                    description += ('@' + str(json_data[col_name]))

        rows.append([columns_val, selection + description])       # The info on the columns transferred to the report

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
    if  "rest_call" in select_info and select_info["rest_call"] == "post":
        select_info["rest_call"] = None
    else:
        select_info["rest_call"] = "get"
    if  "out_format" in select_info and select_info["out_format"] == "json":
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
    conn_info = post_data.get('connect_info')
    if conn_info:
        conn_info = conn_info.strip()

    try:
        authentication = anylog_conn.get_auth(request)
    except:
        authentication = None

    # Search for selected files

    copied_info = []        # Collect the files copied and the message if an error happened

    for entry in post_data:
        if entry.startswith("get@+"):
            operator_ip = ""
            operator_port = ""
            operator_dbms = ""
            operator_table = ""
            operator_file = ""
            file_date = ""

            entry_list = entry[5:].split('+')

            if len(entry_list) >= 5: # Organized with IP and Port and File-Name and DBMS
                # Get the blobs file operator info and file name
                for part in entry_list:         # Consider IP + Port + DBMS + Table + File
                    if part.startswith("ip@"):
                        operator_ip = part[3:]
                    elif part.startswith("port@"):
                        operator_port = part[5:]
                    elif part.startswith("dbms@"):
                        operator_dbms = part[5:]
                    elif part.startswith("table@"):
                        operator_table = part[6:]
                    elif part.startswith("file@"):
                        operator_file = part[5:]
                    elif part.startswith("date@"):
                        file_date = part[5:]        # Needed if file is not in a database - the date determines location on the file system


                info_needed = True
                if operator_ip and operator_port:
                    destination = "%s:%s" % (operator_ip, operator_port)
                else:
                    info_needed = False

                if operator_dbms and operator_file:
                    command = f"file get (dbms = blobs_{operator_dbms} and table = {operator_table} and id = {operator_file}"
                    if file_date:
                        # Needed if file is not in a database - the date determines location on the file system - add the date to retrieve from the date folder
                        command += f" and date = {file_date}"
                    command+= f") {blobs_dir}{operator_dbms}.{operator_table}.{operator_file}"  # Add file full path and name for the destination on THIS MACHINE
                else:
                    info_needed = False

                if info_needed:
                    output = anylog_conn.get_cmd(conn=conn_info, command=command, authentication=authentication, remote=True,  dest=destination, timeout="", subset=False)

                copied_info.append((operator_file, output, entry_list))

    return copied_info


# -----------------------------------------------------------------------------------
# Keep the user selections = move the previous form selections to the current form
# -----------------------------------------------------------------------------------
def transfer_selections(request, select_info):
    '''
    request - the previous form selections
    select_info - current form data
    '''

    global user_selections_     # The entries to pass from form to form
    global CLIENT_INFO          # Defaults from the setting.json file

    previous_form = request.POST

    for entry in user_selections_:
        if entry in previous_form:
            # This key was updated
            select_info[entry] = previous_form[entry]  # info passed to the new form
        else:
            if CLIENT_INFO and entry in CLIENT_INFO:
                select_info[entry] = CLIENT_INFO[entry]  # info passed to the new form from "setting.json" file

    if not "m_connect_info" in select_info and "connect_info" in select_info:
        # Use the default select info
        select_info["m_connect_info"] = select_info["connect_info"]

# -----------------------------------------------------------------------------------
# Query Options:
# QR Code
# AnyLog command
# cURL command
# -----------------------------------------------------------------------------------
def code_options(request):

    select_info = {}

    make_qrcode(request, select_info)

    make_anylog_cmd(request, select_info)

    make_curl_cmd(request, select_info)

    return render(request, "code_options.html", select_info)  # Process the blobs page

# -----------------------------------------------------------------------------------
# Make curl command in the format: curl --location --request GET 'http://10.0.0. ...
# -----------------------------------------------------------------------------------
def make_curl_cmd(request, select_info):

    post_data = request.POST

    curl_cmd = "curl --location --request "

    rest_call = post_data.get('rest_call')
    if rest_call == "post":
        curl_cmd += "POST "
    else:
        curl_cmd += "GET "

    conn_info = post_data.get('connect_info').strip()

    curl_cmd += f"http://{conn_info} "

    curl_cmd += "--header \"User-Agent: AnyLog/1.23\" "

    user_cmd = post_data.get("command").strip()

    if '"' in user_cmd:
        wind_cmd = user_cmd.replace('"', '""')  # Set double quotes in windows
        wind_curl_cmd = curl_cmd +  f"--header \"command: {wind_cmd}\" "
    else:
        wind_curl_cmd = None

    linux_cmd = user_cmd.replace('"', '\\"')  # Set double quotes in windows
    curl_cmd += f"--header \"command: {linux_cmd}\" "
    network = post_data.get('network') == "on"
    if network:
        destination = post_data.get('destination').strip()
        if not destination:
            destination = "network"

        curl_cmd += f"--header \"destination: {destination}\" "

        if wind_curl_cmd:
            wind_curl_cmd += f"--header \"destination: {destination}\" "

    select_info["curl_cmd"] = curl_cmd

    if wind_curl_cmd:
        select_info["win_curl_cmd"] = wind_curl_cmd     # Windows command - replacing quotation with 2 sets: " --> ""


# -----------------------------------------------------------------------------------
# Make anylog command in the format: run client ...
# -----------------------------------------------------------------------------------
def make_anylog_cmd(request, select_info):

    user_cmd = request.POST.get("command").strip()
    if len(user_cmd) > 5 and user_cmd[:4].lower() == "sql ":
        user_cmd, selection_output, get_columns, descr_info = get_additional_instructions(user_cmd)

    network = request.POST.get('network') == "on"
    if network:
        destination =  request.POST.get('destination').strip()
        if destination:
            user_cmd = "run client (%s) %s" % (destination, user_cmd)
        else:
            user_cmd = "run client () %s" % (user_cmd)

    select_info["user_cmd"] = user_cmd

# -----------------------------------------------------------------------------------
# Make QR code - update the url string
# pypng - required to install but not import
# Info at https://pythonhosted.org/PyQRCode/moddoc.html
# -----------------------------------------------------------------------------------
def make_qrcode(request, select_info):


    transfer_selections(request, select_info)       # Move selections from the previous fom to the current form

    html_img = ""
    qrcode_command = ""     # The final command structure


    conn_info = request.POST.get('connect_info')
    if conn_info:
        conn_info = conn_info.strip()

    url_string = f"http://{conn_info}/?User-Agent=AnyLog/1.23"


    username = request.POST.get('auth_usr')
    if username:
        username = username.strip()

    password = request.POST.get('auth_pass')
    if password:
        password = password.strip()


    if request.POST.get('network') == "on":
        destination = request.POST.get('destination').strip()
        if not destination:
            destination = "network"
        url_string += f"?destination={destination}"


    url_string += '?command='
    user_command = request.POST.get("command")
    if user_command:
        url_string += user_command.strip()

    url_encoded = update_url(url_string)

    try:
        qrcode = create_qr(url_encoded)
    except:
        pass
    else:
        try:
            image_as_str = qrcode.png_as_base64_str(scale=5)
        except:
            pass
        else:

            qrcode_command = url_string       # The command that is in the qrcode
            html_img = "data:image/png;base64,{}".format(image_as_str)

    select_info["qr_cmd"] = qrcode_command
    select_info["qrcode"] = html_img  # The files to watch
    select_info["url"] = url_encoded


# -----------------------------------------------------------------------------------
# Make QR code - update the url string
# -----------------------------------------------------------------------------------
def update_url(command:str)->str:
    """
    replace characters according to the url_chars_ dictionary
    """
    qr_string = ""
    for char in command:
        if char in url_chars_:
            qr_string += url_chars_[char]
        else:
            qr_string += char
    return qr_string
# -----------------------------------------------------------------------------------
# Create the QR code
# pypng - required to install but not import
# -----------------------------------------------------------------------------------
def create_qr(url:str='https://anylog.co')->pyqrcode.QRCode:
    """
    Create QR code
    :args:
        url:str - URL correlated to QR
    :params:
        qrcode:pyqrcode.QRCode - Generated QR based on URL
    :return:
        qrcode
    """
    qrcode = None
    try:
        qrcode = pyqrcode.create(url)
    except Exception as error:
        print(f'Failed to create QR code (Error: {error})')

    return qrcode

# -----------------------------------------------------------------------------------
# Setting Options like ssl - Enter into setting Form
# -----------------------------------------------------------------------------------
def setting_options(request):

    global m_file_

    select_info = {}

    transfer_selections(request, select_info)  # Move selections from old form to the current form

    certificate_info = anylog_conn.get_certificate_info()   # Get the certificate setting info

    pem_file = certificate_info["pem_file"]
    if pem_file:
        select_info["pem_file"] = pem_file
    crt_file = certificate_info["crt_file"]
    if crt_file:
        select_info["crt_file"] = crt_file
    key_file = certificate_info["key_file"]
    if key_file:
        select_info["key_file"] = key_file
    enable =  certificate_info["enable"]
    if enable:
        select_info["certificate"] = True

    if monitor_files_:
        # A json file name with the monitoring info
        select_info["monitor_files"] = monitor_files_
        if m_file_:
            select_info["m_file"] = m_file_     # Last file selected


    return render(request, "settings.html", select_info)  # Process the blobs page

# -----------------------------------------------------------------------------------
# Setting Options like ssl - Exit from setting Form
# -----------------------------------------------------------------------------------
def form_setting_info(request):

    global m_file_      # The name of the monitoring file
    global monitoring_info_ # The json file with the monitoring info
    global json_dir_

    certificate_info = anylog_conn.get_certificate_info()
    post_data = request.POST
    if post_data.get("certificate"):
        enable = post_data.get("certificate")
        if enable and enable == "on":
            certificate_info["enable"] = True
        else:
            certificate_info["enable"] = False
    if post_data.get("pem_file"):
        pem_file = post_data.get("pem_file")
        if pem_file:
            certificate_info["pem_file"] = pem_file
    if post_data.get("crt_file"):
        crt_file = post_data.get("crt_file")
        if crt_file:
            certificate_info["crt_file"] = crt_file
    if post_data.get("key_file"):
        key_file = post_data.get("key_file")
        if key_file:
            certificate_info["key_file"] = key_file

    if post_data.get("m_file"):     # A file name for monitoring
        file_name = post_data.get("m_file")
        if not m_file_ or file_name != m_file_:
            # Load the JSON file with the monitoring info
            m_file_ = file_name
            monitoring_info_, error_msg = json_api.load_json(json_dir_ + file_name)  # Read the setting.json file


# -----------------------------------------------------------------------------------
# Monitor data from aggregator node
# -----------------------------------------------------------------------------------
def monitor_nodes(request):

    global monitoring_info_

    select_info = {}

    transfer_selections(request, select_info)  # Move selections from old form to the current form

    m_refresh = 0        # The screen refresh rate in ms

    if monitoring_info_ and isinstance(monitoring_info_,dict):
        # Test if dictionary
        if "views" in monitoring_info_:
            # get all monitoring reports keys + names
            views = monitoring_info_["views"]
            views_list = []         # A list with all the monitoring pages definitions
            if isinstance(views, dict):
                for key, value in views.items():
                    if isinstance(value, dict):
                        if "title" in value:
                            views_list.append((value["title"], key))

                select_info["pages"] = views_list           # ALl the options for monitoring pages

                collection_key = request.POST.get("collection")
                if collection_key and "m_connect_info" in select_info:
                    select_info["collection"] = collection_key
                    monitor_instruct = views[collection_key]        # The info of interest to display

                    # Pull from the aggregator node
                    output= process_anylog(request, "get monitored %s" % collection_key, True)
                    if output:
                        json_struct, error_msg = json_api.string_to_json(output)
                        if json_struct:
                            organize_monitor_info(select_info, monitor_instruct, json_struct) # Organize the output in a table structure
                            if "m_refresh" in select_info:
                                try:
                                    m_refresh = int(select_info["m_refresh"])    # The screen refresh rate in ms
                                except:
                                    m_refresh = 0


    # Set the refresh rate on the monitor and for the script in MS
    select_info["m_refresh"] = m_refresh
    refresh_ms = m_refresh * 1000
    select_info["refresh_ms"] = refresh_ms                      # Transfer the refresh rate in MS or 0 for none

    return render(request, "monitor.html", select_info)  # Process the blobs page

# -----------------------------------------------------------------------------------
# Organize the monitored info for the form
# -----------------------------------------------------------------------------------
def organize_monitor_info(select_info, instruct_tree, json_struct):
    '''
    instruct - the instructions of what to present
    json_struct - the info returned from the aggregator node
    '''
    if json_struct:
        # Transform the JSON to a table
        table_data = {}
        table_rows = []
        column_names_list = []
        totals = None
        alerts = None
        if 'header' in instruct_tree:
            # User specified (in config file) columns to display
            column_names_list = instruct_tree['header']
            select_info['header'] = column_names_list
        if 'totals' in instruct_tree:
            totals = instruct_tree['totals']
        if 'alerts' in instruct_tree:
            alerts = instruct_tree['alerts']  # Test values as arrive

        if not len(column_names_list):
            # Get the columns names from the JSON data
            column_names_list.append("Node")
            # take all columns from the json
            for node_name, node_info in json_struct.items():
                # Key is the node name and value is the second tier dictionary with the info
                for attr_name in node_info:
                    # The keys are the column names
                    if attr_name not in column_names_list:
                        column_names_list.append(attr_name)

        select_info['header'] = column_names_list

        if totals:
            totals_row = []
            # Set an entry for each total
            for column_name in column_names_list:
                if column_name in totals:
                    totals_row.append(
                        [0, False, True])  # Values: Accumulates the total, Alert is false and shift_right is True
                else:
                    totals_row.append(["", False, False])  # Print empty cell

        # Get the columns values
        for node_ip, node_info in json_struct.items():
            # Key is the node name and value is the second tier dictionary with the info
            if node_ip == "Update time":
                continue
            row_info = []
            if column_names_list[0] == "Node":
                row_info.append((node_ip, False))  # First column is node name
            for index, column_name in enumerate(column_names_list[1:]):
                if column_name in node_info:
                    column_value = node_info[column_name]
                    if column_value == None:
                        row_info.append(("", False))
                        continue

                    if isinstance(column_value, int):
                        data_type = "int"
                        shift_right = True  # Shift right in the table cell
                        formated_val = "{:,}".format(column_value)
                    elif isinstance(column_value, float):
                        data_type = "float"
                        shift_right = True  # Shift right in the table cell
                        formated_val = "{0:,.2f}".format(column_value)
                    else:
                        data_type = "str"
                        shift_right = False  # Shift left in the table cell
                        formated_val = str(column_value)
                        if not formated_val:
                            row_info.append(("N/A", True, False,
                                             False))  # "N/A" - The value to print, is alert, shift, the last False means warning (True means alert - impacts the color)
                            continue  # Empty string

                    if totals:
                        if totals_row[index + 1][0] != "":
                            try:
                                if data_type != "str":
                                    totals_row[index + 1][0] += column_value
                                elif column_value.is_digit():
                                    totals_row[index + 1][0] += int(column_value)
                                else:
                                    totals_row[index + 1][0] += float(column_value)
                            except:
                                pass

                    alert_val = False
                    if alerts:
                        # if column_name in alerts --> process alert to change display color
                        if column_name in alerts:
                            alert_code = alerts[column_name].replace("value", str(column_value))
                            try:
                                alert_val = eval(alert_code)
                            except Exception as err_msg:
                                pass
                            else:
                                if alert_val:
                                    # Change color of display
                                    pass

                    row_info.append((formated_val, alert_val, shift_right,
                                     True))  # The value to print, is alert, shift, the last True means Alert (False means warning - impacts the color)

                else:
                    row_info.append(("", False))

            table_rows.append(row_info)

        if totals:
            for entry in totals_row:
                if isinstance(entry[0], int):
                    entry[0] = "{:,}".format(entry[0])
                elif isinstance(entry[0], float):
                    entry[0] = "{0:,.2f}".format(entry[0])

            table_rows.append(totals_row)

        select_info['rows'] = table_rows