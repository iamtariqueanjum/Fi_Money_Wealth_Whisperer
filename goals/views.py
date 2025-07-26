from django.shortcuts import render, redirect, get_object_or_404
from .models import Goal, User
from django.http import HttpResponse

# Create your views here.

def goal_list(request, username):
    user = get_object_or_404(User, username=username)
    goals = Goal.objects.filter(user=user).order_by('-created_at')
    return render(request, 'goals/goal_list.html', {'user': user, 'goals': goals})

def goal_create(request, username):
    user = get_object_or_404(User, username=username)
    if request.method == 'POST':
        goal_text = request.POST.get('goal')
        target_amount = request.POST.get('target_amount')
        due_date = request.POST.get('due_date')
        primary_goal = request.POST.get('primary_goal')
        primary_goal_details = request.POST.get('primary_goal_details')
        secondary_goals = request.POST.getlist('secondary_goals')
        secondary_goal_timeline = request.POST.get('secondary_goal_timeline')
        risk_comfort = request.POST.get('risk_comfort')
        investment_horizon = request.POST.get('investment_horizon')
        major_life_events = request.POST.get('major_life_events')
        if goal_text:
            Goal.objects.create(
                user=user,
                goal=goal_text,
                target_amount=target_amount or None,
                due_date=due_date or None,
                primary_goal=primary_goal,
                primary_goal_details=primary_goal_details,
                secondary_goals=','.join(secondary_goals),
                secondary_goal_timeline=secondary_goal_timeline,
                risk_comfort=risk_comfort,
                investment_horizon=investment_horizon,
                major_life_events=major_life_events
            )
            return redirect('home')
    return render(request, 'goals/goal_form.html', {'user': user})

def goal_update(request, username, goal_id):
    user = get_object_or_404(User, username=username)
    goal = get_object_or_404(Goal, id=goal_id, user=user)
    if request.method == 'POST':
        goal_text = request.POST.get('goal')
        target_amount = request.POST.get('target_amount')
        due_date = request.POST.get('due_date')
        primary_goal = request.POST.get('primary_goal')
        primary_goal_details = request.POST.get('primary_goal_details')
        secondary_goals = request.POST.getlist('secondary_goals')
        secondary_goal_timeline = request.POST.get('secondary_goal_timeline')
        risk_comfort = request.POST.get('risk_comfort')
        investment_horizon = request.POST.get('investment_horizon')
        major_life_events = request.POST.get('major_life_events')
        if goal_text:
            goal.goal = goal_text
            goal.target_amount = target_amount or None
            goal.due_date = due_date or None
            goal.primary_goal = primary_goal
            goal.primary_goal_details = primary_goal_details
            goal.secondary_goals = ','.join(secondary_goals)
            goal.secondary_goal_timeline = secondary_goal_timeline
            goal.risk_comfort = risk_comfort
            goal.investment_horizon = investment_horizon
            goal.major_life_events = major_life_events
            goal.save()
            return redirect('home')
    return render(request, 'goals/goal_form.html', {'user': user, 'goal': goal})

def goal_delete(request, username, goal_id):
    user = get_object_or_404(User, username=username)
    goal = get_object_or_404(Goal, id=goal_id, user=user)
    if request.method == 'POST':
        goal.delete()
        return redirect('goal_list', username=username)
    return render(request, 'goals/goal_confirm_delete.html', {'user': user, 'goal': goal})
