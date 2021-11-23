import argparse
import os

from deployment_process import main as deployment_process
from io_config import read_configs

def main():
    """
     The following is an extension of deployment_process.py to allow for deployment of AnyLog using a config file
     through command line (terminal) rather than through the Django application.
    :positional arguments:
        config_file         CONFIG_FILE         configuration file with full path
    :optional arguments:
        -h, --help                              show this help message and exit
        --timezone          TIMEZONE            docker timezone (default: utc)
        --docker-password   DOCKER_PASSWORD     docker password (default: None)
        --update-anylog     UPDATE_ANYLOG       update AnyLog docker image (default: False)
        --psql              PSQL                deploy PostgreSQL docker container (default: False)
        --grafana           GRAFANA             deploy Grafana docker container (default: False)
    :params:
        config_file:str - full path of args.config_file
        env_params:dict - content from config_file
    :print:
        At the end of the process, the code prints either 'Success' or the error that occured during deployment
    """
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('config_file', type=str, default='', help='configuration file with full path')
    parser.add_argument('--timezone', type=str, default='utc', choices=['utc', 'local'], help='docker timezone')
    parser.add_argument('--docker-password', type=str, default=None, help='docker password')
    parser.add_argument('--update-anylog', type=bool, nargs='?', const=True, default=False, help='update AnyLog docker image')
    parser.add_argument('--psql', type=bool, nargs='?', const=True, default=False, help='deploy PostgreSQL docker container')
    parser.add_argument('--grafana', type=bool, nargs='?', const=True, default=False, help='deploy Grafana docker container')
    args = parser.parse_args()

    config_file = os.path.expandvars(os.path.expanduser(args.config_file))
    env_params = {}
    output = None

    if os.path.isfile(config_file):
        env_params = read_configs(config_file=config_file)

    if env_params != {}:
        output = deployment_process(env_params=env_params, docker_password=args.docker_password, timezone=args.timezone,
                                    update_anylog=args.update_anylog, psql=args.psql, grafana=args.grafana)
    print(output)



if __name__ == '__main__':
    main()