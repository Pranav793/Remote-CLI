import requests
import anylog.anylog_conn.other as other


def get_cmd(conn:str, command:str, authentication:tuple=(), remote:bool=False)->str:
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
        content:str - what is ultimatly printed to screen
        headers:dict - REST header info
    :return:
        content
    """
    error = None
    results = None
    content = None
    headers = {
        'command': command,
        'User-Agent': 'AnyLog/1.23'
    }

    if remote is True:
        headers['destination'] = 'network'

    try:
        r = requests.get('http://%s' % conn, headers=headers, auth=authentication, timeout=30)
    except Exception as error_msg:
        error = other.error_message(conn=conn, command_type='GET', error_type='other', error_msg=error_msg)
    else:
        if int(r.status_code) != 200:
            error = other.error_message(conn=conn, command_type='GET', error_type='network', error_msg=r.status_code)
        else:
            try:
                results = r.text        # results = r.json()
            except Exception as error_msg:
                error = other.error_message(conn=conn, command_type='GET', error_type='formatting', error_msg=error_msg)

    if results is None:
        content = error
    else:
        try:
            content = other.format_content(content=results)
            # if fails to format in table print raw content
            if '<table style="font-family: arial, sans-serif; border-collapse: collapse;"></table>' == content:
                content = results
        except:
            content = results

    return content


