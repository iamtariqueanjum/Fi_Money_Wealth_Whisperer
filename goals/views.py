from django.shortcuts import render, redirect, get_object_or_404
from .models import Goal, User
from django.http import HttpResponse
from google.cloud import firestore
from django.views.decorators.csrf import csrf_exempt

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

def generate_context(request, username):
    from google.cloud import firestore
    db = firestore.Client()
    doc_ref = db.collection('Users').document(username)
    doc = doc_ref.get()
    if not doc.exists:
        return HttpResponse('No user data found.', content_type='text/plain', status=404)
    user_data = doc.to_dict()
    context_lines = []
    for col_name, data in user_data.items():
        if isinstance(data, dict):
            keys = list(data.keys())
            preview = str({k: data[k] for k in keys[:2]}) if keys else str(data)
        elif isinstance(data, list):
            preview = f"List of {len(data)} items"
        else:
            preview = str(data)
        context_lines.append(f"{col_name}: {preview}")
    context_str = "\n".join(context_lines)
    print("\n--- RAG CONTEXT ---\n" + context_str + "\n--- END RAG CONTEXT ---\n")
    return HttpResponse(context_str, content_type="text/plain")

# Simple in-memory cache for recommendations
recommendations_cache = {}

@csrf_exempt
def generate_recommendations(request, username):
    from django.urls import reverse
    import requests
    import time
    import google.generativeai as genai
    from chromadb import Client, EmbeddingFunction
    import os
    import ast
    import re
    import json as pyjson

    # Check cache first
    now = time.time()
    cache_key = f"{username}_recommendations"
    cache_entry = recommendations_cache.get(cache_key)
    if cache_entry and cache_entry['expiry'] > now:
        return HttpResponse(cache_entry['data'], content_type="text/plain")

    # Build the URL for the context endpoint
    context_url = request.build_absolute_uri(reverse('generate_context', args=[username]))
    # Fetch the context string from the context endpoint
    try:
        context_response = requests.get(context_url)
        context_str = context_response.text
    except Exception as e:
        return HttpResponse(f'Error fetching context: {e}', content_type='text/plain', status=500)

    print("\n--- RAG CONTEXT ---\n" + context_str + "\n--- END RAG CONTEXT ---\n")

    # --- Chunking logic ---
    from google.cloud import firestore
    db = firestore.Client()
    doc_ref = db.collection('Users').document(username)
    doc = doc_ref.get()
    user_data = doc.to_dict() if doc.exists else {}
    chunks = []
    chunks = chunk_goals(user_data, chunks)
    chunks = chunk_bank_transactions(user_data, chunks)
    chunks = chunk_epf(user_data, chunks)
    chunks = chunk_net_worth(user_data, chunks)
    chunks = chunk_mf_transactions(user_data, chunks)
    chunks = chunk_credit_report(user_data, chunks)

    # Add more chunking as needed for other data types

    print(f"\n--- CHUNKS ---\n" + "\n".join(chunks) + "\n--- END CHUNKS ---\n")

    class GeminiEmbeddingFunction(EmbeddingFunction):
        def __call__(self, input):
            embeddings_list = genai.embed_content(
                model="models/text-embedding-004",
                content=input,
                task_type="retrieval_document"
            )["embedding"]
            return [e for e in embeddings_list]

    chroma_client = Client()
    user_financial_context_collection = chroma_client.get_or_create_collection(
        name="user_financial_contexts",
        embedding_function=GeminiEmbeddingFunction()
    )

    # Store each chunk as a separate document
    for i, chunk in enumerate(chunks):
        doc_id = f"{username}_chunk_{i}"
        existing_docs = user_financial_context_collection.get(ids=[doc_id])
        if existing_docs['ids']:
            user_financial_context_collection.update(ids=[doc_id], documents=[chunk])
        else:
            user_financial_context_collection.add(documents=[chunk], ids=[doc_id])
    print(f"Stored {len(chunks)} chunks for {username} in ChromaDB.")

    # --- Retrieve top N relevant chunks for a user query or default ---
    if request.method == 'POST':
        try:
            body = pyjson.loads(request.body.decode())
            user_query = body.get('query', '').strip()
        except Exception:
            user_query = ''
    else:
        user_query = ''
    if not user_query:
        user_query = "What are my top financial priorities based on my goals?"
    query_embedding = genai.embed_content(
        model="models/text-embedding-004",
        content=user_query,
        task_type="retrieval_query"
    )["embedding"]
    results = user_financial_context_collection.query(query_embeddings=[query_embedding], n_results=5)
    retrieved_chunks = [doc[0] for doc in results['documents']] if results['documents'] else []
    print(f"\n--- Retrieved Chunks (for query: {user_query}) ---\n" + "\n".join(retrieved_chunks) + "\n--- END Retrieved Chunks ---\n")

    # --- Build prompt for Gemini LLM ---
    prompt = (
        "User context (financial facts):\n" + "\n".join(retrieved_chunks) +
        f"\n\nUser query: {user_query}\n" +
        "\nInstructions:\n"
        "1. Provide 3-5 short, actionable financial recommendations for the user.\n"
        "2. For each recommendation, add a one-sentence explanation using the user's financial data and the supporting articles above.\n"
        "Format your response as:\n"
        "1. [Recommendation 1]\n   - Reason: [Explanation]\n"
        "2. [Recommendation 2]\n   - Reason: [Explanation]\n"
        "and so on."
    )
    print(f"\n--- Gemini LLM Prompt ---\n{prompt}\n--- END Prompt ---\n")

    # --- Call Gemini LLM for recommendations ---
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
    llm_response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.4, "max_output_tokens": 512}
    )
    raw_response = llm_response.text if hasattr(llm_response, 'text') else "No recommendations generated."

    # --- Parse for actionable items (bullets or numbered) ---
    points = [line.strip() for line in raw_response.split('\n') if re.match(r'^(\*|-|\d+\.)', line.strip()) and len(line.strip()) > 10]
    if not points:
        # fallback: split by double newlines or periods
        points = [x.strip() for x in re.split(r'\n\n|\.\s', raw_response) if len(x.strip()) > 10]
    recommendations = '\n'.join(points)

    # Store in cache for 1 hour
    recommendations_cache[cache_key] = {'data': recommendations, 'expiry': now + 3600}

    return HttpResponse(recommendations, content_type="text/plain")

def chunk_goals(user_data, chunks):
    for goal in user_data.get('goals', []):
        chunk = (
            f"Goal: {goal.get('goal', '')}. "
            f"Target: {goal.get('target_amount', '')} INR. "
            f"Due: {goal.get('due_date', '')}. "
            f"Primary: {goal.get('primary_goal', '')}. "
            f"Secondary: {', '.join(goal.get('secondary_goals', []))}."
        )
        chunks.append(chunk)
    return chunks

def chunk_bank_transactions(user_data, chunks):
    import ast
    bank_data = user_data.get('fetch_bank_transactions', {})
    if isinstance(bank_data, dict):
        bank_transactions = bank_data.get('bankTransactions', [])
    elif isinstance(bank_data, list):
        bank_transactions = bank_data
    else:
        bank_transactions = []
    for bank in bank_transactions:
        bank_name = bank.get('bank', '')
        for t in bank.get('txns', [])[:5]:
            try:
                txn = ast.literal_eval(t) if isinstance(t, str) else t
                amount, narration, date, txn_type, mode, balance = txn
                type_map = {1: 'CREDIT', 2: 'DEBIT', 3: 'OPENING', 4: 'INTEREST', 5: 'TDS', 6: 'INSTALLMENT', 7: 'CLOSING', 8: 'OTHERS'}
                chunk = (
                    f"Bank: {bank_name}. Transaction on {date}: {type_map.get(txn_type, 'N/A')} of {amount} INR "
                    f"({narration}) via {mode}. Balance: {balance} INR."
                )
                chunks.append(chunk)
            except Exception:
                continue
    return chunks

def chunk_epf(user_data, chunks):
    epf_data = user_data.get('fetch_epf_details', {})
    if isinstance(epf_data, dict):
        epf_accounts = epf_data.get('uanAccounts', [])
    elif isinstance(epf_data, list):
        epf_accounts = epf_data
    else:
        epf_accounts = []
    for epf in epf_accounts:
        raw = epf.get('rawDetails', {})
        for est in raw.get('est_details', []):
            employer = est.get('est_name', '')
            pf_balance = est.get('pf_balance', {}).get('net_balance', '')
            doj = est.get('doj_epf', '')
            doe = est.get('doe_epf', '')
            office = est.get('office', '')
            member_id = est.get('member_id', '')
            emp_share = est.get('pf_balance', {}).get('employee_share', {}).get('balance', '')
            emp_credit = est.get('pf_balance', {}).get('employee_share', {}).get('credit', '')
            er_share = est.get('pf_balance', {}).get('employer_share', {}).get('balance', '')
            er_credit = est.get('pf_balance', {}).get('employer_share', {}).get('credit', '')
            chunk = (
                f"EPF Employer: {employer} (Office: {office}, Member ID: {member_id}). "
                f"Net PF Balance: {pf_balance} INR. "
                f"Employee Share: {emp_share} (Credit: {emp_credit}), "
                f"Employer Share: {er_share} (Credit: {er_credit}). "
                f"DOJ: {doj}. DOE: {doe}."
            )
            chunks.append(chunk)
    return chunks

def chunk_net_worth(user_data, chunks):
    nw_data = user_data.get('fetch_net_worth', {})
    if isinstance(nw_data, dict):
        nw = nw_data.get('netWorthResponse', {})
    elif isinstance(nw_data, list):
        nw = nw_data[0] if nw_data else {}
    else:
        nw = {}
    for asset in nw.get('assetValues', []):
        attr = asset.get('netWorthAttribute', '').replace('ASSET_TYPE_', '').replace('_', ' ').title()
        value = asset.get('value', {}).get('units', '')
        chunk = f"Asset: {attr}. Value: {value} INR."
        chunks.append(chunk)
    return chunks

def chunk_mf_transactions(user_data, chunks):
    import ast
    mf_data = user_data.get('fetch_mf_transactions', {})
    if isinstance(mf_data, dict):
        mf_transactions = mf_data.get('mfTransactions', [])
    elif isinstance(mf_data, list):
        mf_transactions = mf_data
    else:
        mf_transactions = []
    for mf in mf_transactions:
        scheme = mf.get('schemeName', '')
        for txn in mf.get('txns', [])[-3:]:  # Last 3 transactions
            try:
                tx = ast.literal_eval(txn) if isinstance(txn, str) else txn
                order_type = "BUY" if tx[0] == 1 else "SELL"
                chunk = (
                    f"Mutual Fund: {scheme}. {order_type} {tx[4]} units on {tx[1]}. "
                    f"Purchase Price: {tx[2]}, Units: {tx[3]}."
                )
                chunks.append(chunk)
            except Exception:
                continue
    return chunks

def chunk_credit_report(user_data, chunks):
    cr_data = user_data.get('fetch_credit_report', {})
    if isinstance(cr_data, dict):
        reports = cr_data.get('creditReports', [])
    elif isinstance(cr_data, list):
        reports = cr_data
    else:
        reports = []
    for report in reports:
        crd = report.get('creditReportData', {})
        # Handle both list and dict for creditReportData
        if isinstance(crd, list):
            crd_items = crd
        elif isinstance(crd, dict):
            crd_items = [crd]
        else:
            crd_items = []
        score = None
        active_accounts = None
        outstanding = None
        recent_accounts = []
        for item in crd_items:
            if item.get('name') == 'score':
                score = item.get('bureauScore')
            if item.get('name') == 'creditAccount':
                for acc in item.get('creditAccountSummary', []):
                    if acc.get('name') == 'account':
                        active_accounts = acc.get('creditAccountActive')
                    if acc.get('name') == 'totalOutstandingBalance':
                        outstanding = acc.get('outstandingBalanceAll')
                for acc in item.get('creditAccountDetails', []):
                    recent_accounts.append(f"{acc.get('subscriberName', '')} (Current Balance: {acc.get('currentBalance', '')} INR, Opened: {acc.get('openDate', '')})")
        if score:
            chunks.append(f"Credit Score: {score}.")
        if active_accounts:
            chunks.append(f"Active Credit Accounts: {active_accounts}.")
        if outstanding:
            chunks.append(f"Total Outstanding Balance: {outstanding} INR.")
        for acc in recent_accounts[:3]:
            chunks.append(f"Recent Credit Account: {acc}.")
    return chunks
