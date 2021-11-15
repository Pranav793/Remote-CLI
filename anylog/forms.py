# Import form modules
from django import forms

# Create class to define the form fields
class AnyLogForm(forms.Form):
    conn_info = forms.CharField(label="Connection info", required=True)
    username = forms.CharField(label='Authentication User', required=False)
    password = forms.CharField(label='Authentication Password', required=False, widget=forms.PasswordInput)
    command = forms.CharField(label='Command', required=True, widget=forms.TextInput)

    # name = forms.CharField(label="Full name", max_length=40)
    # email = forms.EmailField(label="Email", max_length=50)
    # username = forms.CharField(label="Username", max_length=20)
