# Fi_Money_Wealth_Whisperer

## Steps to Start and Set Up the Application

### 1. **Clone the Repository**
```bash
git clone <your-repo-url>
cd Fi_Money_Wealth_Whisperer
```

### 2. **Set Up Python Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. **Install Dependencies**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. **Google Cloud Setup**
- Ensure you have a Google Cloud project with Firestore and Vertex AI APIs enabled.
- Download your Google Cloud service account key JSON file and place it in the project root (e.g., `hack2skill-wealth-whisperer-ee65f31bfa33.json`).
- Set the environment variable:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/hack2skill-wealth-whisperer-ee65f31bfa33.json"
```

### 5. **(Optional) Ingest Sample Data**
- Use the provided `script.py` to upload sample user data from `test_data_dir/` to Firestore:
```bash
python script.py
```

### 6. **Run Django Migrations**
```bash
python manage.py migrate
```

### 7. **Start the Django Development Server**
```bash
python manage.py runserver
```
- Access the app at [http://127.0.0.1:8000/users/login/](http://127.0.0.1:8000/users/login/)


## **Notes**
- Ensure your Google Cloud service account has the necessary IAM roles for Firestore and Vertex AI.
- Update environment variables and credentials as needed for your deployment environment.
- For troubleshooting, check Django server logs and Google Cloud Console for errors.
