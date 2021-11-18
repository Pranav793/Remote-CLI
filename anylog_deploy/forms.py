from django import forms

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


class BaseInfo(forms.Form):
    build = forms.ChoiceField(label='Build', required=True, choices=BUILDS)
    node_type = forms.ChoiceField(label='Node Type', required=True, choices=NODE_TYPES)
    password = forms.CharField(label='Docker Password', required=False, widget=forms.PasswordInput)

class GeneralInfo(forms.Form):
    node_name = forms.CharField(label='Node Name', required=True)
    company_name = forms.CharField(label='Company Name', required=True)
    location = forms.CharField(label='Location', required=False)

    # authentication
    authentication = forms.BooleanField(label='Authentication', required=False)
    username = forms.CharField(label='Authentication User', required=False)
    password = forms.CharField(label='Authentication Password', required=False, widget=forms.PasswordInput)
    auth_type = forms.ChoiceField(label='Authentication User Type', required=False, choices=AUTHENTICATION_TYPE)


class AnyLogDeployment(forms.Form):
    # general
    build = forms.ChoiceField(label='Build', required=True, choices=BUILDS)
    node_type = forms.ChoiceField(label='Node Type', required=True, choices=NODE_TYPES)
    node_name = forms.CharField(label='Node Name', required=True)
    company_name = forms.CharField(label='Company Name', required=True)
    location = forms.CharField(label='Location', required=False)

    # authentication
    authentication = forms.BooleanField(label='Authentication', required=False)
    username = forms.CharField(label='Authentication User', required=False)
    password = forms.CharField(label='Authentication Password', required=False, widget=forms.PasswordInput)
    auth_type = forms.ChoiceField(label='Authentication User Type', required=False, choices=AUTHENTICATION_TYPE)

    # networking
    external_ip = forms.GenericIPAddressField(label='External IP Address', required=False)
    local_ip = forms.GenericIPAddressField(label='Local IP Address', required=False)
    anylog_tcp_port = forms.IntegerField(label='TCP Port Number', required=True)
    anylog_rest_port = forms.IntegerField(label='REST Port Number', required=True)
    anylog_broker_port = forms.IntegerField(label='Broker Port Number', required=False)
    master_node = forms.CharField(label='Master Node IP:Port Information', required=True)

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

    # MQTT
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






