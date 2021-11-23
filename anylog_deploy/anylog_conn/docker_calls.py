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
            self.error_messages:list - list of error messages
        """
        self.error_messages = []
        try:
            self.docker_client = docker.DockerClient()
        except Exception as e:
            print('Failed to set docker client (Error: %s)' %  e)
            self.status = False
        else:
            self.timezone = timezone



    def deploy_postgres_container(self, conn_info:str, db_port:int)->bool:
        """
        Deploy Postgres
        :args:
            conn_info:str - connection information (user@ip:passwd)
            db_port:int - database port
        :params:
            status:bool
        :return:
            status
        """
        status = True
        image = 'postgres:14.0'
        container_name='postgres-db'
        db_ports = {'%s/tcp' % db_port: ('127.0.0.1', db_port)}
        environment = {
            'POSTGRES_USER': conn_info.split('@')[0],
            'POSTGRES_PASSWORD': conn_info.split(':')[-1]
        }
        volumes = {'pgdata': {'bind': '/var/lib/postgresql/data', 'mode': 'ro'}}

        if self.timezone == 'local':
            volumes['/etc/localtime'] = {'bind': '/etc/localtime', 'mode': 'ro'}

        try:
            self.docker_client.containers.run(image=image, auto_remove=True, network='host', detach=True,
                                              stdin_open=True, tty=True, privileged=True, name=container_name,
                                              environment=environment,volumes=volumes)
        except Exception as e:
            self.error_messages.append('Failed to Postgres deploy docker client (Error: %s)' % e)
            status = False

        return status



        return status

