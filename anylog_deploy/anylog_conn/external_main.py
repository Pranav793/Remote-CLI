import argparse
import os

from deployment_process import main as deployment_process
from io_config import read_configs


# Deploy containers
def deploy_anylog_container(self, docker_password: str, update_image: bool = False,
                            container_name: str = 'anylog-test-node', build: str = 'predevelop',
                            external_ip: str = None, local_ip: str = None, server_port: int = 2048,
                            rest_port: int = 2049,
                            broker_port: int = None, authentication: str = 'off', auth_type: str = 'admin',
                            username: str = 'anylog', password: str = 'demo', expiration: str = None,
                            exception: bool = True) -> bool:
    """
    Deploy an AnyLog of type rest
    :args:
        docker_password:str - docker password to download AnyLog container
        update_image:bool - whether to update the image (if exists)
        container_name:str - name of the container
        build:str - version of AnyLog image to download
        server_port:int - TCP server port
        rest_port:int - REST server port
        authentication:str - whether to enable authentication
        exception:bool - whether or not to print exceptions
        # Optional configs
        external_ip:str - IP address that's different than the default external IP
        local_ip:str - IPs address that's different  than the default local IP
        broker_port:int - MQTT message broker port
        username:str - authentication username
        password:str - authentication password
    :params:
        status:bool
        volume_paths:dict - key: volume_name | value: path within AnyLog
        volumes:dict - volumes related to AnyLog
        environment:dict - environment variables for docker based on arguments
    :return:
        status
    """
    status = True

    environment = {
        'NODE_TYPE': 'rest',
        'NODE_NAME': container_name,
        'ANYLOG_SERVER_PORT': server_port,
        'ANYLOG_REST_PORT': rest_port,
        'AUTHENTICATION': authentication,
        'AUTH_TYPE': auth_type,
        'USERNAME': username,
        'PASSWORD': password,
        'EXPIRATION': expiration,
    }
    if external_ip is not None:
        environment['EXTERNAL_IP'] = external_ip
    if local_ip is not None:
        environment['IP'] = local_ip
    if broker_port is not None:
        environment['ANYLOG_BROKER_PORT'] = broker_port

    volume_paths = {
        '%s-anylog' % container_name: '/app/AnyLog-Network/anylog',
        '%s-blockchain' % container_name: '/app/AnyLog-Network/blockchain',
        '%s-data' % container_name: '/app/AnyLog-Network/data',
        '%s-local-scripts' % container_name: '/app/AnyLog-Network/local_scripts'
    }

    volumes = {}
    if self.timezone == 'local':
        volumes = {'/etc/localtime': {'bind': '/etc/localtime', 'mode': 'ro'}}

    # Prepare volumes
    for volume in volume_paths:
        if self.__validate_volume(volume_name=volume) is None:
            if self.__create_volume(volume_name=volume, exception=exception) is not None:
                volumes[volume] = {'bind': volume_paths[volume], 'mode': 'rw'}
        else:
            volumes[volume] = {'bind': volume_paths[volume], 'mode': 'rw'}

    # login
    if update_image is True or self.__validate_image(image_name='oshadmon/anylog:%s' % build) is None:
        status = self.__docker_login(password=docker_password, exception=exception)

    # Update image
    if status is True and update_image is True:
        status = self.__update_image(image_name='oshadmon/anylog:%s' % build, exception=exception)

    # deploy AnyLcg container
    if status is True:
        if self.validate_container(container_name=container_name) is None:
            if not self.__run_container(image='oshadmon/anylog:%s' % build, container_name=container_name,
                                        environment=environment, volumes=volumes, exception=exception):
                print('Fails')
                status = False

    return status


def deploy_grafana_container(self, exception: bool = True) -> bool:
    """
    Deploy a Grafana v 7.5.7 as a docker container
    :args:
        exception:bool - whether to print exceptions or not
    :params:
        status:bool
    :return:
        status
    """
    status = True

    environment = {
        'GF_INSTALL_PLUGINS': 'simpod-json-datasource,grafana-worldmap-panel'
    }
    volume_paths = {
        'grafana-data': '/var/lib/grafana',
        'grafana-log': '/var/log/grafana',
        'grafana-config': '/etc/grafana'
    }

    volumes = {}
    if self.timezone == 'local':
        volumes = {'/etc/localtime': {'bind': '/etc/localtime', 'mode': 'ro'}}

    for volume in volume_paths:
        if self.__validate_volume(volume_name=volume) is None:
            if self.__create_volume(volume_name=volume, exception=exception) is not None:
                volumes[volume] = {'bind': volume_paths[volume], 'mode': 'rw'}
        else:
            volumes[volume] = {'bind': volume_paths[volume], 'mode': 'rw'}

    if self.validate_container(container_name='grafana') is None:
        if not self.__run_container(image='grafana/grafana:7.5.7', container_name='grafana',
                                    environment=environment, volumes=volumes, exception=exception):
            status = False

    return status



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