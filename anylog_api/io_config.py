import configparser
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)).rsplit('anylog_conn', 1)[0], "/config/new-config.ini")

def read_configs(config_file:str=CONFIG_FILE)->dict:
    """
    Read configs from file & set values wthin them for Docker env params
    :args:
        config_file:str - config file to read
    :params:
        data:dict - content from config file
        parser:configparser.configparser.ConfigParser - configuration parser
    :return:
        if success return data, else return an error
    """
    data = {}
    if not os.path.isfile(config_file):
        return "Error: Unable to locate file '%s'" % config_file

    try:
        parser = configparser.ConfigParser()
    except Exception as e:
        return 'Error: Unable to create config parser object (Error: %s)' % e

    try:
        parser.read(config_file)
    except Exception as e:
        return "Error: Failed to read config file '%s' (Error: %s)" % (config_file, e)

    try:
        for section in parser.sections():
            for key in parser[section]:
                data[key.upper()] = parser[section][key].replace('"', '')
    except Exception as e:
        return "Failed to extract variables from config file '%s' (Error: %s)" % (config_file, e)

    return data


def write_configs(config_data:dict, config_file:str=CONFIG_FILE)->str:
    """
    Write configurations to file
    :args:
        config_data:dict - content to write to file
        config_file:str - file to write content into
    :params:
        parser:configparser.configparser.ConfigParser - configuration parser
    :return:
        error otherwise None
    """
    config_file = os.path.expandvars(os.path.expanduser(config_file))
    output = None
    # create file if DNE
    if not os.path.isfile(config_file):
        try:
            open(config_file, 'w').close()
        except Exception as e:
            return 'Error: Unable to create file %s (Error: %s)' % (config_file, e)
    try:
        parser = configparser.ConfigParser()
    except Exception as e:
        return 'Error: Unbale to set parser for setting configs (Error: %s)' % e

    try:
        for section in config_data:
            parser.add_section(section)
            for key in config_data[section]:
                if config_data[section][key] != '' and config_data[section][key] != None:
                    parser.set(section, key, config_data[section][key])
    except Exception as e:
        return 'Error: Failed to add content into file (Error: %s)' % e

    try:
        with open(config_file, 'w') as confil:
            try:
                parser.write(confil)
            except Exception as e:
                return 'Error: Failed to write content into %s (Error: %s)' % (config_file, e)
    except Exception as e:
        return 'Error: Failed to open %s for content to be written (Error: %s)' % (config_file, e)

    return None


def validate_config(env_params:dict)->(bool, list):
    """
    validate configuration values
    :args:
        env_params:dict - configuration
    :params:
        status:bool
        params:list - list of missing params
    :return;
        status
    """
    status = True
    errors = []
    config = dict((key.lower(), value) for key, value in env_params.items())

    # Base required params
    for key in ['build', 'node_type', 'node_name']:
        if key not in list(config.keys()):
            errors.append('Missing configuration param: %s' % key)
            status = False

    if 'node_type' in list(config.keys()) and config['node_type'] not in ['none', 'rest', 'master', 'operator', 'publisher', 'query', 'single-node', 'single-node-publisher']:
        errors.append("Invalid node type '%s'" % config['node_type'])
        status = False 
        
    if status is False or config['node_type'] == 'none':
        return status, errors

    # parameters that exist in node types: master, operator, publisher and query
    for key in ['company_name', 'master_node', 'anylog_tcp_port', 'anylog_rest_port', 'db_type', 'db_user', 'db_port']:
        if key not in list(config.keys()):
            errors.append('Missing configuration param %s' % key)
            status = False

    if 'authentication' in list(config.keys()) and config['authentication'] == 'true':
        for key in ['username', 'password', 'auth_type']:
            if key not in list(config.keys()):
                errors.append('Missing configuration param %s' % key)
                status = False

    return status, errors

