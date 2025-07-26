from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

# Create your views here.

def home_view(request):
    username = request.GET.get('username')  
    return render(request, 'dashboard/home.html', {'username': username})
