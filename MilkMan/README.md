# MilkMan (Django + React)

Monorepo layout:

- `DjangoProject/`: Django REST backend (SQL Server via ODBC)
- `frontend/`: React frontend (CRA)

## Backend (Windows, PowerShell)

```powershell
cd MilkMan\DjangoProject
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt

# Create a .env based on .env.example
copy .env.example .env

.\venv\Scripts\python manage.py migrate
.\venv\Scripts\python manage.py runserver 8001
```

## Frontend

```powershell
cd MilkMan\frontend
npm install

# Optional: configure API base URL
copy .env.example .env

npm start
```

Frontend defaults to calling `http://localhost:8001/api` unless `REACT_APP_API_BASE_URL` is set.

