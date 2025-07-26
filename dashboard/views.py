import os
import json
from django.conf import settings
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

def get_user_file_data(username, filename):
    data = None
    user_dir = os.path.join(settings.BASE_DIR, 'test_data_dir', username)
    file_path = os.path.join(user_dir, filename)
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def home_view(request):
    username = request.GET.get('username')
    net_worth = get_user_file_data(username, 'fetch_net_worth.json')
    credit_report = get_user_file_data(username, 'fetch_credit_report.json')
    epf = get_user_file_data(username, 'fetch_epf_details.json')
    mf = get_user_file_data(username, 'fetch_mf_transactions.json')
    stocks = get_user_file_data(username, 'fetch_stock_transactions.json')
    recent_transactions = get_user_file_data(username, 'fetch_bank_transactions.json')
    credit_score = None
    if credit_report:
        try:
            credit_score = credit_report['creditReports'][0]['creditReportData']['score']['bureauScore']
        except (KeyError, IndexError, TypeError):
            credit_score = None
    if net_worth:
        try:
            net_worth = net_worth['netWorthResponse']['totalNetWorthValue']['units']
        except (KeyError, TypeError):
            net_worth = None
    context = {
        'username': username,
        'net_worth': net_worth,
        'credit_report': credit_report,
        'epf': epf,
        'mf': mf,
        'stocks': stocks,
        'recent_transactions': recent_transactions,
        'credit_score': credit_score,
    }
    return render(request, 'dashboard/home.html', context)
