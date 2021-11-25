import requests
import anylog_query.anylog_conn.other as other


def get_cmd(conn:str, command:str, authentication:tuple=(), remote:bool=False, dest:str = "")->str:
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
    results = None

    headers = {
        'command': command,
        'User-Agent': 'AnyLog/1.23'
    }

    if remote is True:
        if dest:
            # a comma seperated IP and Ports
            headers['destination'] = dest
        else:
            headers['destination'] = 'network'

    try:
        r = requests.get('http://%s' % conn, headers=headers, auth=authentication, timeout=30)
    except Exception as error_msg:
        results = other.error_message(conn=conn, command_type='GET', error_type='other', error_msg=error_msg)
    else:
        if int(r.status_code) != 200:
            results = other.error_message(conn=conn, command_type='GET', error_type='network', error_msg=r.status_code)
        else:
            try:
                results = r.text        # results = r.json()
            except Exception as error_msg:
                results = other.error_message(conn=conn, command_type='GET', error_type='formatting', error_msg=error_msg)

    return results



def post_cmd(conn:str, command:str, authentication:tuple=())->str:
    """
    Execute POST command
    :args:
        conn:str - REST connection info (IP:PORT)
        command:str - command to execute
        authentication:tuple - tuple of username and password if set
    :params:
        output:str - content to return
         headers:dict - REST header info
    :return:
        if fails return error message, else return "Success!"
    """

    headers = {
        'command': command,
        'User-Agent': 'AnyLog/1.23'
    }

    try:
        r = requests.post('http://%s' % conn, headers=headers, auth=authentication)
    except Exception as error_msg:
        output = other.error_message(conn=conn, command_type='POST', error_type='other', error_msg=error_msg)
    else:
        if int(r.status_code) != 200:
            output = other.error_message(conn=conn, command_type='POST', error_type='network', error_msg=r.status_code)
        else:
            output = 'Success!'

    return output




