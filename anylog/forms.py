# Import form modules
from django import forms

# Create class to define the form fields
class AnyLogCredentials(forms.Form):
    conn_info = forms.CharField(label="Connection info", required=True)
    username = forms.CharField(label='Authentication User', required=False)
    password = forms.CharField(label='Authentication Password', required=False, widget=forms.PasswordInput)

    # destination = forms.CharField(label='Destination', required=False)
    command = forms.CharField(label='Command', required=False, widget=forms.TextInput)

