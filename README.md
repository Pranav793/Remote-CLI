# AnyLog Django Connection

The following is intended to provide support for connecting a third-party application to AnyLog using Django.

## Requirements
* Python3
  * [docker](https://pypi.org/project/docker/) - used to deploy AnyLog
  * [django](https://pypi.org/project/Django/)
  * [requests](https://pypi.org/project/requests/)


## AnyLog Deployment
Directory [anylog_deploy](anylog_deploy) provides the ability to deploy an AnyLog node. 

### Process
1. User selects whether to use an existing config file or create a new file
2. If selecting _new file_ set configuration
   * Build & Node type 
   * General configuration - like: node name, company name, location and authentication
   * Networking configuration - IPs, ports and master node information 
   * Database configuration & Operator configurations - if node of type  _operator_ or _single-node_ 
   * MQTT configuration - if node of type _operator_, _publisher_, or _single-node_
3. Store configuration in [configs](anylog_deploy/configs) directory 
4. Repeat step 1 
5. Based on configuration, ask for information regarding deployment options
6. Deploy node

## AnyLog Query
Directory [anylog_query](anylog_query) provides the ability to query against an AnyLog instance.
Queries can be done either based on the (default) options provided or by manually typing a command. 

### List of Defaults Options
* Node Status
* Event Log
* Error Log
* Rest Log 
* Query Log
* Operator & Publisher Logs
* Query Status & Table Summaries
* Basic Blockchain commands 