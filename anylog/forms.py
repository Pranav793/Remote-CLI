# Import form modules
from django import forms

ANYLOG_COMMANDS= [
    (1, 'Node Status'),
    (2, 'Event Log'),
    (3, 'Error Log'),
    (40, 'Disable REST Log'),
    (41, 'Enable REST Log'),
    (5, 'Full REST Log'),
    (6, 'Latest REST request'),
    (7, 'Get Streaming'),
    (8, 'Operator Summary'),
    (9, 'Publisher Summary'),
    (10, 'Full Query Status List'),
    (11, 'Latest Query Status'),
    (12, 'Rows Count'),
    (13, 'Rows Count by Table')
]


# Create class to define the form fields
class AnyLogCredentials(forms.Form):
    conn_info = forms.CharField(label="Connection info", required=True)
    username = forms.CharField(label='Authentication User', required=False)
    password = forms.CharField(label='Authentication Password', required=False, widget=forms.PasswordInput)

    # destination = forms.CharField(label='Destination', required=False)
    command = forms.CharField(label='Command', required=False, widget=forms.TextInput)

    anylog_cmd = forms.CharField(label='Preset Commands', widget=forms.RadioSelect(choices=ANYLOG_COMMANDS),
                                 empty_value=None, required=False)

    network = forms.BooleanField(label='Network', required=False)
    post = forms.BooleanField(label='POST Command', required=False)


