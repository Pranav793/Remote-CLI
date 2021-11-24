from django import forms
from django.core.validators import RegexValidator
import os

CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'configs')

BUILDS = (
    ('', ("")),
    ('develop', ("develop")),
    ('develop-alpine', ("alpine")),
    ('predevelop', ("predevelop")),
    ('predevelop-alpine', ("predevelop-alpine"))
)

NODE_TYPES = (
    ('', ("")),
    ('none', ("Empty")),
    ('master', ("Master")),
    ('operator', ("Operator")),
    ('publisher', ("Publisher")),
    ('query', ("Query")),
    ('single-node', ("single-node"))
)

NODE_TYPE = None

AUTHENTICATION_TYPE = (
    ('admin', ("Admin")),
    ('user', ("User"))
)

DATABASES = (
    ('sqlite', ("SQLite")),
    ('psql', ("PostgreSQL"))
)

MQTT_COLUMN_TYPES = (
    ('str', ("String")),
    ('int', ("Integer")),
    ('float', ("Float")),
    ('timestamp', ("Timestamp")),
    ('bool', ("Boolean")),
)

TIMEZONE = (
    ('utc', ('UTC')),
    ('local', ('Local'))
)

class SelectConfig(forms.Form):
    preset_config_file = forms.FilePathField(label='Config File', path=CONFIG_FILE_PATH, required=False)
    external_config_file = forms.CharField(label='External Config File', required=False)

class DeployAnyLog(forms.Form):
    password = forms.CharField(label='Docker Password', required=False, widget=forms.PasswordInput)
    update_anylog = forms.BooleanField(label='Update AnyLog', required=False)
    timezone = forms.ChoiceField(label='Set Docker Timezone', required=False, choices=TIMEZONE)
    psql = forms.BooleanField(label='Deploy PostgreSQL', required=False)
    grafana = forms.BooleanField(label='Deploy Grafana', required=False)

class BaseInfo(forms.Form):
    build = forms.ChoiceField(label='Build', required=True, choices=BUILDS)
    node_type = forms.ChoiceField(label='Node Type', required=True, choices=NODE_TYPES)

class GeneralInfo(forms.Form):
    node_name = forms.CharField(label='Node Name', required=True)
    company_name = forms.CharField(label='Company Name', required=True)
    location = forms.CharField(label='Location', required=False)

    # authentication
    authentication = forms.BooleanField(label='Authentication', required=False)
    username = forms.CharField(label='Authentication User', required=False)
    password = forms.CharField(label='Authentication Password', required=False, widget=forms.PasswordInput)
    auth_type = forms.ChoiceField(label='Authentication User Type', required=False, choices=AUTHENTICATION_TYPE)

class NetworkingConfigs(forms.Form):
    # networking
    master_validator = RegexValidator('{:')
    external_ip = forms.GenericIPAddressField(label='External IP Address', required=False)
    local_ip = forms.GenericIPAddressField(label='Local IP Address', required=False)
    anylog_tcp_port = forms.IntegerField(label='TCP Port Number', required=True)
    anylog_rest_port = forms.IntegerField(label='REST Port Number', required=True)
    anylog_broker_port = forms.IntegerField(label='Broker Port Number', required=False)
    master_node = forms.CharField(label='Master Node IP:Port Information', required=True)


class DBConfigs(forms.Form):
    # database
    db_type = forms.ChoiceField(label='Database Type', required=False, choices=DATABASES)
    db_user = forms.CharField(label='Database User', required=True)
    db_pass = forms.CharField(label='Database Password', required=True, widget=forms.PasswordInput)
    db_addr = forms.GenericIPAddressField(label='Database Address', required=True)
    db_port = forms.IntegerField(label='Database Port', required=True)

class NoneConfigs(forms.Form):
    # Configuration information for an empty node
    node_name = forms.CharField(label='Node Name', required=True)
    db_type = forms.ChoiceField(label='Database Type', required=False, choices=DATABASES)
    db_user = forms.CharField(label='Database User', required=False)
    db_pass = forms.CharField(label='Database Password', required=False, widget=forms.PasswordInput)
    db_addr = forms.GenericIPAddressField(label='Database Address', required=False)
    db_port = forms.IntegerField(label='Database Port', required=False)

class DBOperatorConfigs(forms.Form):
    # database
    db_type = forms.ChoiceField(label='Database Type', required=False, choices=DATABASES)
    db_user = forms.CharField(label='Database User', required=True)
    db_pass = forms.CharField(label='Database Password', required=True, widget=forms.PasswordInput)
    db_addr = forms.GenericIPAddressField(label='Database Address', required=True)
    db_port = forms.IntegerField(label='Database Port', required=True)

    # Operator specific params
    default_dbms = forms.CharField(label='Operator Database Name', required=False)
    enable_cluster = forms.BooleanField(label='Enable Cluster', required=False)
    cluster_name = forms.CharField(label='Cluster Name', required=False)

    # Operator partition
    enable_partition = forms.BooleanField(label='Enable Partitions', required=False)
    partition_column = forms.CharField(label='Column to Partition By', required=False)
    partition_interval = forms.CharField(label='Partitioning Interval', required=False)

class MqttConfigs(forms.Form):
    mqtt_enable = forms.BooleanField(label='Enable MQTT', required=False)
    mqtt_broker = forms.CharField(label='MQTT Broker', required=False)
    mqtt_port = forms.IntegerField(label='MQTT Broker Port', required=False)
    mqtt_user = forms.CharField(label='MQTT User', required=False)
    mqtt_pass = forms.CharField(label='MQTT Password', required=False, widget=forms.PasswordInput)
    mqtt_log = forms.BooleanField(label='Enable MQTT Logging', required=False)
    mqtt_topic_name = forms.CharField(label='Topic Name', required=False)
    mqtt_topic_dbms = forms.CharField(label='Database Name', required=False)
    mqtt_topic_table = forms.CharField(label='Table Name', required=False)
    mqtt_column_timestamp = forms.CharField(label='Timestamp Column', required=False)
    mqtt_column_value_type = forms.ChoiceField(label='Value Column Type', required=False, choices=MQTT_COLUMN_TYPES)
    mqtt_column_value = forms.CharField(label='Value Column', required=False)






