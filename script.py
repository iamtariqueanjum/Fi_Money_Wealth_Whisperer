import os
import json
from google.cloud import firestore

def upload_user_data(user_id, user_dir):
    print(f"Processing user: {user_id}")
    # Initialize Firestore client
    try:
        db = firestore.Client()
        print("Firestore client initialized.")
    except Exception as e:
        print(f"Error initializing Firestore client: {e}")
        return

    # Prepare a dictionary to hold all JSON data
    data = {}

    # Loop through all JSON files in the user's directory
    if not os.path.isdir(user_dir):
        print(f"Directory {user_dir} does not exist. Skipping user {user_id}.")
        return

    for filename in os.listdir(user_dir):
        if filename.endswith('.json'):
            field_name = filename.replace('.json', '')
            file_path = os.path.join(user_dir, filename)
            print(f"Reading file: {file_path}")
            with open(file_path, 'r') as f:
                try:
                    content = json.load(f)
                    # Recursively flatten any dict-of-dicts structure
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
                    flatten_dict_of_dicts(content, parent_field=field_name)
                    data[field_name] = content
                    print(f"Loaded data for field: {field_name}")
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    # Upload as a single document in the 'Users' collection
    try:
        doc_ref = db.collection('Users').document(user_id)
        doc_ref.set(data)
        print(f"Uploaded data for {user_id} to Firestore.")
    except Exception as e:
        print(f"Error uploading data for {user_id}: {e}")

if __name__ == "__main__":
    user_ids = ["UserA", "UserB", "UserC", "UserD", "UserE", "UserF", "UserG", "UserH", "UserI", "UserJ", "UserK", "UserL", "UserM", "UserN", "UserO", "UserP"]
    for user_id in user_ids:
        user_dir = os.path.join("test_data_dir", user_id)
        upload_user_data(user_id, user_dir)
