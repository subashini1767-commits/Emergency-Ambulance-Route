# Emergency Ambulance Route Optimization System

This project is a Python Flask web application for ambulance drivers to quickly identify the most suitable hospital after an accident or medical emergency. It includes a secure demo login flow, emergency-location lookup, hospital ranking, and a map display with the route to the recommended hospital.

## Features

- Driver account registration, login, and validation
- Dashboard after successful login
- Manual emergency address entry and browser geolocation support
- Hospital search using sample SQLite-backed data across Tamil Nadu
- Ranking logic based on beds, travel time, distance, and traffic condition
- Leaflet + OpenStreetMap map visualization
- Emergency route summary and navigation prompt
- Logout button and session-based access control

## Project structure

- `app.py` — creates and runs the Flask application
- `config.py` — site configuration and database path
- `database/db.py` — SQLite database and sample data setup
- `routes/auth.py` — login and logout endpoints
- `routes/emergency.py` — emergency lookup, hospital search, and route API
- `services/geocoding_service.py` — Tamil Nadu location coordinate lookup adapter
- `services/hospital_service.py` — hospital filtering and best-hospital selection
- `templates/` — HTML pages for login and dashboard
- `static/` — CSS and JavaScript frontend files

## Local setup

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
cd "c:\Users\Admin\Desktop\emergency ambulance routeee\Emergency Ambulance Route"
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks scripts, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Initialize the database

The SQLite database is initialized automatically when the app starts. The first launch creates the tables and inserts demo data.

### 4. Start the Flask server

```powershell
python app.py
```

### 5. Open the application in a browser

Open:

```text
http://127.0.0.1:5000/login
```

## Python-only frontend

The Python-only Streamlit frontend is in `streamlit_app.py`. Run the Flask backend in one terminal and the Streamlit frontend in another:

```powershell
python app.py
streamlit run streamlit_app.py
```

Open the Streamlit URL shown in the terminal, normally `http://localhost:8501`.

## How to test the emergency workflow

1. Log in with the demo account.
2. On the dashboard, enter a Tamil Nadu emergency address such as `Anna Nagar, Chennai` or click "Use My Location".
3. Click "Find Tamil Nadu Hospital & Route".
4. Review the hospital list and the recommended hospital.
5. Click "Start Navigation" to trigger the route summary.
6. Use "Enter Another Emergency Location" to reset and search again.

## Important note

This version uses realistic sample hospital data stored locally in SQLite across Tamil Nadu. It does not claim live real-time bed availability unless a real hospital API is later connected. The hospital service layer is intentionally separated so it can be replaced with an external provider in the future.
