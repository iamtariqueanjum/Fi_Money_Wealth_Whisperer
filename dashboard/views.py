import os
import json
from django.conf import settings
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

def get_user_net_worth(username):
    user_dir = os.path.join(settings.BASE_DIR, 'test_data_dir', username)
    net_worth_file = os.path.join(user_dir, 'fetch_net_worth.json')
    if not os.path.exists(net_worth_file):
        return None
    with open(net_worth_file, 'r') as f:
        data = json.load(f)
    try:
        return data['netWorthResponse']['totalNetWorthValue']['units']
    except (KeyError, TypeError):
        return None

def home_view(request):
    username = request.GET.get('username') 
    net_worth = get_user_net_worth(username)
    context = {'username': username}
    if net_worth:
        context['net_worth'] = net_worth
    else:
        context['net_worth_error'] = 'Please sync data to show your current net_worth.'
    return render(request, 'dashboard/home.html', context)
