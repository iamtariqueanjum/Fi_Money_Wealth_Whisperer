from django.shortcuts import render, redirect, get_object_or_404
from .models import Goal, User
from django.http import HttpResponse
from google.cloud import firestore

# Create your views here.

def goal_list(request, username):
    user = get_object_or_404(User, username=username)
    goals = Goal.objects.filter(user=user).order_by('-created_at')
    # Ensure secondary_goals is always a list for each goal
    for goal in goals:
        if hasattr(goal, 'secondary_goals') and isinstance(goal.secondary_goals, str):
            if ',' in goal.secondary_goals:
                goal.secondary_goals = [g.strip() for g in goal.secondary_goals.split(',')]
            elif goal.secondary_goals:
                goal.secondary_goals = [goal.secondary_goals]
            else:
                goal.secondary_goals = []
    return render(request, 'goals/goal_list.html', {'user': user, 'goals': goals})

# Flattening function from script.py

def flatten_dict_of_dicts(obj, parent_field=None):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, dict) and all(isinstance(val, dict) for val in v.values()):
                print(f"Flattening field: {parent_field + '.' if parent_field else ''}{k}")
                flattened = []
                for sub_name, sub_data in v.items():
                    if isinstance(sub_data, dict):
                        summary = {'name': sub_name}
                        summary.update(sub_data)
                        fields_str = ', '.join([f"{key}: {value}" for key, value in summary.items()])
                        print(f"{parent_field + '.' if parent_field else ''}{k} -> {fields_str}")
                        flattened.append(summary)
                obj[k] = flattened
                for item in flattened:
                    for subk, subv in item.items():
                        flatten_dict_of_dicts(subv, parent_field=f"{k}.{sub_name}")
            elif isinstance(v, list) and v and all(isinstance(item, dict) for item in v):
                print(f"Flattening list of dicts at field: {parent_field + '.' if parent_field else ''}{k}")
                flattened_list = []
                for idx, item in enumerate(v):
                    if isinstance(item, dict):
                        fields_str = ', '.join([f"{key}: {value}" for key, value in item.items()])
                        print(f"{parent_field + '.' if parent_field else ''}{k}[{idx}] -> {fields_str}")
                        flattened_list.append(item)
                    else:
                        flattened_list.append(str(item))
                obj[k] = flattened_list
                for item in flattened_list:
                    flatten_dict_of_dicts(item, parent_field=f"{k}")
            else:
                flatten_dict_of_dicts(v, parent_field=f"{parent_field + '.' if parent_field else ''}{k}")
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            if isinstance(item, dict):
                flatten_dict_of_dicts(item, parent_field=parent_field)
            elif not isinstance(item, (str, int, float, bool, type(None))):
                print(f"Converting non-serializable list item at {parent_field}[{idx}] to string.")
                obj[idx] = str(item)
    elif not isinstance(obj, (str, int, float, bool, type(None))):
        print(f"Converting non-serializable object at {parent_field} to string.")
        obj = str(obj)

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
            goal_obj = Goal.objects.create(
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
            # Prepare goal data for Firestore
            goal_data = {
                'goal_id': goal_obj.id,
                'goal': goal_text,
                'target_amount': target_amount,
                'due_date': due_date,
                'primary_goal': primary_goal,
                'primary_goal_details': primary_goal_details,
                'secondary_goals': secondary_goals,
                'secondary_goal_timeline': secondary_goal_timeline,
                'risk_comfort': risk_comfort,
                'investment_horizon': investment_horizon,
                'major_life_events': major_life_events
            }
            flatten_dict_of_dicts(goal_data, parent_field='goal')
            # Save to Firestore Users document
            try:
                db = firestore.Client()
                doc_ref = db.collection('Users').document(username)
                user_doc = doc_ref.get()
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                else:
                    user_data = {}
                # Append or create 'goals' field as a list
                goals_list = user_data.get('goals', [])
                goals_list.append(goal_data)
                user_data['goals'] = goals_list
                flatten_dict_of_dicts(user_data, parent_field='user')
                doc_ref.set(user_data)
                print(f"Goal for {username} saved/updated in Firestore Users document.")
            except Exception as e:
                print(f"Error saving goal to Firestore: {e}")
            return redirect('home')
    return render(request, 'goals/goal_form.html', {'user': user})

def goal_update(request, username, goal_id):
    user = get_object_or_404(User, username=username)
    # Try to fetch goal data from Firestore first
    goal_data = None
    try:
        db = firestore.Client()
        doc_ref = db.collection('Users').document(username)
        user_doc = doc_ref.get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            goals_list = user_data.get('goals', [])
            for g in goals_list:
                # goal_id may be int or str, so compare as str
                if str(g.get('goal_id')) == str(goal_id):
                    goal_data = g
                    break
            # Ensure secondary_goals is always a list
            if goal_data and 'secondary_goals' in goal_data and isinstance(goal_data['secondary_goals'], str):
                if ',' in goal_data['secondary_goals']:
                    goal_data['secondary_goals'] = [s.strip() for s in goal_data['secondary_goals'].split(',')]
                elif goal_data['secondary_goals']:
                    goal_data['secondary_goals'] = [goal_data['secondary_goals']]
                else:
                    goal_data['secondary_goals'] = []
    except Exception as e:
        print(f"Error fetching goal from Firestore: {e}")
    # If not found in Firestore, fall back to Django DB
    if not goal_data:
        goal = get_object_or_404(Goal, id=goal_id, user=user)
        # Convert secondary_goals to list for the form
        if hasattr(goal, 'secondary_goals') and isinstance(goal.secondary_goals, str):
            if ',' in goal.secondary_goals:
                secondary_goals_list = [g.strip() for g in goal.secondary_goals.split(',')]
            elif goal.secondary_goals:
                secondary_goals_list = [goal.secondary_goals]
            else:
                secondary_goals_list = []
        else:
            secondary_goals_list = goal.secondary_goals if hasattr(goal, 'secondary_goals') else []
        goal_data = {
            'goal': goal.goal,
            'target_amount': goal.target_amount,
            'due_date': goal.due_date,
            'primary_goal': goal.primary_goal,
            'primary_goal_details': goal.primary_goal_details,
            'secondary_goals': secondary_goals_list,
            'secondary_goal_timeline': goal.secondary_goal_timeline,
            'risk_comfort': goal.risk_comfort,
            'investment_horizon': goal.investment_horizon,
            'major_life_events': goal.major_life_events,
        }
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
    return render(request, 'goals/goal_form.html', {'user': user, 'goal': goal_data})

def goal_delete(request, username, goal_id):
    user = get_object_or_404(User, username=username)
    goal = get_object_or_404(Goal, id=goal_id, user=user)
    if request.method == 'POST':
        goal.delete()
        return redirect('goal_list', username=username)
    return render(request, 'goals/goal_confirm_delete.html', {'user': user, 'goal': goal})
