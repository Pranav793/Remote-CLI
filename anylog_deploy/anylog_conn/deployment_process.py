import docker
import sys

def __docker_login(docker_client:docker.client.DockerClient, password:str)->bool:
    """
    Docker login process
    :args:
        password:str - docker password
    :params:
        status:bool
    """
    status = ''
    try:
        docker_client.login(username='oshadmon', password=password)
    except Exception as e:
        status = 'Error: Failed to log into docker (Error: %s)' % e
    return ''


def __validate_container(docker_client:docker.client.DockerClient,
                         container_name:str)->docker.models.containers.Container:
    """
    Validate container was deployed
    :args:
        container_name:str - container name
        exception:bool - whether to print exception
    :params:
        container:docker.models.containers.Container - container object
    :return:
        container object, else None
    """
    container = None
    try:
        container = docker_client.containers.get(container_id=container_name)
    except Exception:
        pass

    return container


def __run_container(docker_client:docker.client, image:str, container_name:str, environment:dict={},
                    volumes:dict={})->docker.models.containers.Container:
        """
        Deploy docker container based on params
        :docker-call:
            docker run --name ${CONTAINER_NAME}
                -e ${ENV_KEY}=${ENV_VALUE}
                ...
                -v ${VOLUME_KEY}:${DIRECTORY_PATH}
                ...
                --host network --rm ${IMAGE}
        :args:
            image:str - image name with build
            container_name:str - container name
            environment:dict - environment params
            volumes:dict - volume params
            exception:bool - whether or not to print exceptions
        :params:
            container:docker.models.containers.Container - docker container object
        :return:
            status
        """
        container = None
        try:
            container = docker_client.containers.run(image=image, auto_remove=True, network_mode='host',
                                                     detach=True, stdin_open=True, tty=True, privileged=True,
                                                     name=container_name, environment=environment,
                                                     volumes=volumes)
        except Exception as e:
            return 'Error: Failed to deploy docker container %s against image %s (Error: %s)' % (container_name, image, e)
        else:
            container = __validate_container(container_name=container_name)
            if container is None:
                return 'Error: Failed to validate docker container %s' % container_name

        return None


def deploy_postgres(docker_client:docker.client.DockerClient, conn_info:str, timezone:str)->str:
    """
    Deploy postgres
    :args:
        docker_client:docker.client.DockerClient - docker client
        connection_info - username@{ip}:password
        timezone:str - timezone
    :params:
        status:bool
        container_name:str - container name
        build:str - postgres build
        environment:dict - environment variables
        volumes:dict - postgres volumes
    :return:
        error, otherwise None
    """
    status = None
    container_name = 'postgres-db'
    build='postgres:14.0-alpine'
    environment = {
        'POSTGRES_USER': conn_info.split('@')[0],
        'POSTGRES_PASSWORD': conn_info.split(':')[-1]
    }
    volumes = {'pgdata': {'bind': '/var/lib/postgresql/data', 'mode': 'ro'}}
    if timezone == 'local' and not sys.platform.startswith('win'):
        volumes['/etc/localtime'] = {'bind': '/etc/localtime', 'mode': 'ro'}

    if __validate_container(docker_client=docker_client, container_name=container_name) is None:
        status = __run_container(docker_client=docker_client, image=build, container_name=container_name,
                        environment=environment, volumes=volumes)
    return status


def deploy_grafana(docker_client:docker.client.DockerClient, timezone:str)->str:
    """
    Deploy grafana
    :args:
        docker_client:docker.client.DockerClient - docker client
        timezone:str - timezone
    :params:
        container_name:str - container name
        build:str - postgres build
        environment:dict - environment variables
        volumes:dict - grafana volumes
    :return:
        error, otherwise None
    """
    status = None
    container_name = 'grafana'
    build='grafana/grafana:7.5.7'
    environment = {'GF_INSTALL_PLUGINS': 'simpod-json-datasource,grafana-worldmap-panel'}
    volumes = {
        'grafana-data': {'bind': '/var/lib/grafana', 'mode': 'ro'},
        'grafana-log': {'bind': '/var/log/grafana', 'mode': 'ro'},
        'grafana-config': {'bind': '/etc/grafana', 'mode': 'ro'}
    }

    if __validate_container(docker_client=docker_client, container_name=container_name) is None:
        status = __run_container(docker_client=docker_client, image=build, container_name=container_name,
                                 environment=environment, volumes=volumes)
    return status


def update_anylog(docker_client:docker.client.DockerClient, build:str)->str:
    """
    Update AnyLog
    :args:
        docker_client:docker.client.DockerClient - docker client
        build:str - AnyLog version build to update
    :return:
        error, else None
    """
    repo = 'oshadmon/anylog:%s' % build
    try:
        docker_client.images.pull(repository=repo)
    except Exception as e:
        return 'Error: Failed to pull image %s (Error: %s)' % (repo, e)
    return None


def depeloy_anylog(docker_client:docker.client.DockerClient, timezone:str, env_params:dict)->str:
    """
    Deploy AnyLog instance
    :args:
        docker_client:docker.client.DockerClient - docker client
        timezone:str - timezone
        env_params:dict - environment params
    :params:
        container_name:str - container name
        build:str - postgres build
        volumes:dict - grafana volumes
    :retrun:
        error, else None
    """
    status = None
    container_name = env_params['NODE_NAME'].replace(' ', '-')
    build = 'oshadmon/anylog:%s' % env_params['BUILD']
    volumes = {
        '%s-anylog' % container_name: '/app/AnyLog-Network/anylog',
        '%s-blockchain' % container_name: '/app/AnyLog-Network/blockchain',
        '%s-data' % container_name: '/app/AnyLog-Network/data',
        '%s-local-scripts' % container_name: '/app/AnyLog-Network/local_scripts'
    }
    if timezone == 'local' and not sys.platform.startswith('win'):
        volumes['/etc/localtime'] = {'bind': '/etc/localtime', 'mode': 'ro'}

    if __validate_container(docker_client=docker_client, container_name=container_name) is None:
        status = __run_container(docker_client=docker_client, image=build, container_name=container_name,
                                 environment=env_params, volumes=volumes)
    return status


def main(env_params:dict, docker_password:str, timezone:str, update_anylog:bool, psql:bool, grafana:bool)->str:
    """
    Main for the deployment process
    :args:
        env_params:dict - environment variables from config file
        docker_password:str - password for docker
        timezone:str - docker timezone
        update_anylog:bool - whether to update the AnyLog version
        psql:bool - whether to deploy postgres
        grafana:bool - whether to deploy Grafana
    :params:
        status:str - status message
    :return:
        status
    """
    try:
        docker_client = docker.DockerClient()
    except Exception as e:
       return 'Failed to set docker client'
    # docker login into AnyLog account
    output = __docker_login(docker_client=docker_client, password=docker_password)
    if output != '':
        return output

    # deploy psql
    if psql is True:
        output = deploy_postgres(docker_client=docker_client, conn_info=env_params['DB_USER'], timezone=timezone)
        if isinstance(output, str):
            return output

    # deploy grafana
    if grafana is True:
        output = deploy_grafana(docker_client=docker_client, timezone=timezone)
        if isinstance(output, str):
            return output

    # deploy anylog
    if update_anylog is True:
        output = update_anylog(docker_client=docker_client, build=env_params['BUILD'])
        if isinstance(output, str):
            return output
    output = depeloy_anylog(docker_client=docker_client, timezone=timezone, env_params=env_params)
    if isinstance(output, str):
        return output

    return 'Successs'