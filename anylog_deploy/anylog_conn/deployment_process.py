import argparse
import os
from anylog_deploy.anylog_conn.docker_calls import DeployAnyLog
from anylog_deploy.anylog_conn.io_config import read_configs


def django_main(config_file:str, timezone:str='utc', docker_password:str=None, update_anylog:bool=False,
                psql:bool=False, grafana:bool=False)->(bool, list):
    """
    The following is the main wrapper to deploy AnyLog (and Grafana / Postgres) docker container(s) using a
    configuration file. The method is called from within the Django App.
    :args:
        config_file:str - configuration file
        timezone:str - docker timezone
        docker_password:str -  docker password
        update_anylog:bool - whether to update AnyLog
        psql:bool - deploy Postgres docker container
        grafana:bool - deploy Grafana docker container
    :params:
        status:bool
        errors:list - list of error messages
        deploy_anylog:docker_calls.DeployAnyLog - class method used to deploy docker code

        env_params:dict - content from config_file
    """
    status = True
    errors = []
    env_params = {}
    deploy_anylog = DeployAnyLog(timezone=timezone)

    if len(deploy_anylog.error_message) > 0:
        errors.append(deploy_anylog.error_message[0])
        return False, errors

    config_file = os.path.expandvars(os.path.expanduser(args.config_file))
    if os.path.isfile(config_file):
        env_params = read_configs(config_file=config_file)

    if psql is True:
        status = deploy_anylog.deploy_postgres_container(conn_info=env_params['DB_USER'])
        if status is True:
            for error in deploy_anylog.error_message:
                errors.append(error)
            deploy_anylog.error_message = []

    if grafana is True:
        if not deploy_anylog.deploy_grafana_container():
            for error in deploy_anylog.error_message:
                errors.append(error)

    if status is True:
        status = deploy_anylog.deploy_anylog_container(docker_password=docker_password, timezone=timezone,
                                                       environment_variables=env_params, update_anylog=update_anylog)
        if status is False:
            for error in deploy_anylog.error_message:
                errors.append(error)

    return status, errors


def terminal_main():
    """
    The following is the main wrapper to deploy AnyLog (and Grafana / Postgres) docker container(s) using a
    configuration file. Unlike `djano_main`, which is used with the Django App, this main allows to deploy via command
    line with a preset configuration file.
    :positional arguments:
        config_file         CONFIG_FILE         configuration file with full path
    :optional arguments:
        -h, --help                              show this help message and exit
        --timezone          TIMEZONE            docker timezone (default: utc | choices: local, utc)
        --docker-password   DOCKER_PASSWORD     docker password (default: None)
        --update-anylog     UPDATE_ANYLOG       update AnyLog docker image (default: False)
        --psql              PSQL                deploy PostgreSQL docker container (default: False)
        --grafana           GRAFANA             deploy Grafana docker container (default: False)
    :params:
        status:bool
        deploy_anylog:docker_calls.DeployAnyLog - class method used to deploy docker code
        config_file:str - full path of args.config_file
        env_params:dict - content from config_file
    :print:
        At the end of the process, the code prints either 'Success' or the error that occurred during deployment
    """
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('config_file', type=str, default='', help='configuration file with full path')
    parser.add_argument('--timezone', type=str, default='utc', choices=['utc', 'local'], help='docker timezone')
    parser.add_argument('--docker-password', type=str, default=None, help='docker password')
    parser.add_argument('--update-anylog', type=bool, nargs='?', const=True, default=False, help='update AnyLog docker image')
    parser.add_argument('--psql', type=bool, nargs='?', const=True, default=False, help='deploy PostgreSQL docker container')
    parser.add_argument('--grafana', type=bool, nargs='?', const=True, default=False, help='deploy Grafana docker container')
    args = parser.parse_args()

    status = True
    deploy_anylog = DeployAnyLog(timezone=args.timezone)
    if len(deploy_anylog.error_message) > 0:
        print(deploy_anylog.error_message[0])
        exit(1)

    config_file = os.path.expandvars(os.path.expanduser(args.config_file))
    env_params = {}

    if os.path.isfile(config_file):
        env_params = read_configs(config_file=config_file)

    if args.psql is True:
        status = deploy_anylog.deploy_postgres_container(conn_info=env_params['DB_USER'])
        if status is True:
            for error in deploy_anylog.error_message:
                print(error)
            deploy_anylog.error_message = []

    if args.grafana is True:
        if not deploy_anylog.deploy_grafana_container():
            for error in deploy_anylog.error_message:
                print(error)
    
    if status is True:
        status = deploy_anylog.deploy_anylog_container(docker_password=args.docker_password,
                                                       environment_variables=env_params, timezone=args.timezone,
                                                       update_anylog=args.update_anylog)
        if status is False:
            for error in deploy_anylog.error_message:
                print(error)
                print('Unable to download AnyLog, thus cannot continue...')
                exit(1)
        else:
            print('Successfully deployed AnyLog!')

if __name__ == '__main__':
    terminal_main()
