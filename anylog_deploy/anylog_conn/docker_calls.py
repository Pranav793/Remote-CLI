"""
2. Should change to docker via Python
    - PyPi - https://pypi.org/project/docker/
    - GitHub: https://github.com/docker/docker-py
    - docs: https://docker-py.readthedocs.io/en/stable/client.html
"""
try:
    import docker
except Exception:
    pass


class DeployAnyLog:
    def __init__(self, timezone:str='utc'):
        """
        Connect to docker client
        :args:
            docker_client_path:str - path to docker socket
        :params:
            self.timezone:str - container(s) timezone 
        """
        self.error_message = []
        try:
            self.docker_client = docker.DockerClient()
        except Exception as e:
            self.error_message.append('Failed to set docker client (Error: %s)' %  e)
        else:
            self.timezone = timezone

    def __docker_login(self, password:str, exception:bool=False)->bool:
        """
        login into docker to download AnyLog
        :args:
            password:str - docker login password
            exception:bool - whether to print exception
        :params:
            status:bool
        :return:
            status
        """
        status = True
        try:
            self.docker_client.login(username='oshadmon', password=password)
        except Exception as e:
            self.error_message.append("Failed to log into docker with password: '%s' (Error: %s)" % (password, e))
            status = False

        return status

    # Image support functions - update, validate, remove
    def __update_image(self, image_name:str)->docker.models.images.Image:
        """
        Pull image oshadmon/anylog
        :args:
            image_name:str image with build

        :params:
            status:bool
        :return:
            if fails return False, else True
        """
        image = None
        try:
            image = self.docker_client.images.pull(repository=image_name)
        except Exception as e:
            self.error_message.append('Failed to pull image %s (Error: %s)' % (image_name, e))
        else:
            image = self.__validate_image(image_name=image_name)
            if image is None:
                self.error_message.append('Failed to pull image for an unknown reason...' % image_name)

        return image

    def __validate_image(self, image_name:str)->docker.models.images.Image:
        """
        Check if Image exists
        :args:
            image_name:str - image name (with build)
        :params:
            image
        :return:
            return image object, if fails return None
        """
        try:
            image = self.docker_client.images.get(name=image_name)
        except Exception:
            image = None

        return image

    # Volume support functions - create, validate, remove
    def __create_volume(self, volume_name:str)->docker.models.containers.Container:
        """
        Create volume (if not exists)
        :args:
            volume_name:str - volume name
            exception:bool - whether to print exception
        :params:
            volume:docker.models.containers.Container - volume object
        :return:
            volume
        """
        volume = None
        try:
            volume = self.docker_client.volumes.create(name=volume_name, driver='local')
        except Exception as e:
            self.error_message('Failed to create volume %s (Error: %s)' % (volume_name, e))
        else:
            volume = self.__validate_volume(volume_name=volume_name)
            if volume is None:
                self.error_message('Failed to create volume for %s' % volume_name)

        return volume

    def __validate_volume(self, volume_name:str)->docker.models.containers.Container:
        """
        Validate if volume exists
        :args:
            volume_name:str - volume name
        :params:
            volume:docker.models.volumes.Volume - volume object
        :return:
            volume if fails return None
        """
        volume = None
        try:
            volume = self.docker_client.volumes.get(volume_id=volume_name)
        except Exception:
            pass

        return volume

    # Container support functions - run, validate, stop
    def __run_container(self, image:str, container_name:str, environment:dict={},
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
            container = self.docker_client.containers.run(image=image, auto_remove=True, network_mode='host',
                                                          detach=True, stdin_open=True, tty=True, privileged=True,
                                                          name=container_name, environment=environment,
                                                          volumes=volumes)
        except Exception as e:
            self.error_message.append('Failed to deploy docker container %s against image %s (Error: %s)' % (container_name, image, e))
        else:
            container = self.__validate_container(container_name=container_name)
            if container is None:
                self.error_message.append('Failed to validate docker container %s' % container_name)

        return container

    def __validate_container(self, container_name:str)->docker.models.containers.Container:
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
            container = self.docker_client.containers.get(container_id=container_name)
        except Exception:
            pass

        return container

    # Deploy containers
    def deploy_anylog_container(self, docker_password:str, environment_variables:dict={}, timezone:str='utc',
                                update_anylog:bool=False):
        """
        Deploy AnyLog container
        :args:
            docker_password:str - docker password
            environment_variables:dict - docker enviornment parms
            timezone:str - whether to use UTC or local
            update_anylog:bool - whether to update AnyLog
        """
        status = True
        image = 'oshadmon/anylog:%s' % environment_variables['BUILD']
        node_name = environment_variables['NODE_NAME']
        volume_paths = {
            '%s-anylog' % node_name: '/app/AnyLog-Network/anylog',
            '%s-blockchain' % node_name: '/app/AnyLog-Network/blockchain',
            '%s-data' % node_name: '/app/AnyLog-Network/data',
            '%s-local-scripts' % node_name: '/app/AnyLog-Network/local_scripts'
        }

        """
        # Validate image information  
        1. Check if image exists || needs to be updated 
        2. if not log into docker with docker_password 
        3. update / download image
        4. if fails at any point during this process return False
        """
        if self.__validate_image(image_name=image) is None or update_anylog is True:
            if self.__docker_login(password=docker_password):
                img = self.__update_image(image_name=image)
                if not isinstance(img, docker.models.images.Image):
                    status = False
            if status is False:
                return status

        volumes = {}
        if timezone == 'local':
            volumes = {'/etc/localtime': {'bind': '/etc/localtime', 'mode': 'ro'}}
        
        for volume in volume_paths:
            if self.__validate_volume(volume_name=volume) is None:
                output = self.__create_volume(volume_name=volume)
                if isinstance(output, docker.models.containers.Container):
                    volumes[volume] = {'bind': volume_paths[volume], 'mode': 'rw'}
                else:
                    status = False
            else:
                volumes[volume] = {'bind': volume_paths[volume], 'mode': 'rw'}
        
        if self.__validate_container(container_name=node_name) is None:
            output = self.__run_container(image=image, container_name=node_name,
                                          environment=environment_variables, volumes=volumes)
            if not isinstance(output, docker.models.containers.Container):
                status = False

        return status

    def deploy_postgres_container(self, conn_info:str)->bool:
        """
        Deploy Postgres
        :args:
            conn_info:str - connection information (user@ip:passwd)
            db_port:int - database port
            password:str psql password correlated to user
        :params:
            status:bool
        :return:
            status
        """
        status = True

        environment = {
            'POSTGRES_USER': conn_info.split('@')[0],
            'POSTGRES_PASSWORD': conn_info.split(':')[-1]
        }

        volume_paths = {'pgdata': '/var/lib/postgresql/data'}

        volumes = {}
        if self.timezone == 'local':
            volumes = {'/etc/localtime': {'bind': '/etc/localtime', 'mode': 'ro'}}

        for volume in volume_paths:
            if self.__validate_volume(volume_name=volume) is None:
                output = self.__create_volume(volume_name=volume)
                if isinstance(output, docker.models.containers.Container):
                    volumes[volume] = {'bind': volume_paths[volume], 'mode': 'rw'}
                else:
                    status = False
            else:
                volumes[volume] = {'bind': volume_paths[volume], 'mode': 'rw'}

        if self.__validate_container(container_name='postgres-db') is None:
            output = self.__run_container(image='postgres:14.0-alpine', container_name='postgres-db',
                                          environment=environment, volumes=volumes)
            if isinstance(output, docker.models.containers.Container):
                status = False

        return status

    def deploy_grafana_container(self)->bool:
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
                output = self.__create_volume(volume_name=volume)
                if isinstance(output, docker.models.containers.Container):
                    volumes[volume] = {'bind': volume_paths[volume], 'mode': 'rw'}
                else:
                    status = False
            else:
                volumes[volume] = {'bind': volume_paths[volume], 'mode': 'rw'}

        if self.__validate_container(container_name='grafana') is None:
            output = self.__run_container(image='grafana/grafana:7.5.7', container_name='grafana',
                                          environment=environment, volumes=volumes)
            if not isinstance(output, docker.models.containers.Container):
                status = False

        return status




