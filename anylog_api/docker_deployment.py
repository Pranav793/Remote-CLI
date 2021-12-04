import argparse
import os
import time
import anylog_api.io_config as io_config
from anylog_api.docker_api import DeployDocker


def deploy_anylog_container(env_params:dict, docker_password:str, timezone:str='utc',
                            update_anylog:bool=False)->(bool, list):
    """
    Process to deploy AnyLog
    :args:
        env_params:dict - config params
        docker_password:str - docker password
        timezone:str - docker timezone
        update_anylog:bool - whether to update AnyLog
    :params:
        deploy_docker:class.DeployAnyLog - class call to DeployAnyLog
        status:bool
        errors:list - list of error messages
        deploy_docker:docker_calls.DeployAnyLog - class method used to deploy docker code
    :return:
        status, errors
    """
    deploy_docker = DeployDocker(timezone=timezone)
    errors = []

    status, validate_errors = io_config.validate_config(env_params=env_params)
    if status is False:
        for error in validate_errors:
            errors.append(error)
    else:
        status = deploy_docker.deploy_anylog_container(environment_variables=env_params, timezone=timezone,
                                                       docker_password=docker_password, update_anylog=update_anylog)
        if status is False:
            for error in deploy_docker.error_message:
                errors.append(error)
        elif status is False and len(deploy_docker.error_message) == 0:
            errors.append('Failed to deploy AnyLog container')
        else:
            errors.append('Successfully deployed AnyLog')

    return status, errors


def deploy_postgres_container(user_info:str=None, timezone:str='utc')->(bool, list):
    """
    Deploy postgres instance
    :args:
        user_info:str - Database connection information
        timezone:str - docker timezone
    :params:
        deploy_docker:class.DeployAnyLog - class call to DeployAnyLog
        status:bool
        errors:list - list of errors
    :return:
        status, errors
    """
    deploy_docker = DeployDocker(timezone=timezone)

    errors = []

    if not user_info:
        user_info = 'anylog@127.0.0.1:demo'

    status = deploy_docker.deploy_postgres_container(conn_info=user_info)
    if status is False:
        for error in deploy_docker.error_message:
            errors.append(error)
    elif status is False and len(deploy_docker.error_message) == 0:
        errors.append('Failed to deploy Postgres container')
    else:
        errors.append('Successfully deployed Postgres')

    return status, errors


def deploy_grafana_container()->list:
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
    deploy_docker = DeployDocker()

    status = deploy_docker.deploy_grafana_container()
    if status is False:
        for error in deploy_docker.error_message:
            errors.append(error)
    elif status is False and len(deploy_docker.error_message) == 0:
        errors.append('Failed to deploy Grafana container')
    else:
        errors.append('Successfully deployed Grafana')

    return errors


def manual_deployment():
    """
    The following is the main wrapper to deploy AnyLog (and Grafana / Postgres) docker container(s) using a
    configuration file. Unlike the code in "views.DeploymentViews.deploy_anylog"  which is used with the Django App,
    this main allows to deploy via command line with a preset configuration file.
    :positional arguments:
        config_file           configuration file with full path
    :optional arguments:
        -h, --help                               show this help message and exit
        --docker-password   DOCKER_PASSWORD     docker password (default: None)
        --update-anylog     UPDATE_ANYLOG       update AnyLog docker image (default: False)
        --psql              PSQL                deploy PostgreSQL docker container (default: False)
        --grafana           GRAFANA             deploy Grafana docker container (default: False)
    :params:
        status:bool
        config_file:str - full path for args.config_file
        env_params:dict - extracted values from config_file
    :print:
        A message is printed if a container fails to load and/or if AnyLog successfully deploys
    """
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('config_file', type=str, default='', help='configuration file with full path')
    # parser.add_argument('--timezone', type=str, default='utc', choices=['utc', 'local'], help='docker timezone')
    parser.add_argument('--docker-password', type=str, default=None, help='docker password')
    parser.add_argument('--update-anylog', type=bool, nargs='?', const=True, default=False, help='update AnyLog docker image')
    parser.add_argument('--psql', type=bool, nargs='?', const=True, default=False, help='deploy PostgreSQL docker container')
    parser.add_argument('--grafana', type=bool, nargs='?', const=True, default=False, help='deploy Grafana docker container')
    args = parser.parse_args()

    status = True

    config_file = os.path.expandvars(os.path.expanduser(args.config_file))
    if not os.path.isfile(config_file):
        print("Unable to locate config file: '%s'. Cannot deploy docker container(s)" % config_file)
        return status

    env_params = io_config.read_configs(config_file=config_file)

    if 'DB_USER' not in env_params:
        print("Missing database credentials. Setting db_user to: 'anylog@127.0.0.1:demo'")
        env_params['DB_USER'] = 'anylog@127.0.0.1:demo'

    if args.psql is True:
        status, errors = deploy_postgres_container(user_info=env_params['DB_USER'], timezone='utc')
        if status is False and len(errors) != 0:
            for error in errors:
                print(error)
        elif status is False:
            print('Failed to deploy Postgres container')
        else:
            time.sleep(15)

    if args.grafana is True:
        errors = deploy_grafana_container()
        if len(errors) != 0:
            for error in errors:
                print(error)

    if status is True:
        status, errors = deploy_anylog_container(env_params=env_params, docker_password=args.docker_password,
                                                 timezone='utc', update_anylog=args.update_anylog)
        if status is False and len(errors) != 0:
            for error in errors:
                print(error)
        elif status is False:
            print('Failed to deploy AnyLog container')
        else:
            print('Deployed AnyLog successfully')


if __name__ == '__main__':
    manual_deployment()






