# Learning Strategy Recommendation System

## 실행 방법

### 0) Node.js install
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
source ~/.zshrc

# Node LTS install
nvm install --lts
nvm use --lts

### 1) Backend
cd backend
python3 -m venv .<your project name>
source .<your project name>/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000


### 2) Frontend
cd frontend
npm install
npm run dev
