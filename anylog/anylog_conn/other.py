import json

def __table_column_headers(content_keys:list)->str:
    """
    Create column names
    :args:
        content_keys:list - list of columns (in order)
    :params:
        body:str - columns table
    """
    body = ''
    for column in content_keys:
        body += '<th style="border: 1px solid #dddddd; text-align: left; padding: 8px;">%s</th>' % (column)

    return body

def __table_column_values(content:dict)->str:
    """
    Format dictionary content
    :args:
        content:dict - content to format
    :params:
        body:str - formmatted data
    :return:
        body
    """
    body = '<tr>'
    for key in content:
        body += '<td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">%s</td>' % content[key]
    body += '</tr>'

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
        return "Failed to execute %s against '%s' (Network Error: %s)" % (command_type, conn, error_msg)
    elif error_type == 'formatting':
        return "Failed to format %s results against '%s' (Error: %s)" % (command_type, conn, error_msg)
    else:
        return "Failed to execute %s against '%s' (Error: %s)" % (command_type, conn, error_msg)

def format_content(content:str)->str:
    """
    Format content data
    :args:
        content:str - raw content from request
    :params;
        body:str - contnet to be printed
    :return:
        body
    """
    column_names = False
    content = content.split('Content-type: text/json')[-1].split('\n')[-1]
    try:
        content = json.loads(content)
    except Exception:
        body = content
    else:
        if isinstance(content, list):
            body = ''
            for row in content:
                if isinstance(row, dict):
                    if column_names is False:
                        body += __table_column_headers(row)
                        column_names = True
                    body += __table_column_values(row)

    return '%s' % body
