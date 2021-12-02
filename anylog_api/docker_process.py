import os
from anylog_api.docker_calls import DeployAnyLog
from anylog_api.io_config import read_configs, validate_config

def deploy_anylog(config_file:str, docker_password:str, timezone:str='utc', update_anylog:bool=False):
    """
    Deploy AnyLog
    :args:
        config_file:str - configuration file
        docker_password:str - docker password
        timezone:str - docker timezone
        update_anylog:bool - whether to update AnyLog
    :params:
        status:bool
        errors:list - list of error messages
        deploy_docker:docker_calls.DeployAnyLog - class method used to deploy docker code
        env_params:dict - params from config_file
    :return:
        status, errors
    """
    status = True
    deploy_docker = DeployAnyLog(timezone=timezone)
    errors = []
    config_file = os.path.expandvars(os.path.expanduser(config_file))

    if not os.path.isfile(config_file):
        errors.append('Unable to locate config file: %s' % config_file)
        status = False

    if status is True:
        env_params = read_configs(config_file=config_file)
        status, error = validate_config(env_params=env_params)
        if status is False:
            for err in error:
                errors.append(err)
        else:
            status, anylog_errors = deploy_docker.deploy_anylog_container(environment_variables=env_params, timezone=timezone,
                                                           docker_password=docker_password, update_anylog=update_anylog)
            if anylog_errors != []:
                for error in anylog_errors:
                    errors.append(error)
            elif status is False:

                errors.append('Failed to deploy AnyLog container')
            else:
                errors.append('Successfully deployed AnyLog')

    return status, errors


def deploy_postgres(config_file:str, timezone:str='utc')->(bool, list):
    """
    Deploy Postgres
    :args:
        config_file:str - Configuration file
        timezone:str - timezone
    :params:
        status:bool
        deploy_docker:docker_calls.DeployAnyLog - class method used to deploy docker code
        errors:list - error message
        env_params:dict - params from configs
    :return:
        status, errors
    """
    status = True
    errors = []
    deploy_docker = DeployAnyLog(timezone=timezone)

    config_file = os.path.expandvars(os.path.expanduser(config_file))

    if not os.path.isfile(config_file):
        errors.append('Unable to locate config file: %s' % config_file)
        status = False

    if status is True:
        env_params = read_configs(config_file=config_file)
        if 'DB_USER' not in env_params:
            env_params['DB_USER'] = 'anylog@127.0.0.1:demo'
        status = deploy_docker.deploy_postgres_container(conn_info=env_params['DB_USER'])
        if status is False:
            for error in deploy_docker.error_message:
                errors.append(error)

    return status, errors


def deploy_grafana()->list:
    """
    Deploy Grafana
    :args:
        None
    :params:
        status:bool
        deploy_docker:docker_calls.DeployAnyLog - class method used to deploy docker code
        errors:list - error message
    :return:
        errors
    """
    status = bool
    errors = []
    deploy_docker = DeployAnyLog()

    status = deploy_docker.deploy_grafana_container()
    if status is False:
        for error in deploy_docker.error_message:
            errors.append(error)

    return errors
