import requests


def __error_message(conn:str, command_type:str, error_type:str, error_msg:str)->str:
    if error_type == 'network':
        return "Failed to execute %s against '%s' <br/><b>Network Error<b/>: %s" % (command_type, conn, error_msg)
    elif error_type == 'output':
        return "Failed to extract results from '%s' <br/><b>Error<b/>: %s" % (command_type, error_msg)
    else:
        return "Failed to execute %s against '%s' <br/><b>Error<b/>: %s" % (command_type, conn, error_msg)


def get_cmd(conn:str, command:str, authentication:tuple=(), remote:bool=False)->(str, str):
    """
    Execute GET request
    :args:
        conn:str - REST connection info (IP:PORT)
        command:str - command to execute
        authentication:tuple - tuple of username and password if set
        remote:bool - whether to execute remote command (queries)
    :params:
        results:str - content from request
        error:str - if command fails at any point, correlating error
        headers:dict - REST header info
    :return;
        results, error
    """
    error = None
    results = None
    headers = {
       'command': command,
        'User-Agent': 'AnyLog/1.23'
    }

    if remote is True:
        headers['destination'] = 'network'

    try:
        r = requests.get('http://%s' % conn, headers=headers, auth=authentication, timeout=30)
    except Exception as error_msg:
        error = __error_message(conn=conn, command_type='GET', error_type='other', error_msg=error_msg)
    else:
        if int(r.status_code) != 200:
            error = __error_message(conn=conn, command_type='GET', error_type='network', error_msg=r.status_code)
        else:
            try:
                results = r.json()
            except Exception as error_msg:
                try:
                    results = r.text
                except Exception as e:
                    error = __error_message(conn=conn, command_type='GET', error_type='formatting', error_msg=error_msg)

    return results, error