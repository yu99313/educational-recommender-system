# Learning Strategy Recommendation System

## Requirements

- Python: `3.13.2` (current dev environment)
- Node.js: installed locally (LTS recommended)

## How to use

### 1) Backend

```bash
cd backend
python3 -m venv <project_name>
source <project_name>/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```
