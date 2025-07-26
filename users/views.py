from django.shortcuts import render, redirect, reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        # user = authenticate(request, username=username, password=password)
        if username is not None and password is not None:
            return redirect(f'/dashboard/home/?username={username}')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'users/login.html')

@csrf_exempt
def logout_view(request):
    if request.method == 'POST':
        # logout(request)
        return redirect('login')