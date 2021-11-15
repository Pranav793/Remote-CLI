from django.shortcuts import render

# Create your views here.
# Import necessary modules
from django.shortcuts import render
from anylog.forms import AnyLogForm
from django.http import HttpResponse

# ---------------------------------------------------------------------------------------
# GET / POST  AnyLog command form
# ---------------------------------------------------------------------------------------
def form_request(request):

    # Check the form is submitted or not
    if request.method == 'POST':
        user_info = AnyLogForm(request.POST)
        # Check the form data are valid or not
        if user_info.is_valid():
            # Proces the command
            data = process_anylog(request)
            # Return the form values as response
            return render(request, "form.html", {'form': user_info, 'data' : data })
            #return HttpResponse(data)
    else:
        # Display the html form
        user_info = AnyLogForm()
        return render(request, "form.html", {'form': user_info})

# ---------------------------------------------------------------------------------------
# Process the AnyLog command form
# ---------------------------------------------------------------------------------------
def process_anylog(request):
    '''
    :param request: The info needed to execute command to the AnyLog network
    :return: The data to display on the output form
    '''

    # Get the needed info from the form
    name = request.POST.get("name")
    email = request.POST.get("email")
    username = request.POST.get("username")

    # Call AnyLog using REST with the info provided

    data = [ 'Name:', name, '<br />', 'Email:', email, '<br />', 'Username:', username]

    return data     # Data returned from AnyLog or an Error Message