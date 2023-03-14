import requests
import djangoProject.anylog_conn.other as other


cert_info_ = None       # Info at https://docs.python-requests.org/en/latest/user/advanced/

def set_certificate_info(cert_info, pem_dir):
    """
    Keep a global param with the certificate info
    """
    global cert_info_
    cert_info_ = cert_info

    cert_info_["pem_dir"] = pem_dir           # Default dir for certificates

    if not "pem_file" in cert_info_:
        cert_info_["pem_file"] = ""
    if not "crt_file" in cert_info_:
        cert_info_["crt_file"] = ""
    if not "key_file" in cert_info_:
        cert_info_["key_file"] = ""
    if not "enable" in cert_info_:     # Needs to be True to enable certificates
        cert_info_["enable"] =  False  # default

def get_certificate_info():
    global cert_info_
    return cert_info_

def get_cmd(conn:str, command:str, authentication:tuple=(), remote:bool=False, dest:str = "", timeout:str="", subset:bool=False)->str:
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
    global cert_info_

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

    if timeout:
        headers['timeout'] = timeout        # Change default timeout on the AnyLog Node
        try:
            client_timeout = int(timeout) + 5        # Add 5 sec to the node timeout for the browser to checkout
        except:
            client_timeout = 30             # Revert to the default
    else:
        client_timeout = 30                 # Default browser/client timeout

    if subset:
        headers['subset'] = str(subset)          # Return info even if not all replied


    try:
        if cert_info_["enable"] :
            pem_file = cert_info_["pem_file"]   # File name on the AnyLog Node
            crt_file = cert_info_["pem_dir"] + cert_info_["crt_file"]  # Add Path
            key_file = cert_info_["pem_dir"] + cert_info_["key_file"]  # Add Path
            # https://docs.python-requests.org/en/latest/user/advanced/
            r = requests.get('https://%s' % conn, headers=headers, auth=authentication, timeout=client_timeout, verify=False,  cert=(crt_file, key_file))
        else:
            r = requests.get('http://%s' % conn, headers=headers, auth=authentication, timeout=client_timeout)
    except Exception as error_msg:
        results = other.error_message(conn=conn, command_type='GET', error_type='other', error_msg=error_msg)
    else:
        if int(r.status_code) != 200:
            try:
                results = r.reason        # results = r.json()
            except Exception as error_msg:
                results = other.error_message(conn=conn, command_type='GET', error_type='network', error_msg=r.status_code)
        else:
            try:
                results = r.text        # results = r.json()
            except Exception as error_msg:
                results = other.error_message(conn=conn, command_type='GET', error_type='formatting', error_msg=error_msg)

    return results



def post_cmd(conn:str, command:str, authentication:tuple=(), msg_data:str = None)->str:
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
        'User-Agent': 'AnyLog/1.23',
        "command" : command
    }

    try:
        r = requests.post('http://%s' % conn, headers=headers, data=msg_data, auth=authentication)
    except Exception as error_msg:
        output = other.error_message(conn=conn, command_type='POST', error_type='other', error_msg=error_msg)
    else:
        if int(r.status_code) != 200:
            output = other.error_message(conn=conn, command_type='POST', error_type='network', error_msg=r.status_code)
        else:
            output = 'Success!'

    return output


def get_auth(request):
    '''
    Get the Authentication info from the form info
    '''

    post_data = request.POST

    # Get the needed info from the form
    username = post_data.get('auth_usr').strip()
    password = post_data.get('auth_pass').strip()

    authentication = ()
    if username != '' and password != '':
        authentication = (username, password)

    return authentication


