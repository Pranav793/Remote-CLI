from django.http.response import HttpResponse
from django.shortcuts import render
from django.http import HttpResponseRedirect

def home(request)->HttpResponse:
    return render(request, 'home.html')