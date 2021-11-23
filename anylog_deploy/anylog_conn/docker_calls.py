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
            if exception is True:
                print("Failed to log into docker with password: '%s' (Error: %s)" % (password, e))
            status = False

        return status

    # Image support functions - update, validate, remove
    def __update_image(self, image_name:str, exception:bool=True)->docker.models.images.Image:
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
            if exception is True:
                print('Failed to pull image %s (Error: %s)' % (image_name, e))
        else:
            image = self.__validate_image(image_name=image_name)
            if image is None and exception is True:
                print('Failed to pull image for an unknown reason...' % image_name)

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

    def __remove_image(self, image_name:str, exception:bool=True)->bool:
        """
        Remove image from docker
        :args:
            image_name:str - image name with version
            exception:bool - whether or not to print exceptions
        :params:
            image_obj:docker.models.images.Image - Image object
            status:bool
        :return:
            status
        """
        status = True

        try:
            self.docker_client.images.remove(image=image_name)
        except Exception as e:
            status = False
            if exception is True:
                print('Failed to remove image %s (Error: %s)' % (image_name, e))
        else:
            if self.__validate_image(image_name=image_name) is not None:
                status = False
                if exception is True:
                    print('Failed to remove image: %s' % image_name)

        return status

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

    def __remove_volume(self, volume:docker.models.volumes.Volume, exception:bool=True)->bool:
        """
        Remove volume
        :args:
            volume:docker.models.volumes.Volume - volume object
            exception:bool - whether to print exception
        :params:
            status:bool - whether to print exceptions
        :return:
            status
        """
        status = True

        try:
            volume.remove()
        except Exception as e:
            status = False
            if exception is True:
                print('Failed to remove volume for container %s (Error: %s)' % (container.name, e))
        else:
            if self.__validate_volume(volume_name=volume) is not None:
                status = False
                if exception is True:
                    print('Failed to remove volume for container %s' % container.name)

        return status

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

    def __stop_container(self, container:docker.models.containers.Container, exception:bool=False)->bool:
        """
        Stop container based on name
        :args:
            container:docker.models.containers.Container - container object
            exception:bool - whether to print exception
        :params:
            status:bool
        :return:
            status
        """
        status = True

        try:
            container.stop()
        except Exception as e:
            status = False
            if exception is True:
                print('Failed to remove container %s (Error: %s)' % (container.name, e))
        else:
            if self.__validate_container(container_name=container.name) is not None:
                status = False
                if exception is True:
                    print('Failed to remove container %s' % container.name)

        return status

    # Deploy containers
    def deploy_anylog_container(self, docker_password:str, update_image:bool=False,
                                container_name:str='anylog-test-node', build:str='predevelop',
                                external_ip:str=None, local_ip:str=None, server_port:int=2048, rest_port:int=2049,
                                broker_port:int=None, authentication:str='off', auth_type:str='admin',
                                username:str='anylog', password:str='demo', expiration:str=None,
                                exception:bool=True)->bool:
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
            if self.__validate_container(container_name=container_name) is None:
                if not self.__run_container(image='oshadmon/anylog:%s' % build, container_name=container_name,
                                          environment=environment, volumes=volumes, exception=exception):
                    print('Fails') 
                    status = False

        return status

    def deploy_grafana_container(self, exception:bool=True)->bool:
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

        if self.__validate_container(container_name='grafana') is None:
            if not self.__run_container(image='grafana/grafana:7.5.7', container_name='grafana',
                                        environment=environment, volumes=volumes, exception=exception):
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
                                          environment=environment, volumes=volumes, exception=exception)
            if isinstance(output, docker.models.containers.Container):
                status = False

        return status


