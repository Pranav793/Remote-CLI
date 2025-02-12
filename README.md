# Remote CLI 

The Remote CLI is an API development environment specifically for AnyLog. The tool provides support for both `GET` & 
`POST` commands, providing an array of default options as well as the ability to manually execute commands. The preset
commands include, but not limited to:
* Node Status
* Event Log
* Error Log
* REST Log 
* Query Log
* Operator & Publisher Logs
* Query Status & Table Summaries
* Basic Blockchain commands 


### Requirements
* Python3
  * [django](https://pypi.org/project/Django/)
  * [requests](https://pypi.org/project/requests/)


### Deployment
```
cd $HOME/Django-API
python3 $HOME/Django-API/manage.py runserver ${IP}:${PORT}
```

### Build and deploy to docker

```
docker build -t my-remote-cli .
chmod +x remote_cli.sh
./remote_cli.sh
```

### Current IP

23.239.12.151:31800

#### Process
 1. Clone github repo
 2. run docker commands
 3. open localhost:8000