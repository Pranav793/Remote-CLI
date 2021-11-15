import json

def __format_dict(content:dict)->str:
    """
    Format dictionary content
    :args:
        content:dict - content to format
    :params:
        body:str - formmatted data
    :return:
        body
    """
    body = ''
    for key in content:
        body += "%s: %s" % (key, content[key])
        if key != list(content.keys())[-1]:
            body += " | "
    return body

def error_message(conn:str, command_type:str, error_type:str, error_msg:str)->str:
    """
    Return error message based on arguments provided by user
    :args:
        conn:str - REST connection information
        command_type:str - Type of command executed [ex. GET, PUT, POST]
        error_type:str - Type of error message [ex. Network, formatting, other]
        error_msg:str - Error from exception message
    :return:
        full error message
    """
    if error_type == 'network':
        return "Failed to execute %s against '%s' <br/><b>Network Error<b/>: %s" % (command_type, conn, error_msg)
    elif error_type == 'formatting':
        return "Failed to format %s results against '%s' <br/><b>Error<b/>: %s" % (command_type, conn, error_msg)
    else:
        return "Failed to execute %s against '%s' <br/><b>Error<b/>: %s" % (command_type, conn, error_msg)

def format_content(content:str)->str:
    """

    """
    content = content.split('Content-type: text/json')[-1].split('\n')[-1]
    try:
        content = json.loads(content)
    except:
        body = content
    else:
        if isinstance(content, list):
            body = ''
            for row in content:
                if isinstance(row, dict):
                    body += __format_dict(content=row) + "<br/>\n"
                else:
                    body += row + "<br/>"
        elif isinstance(content, dict):
            body = __format_dict(content=content)

    print(body)
