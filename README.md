# Math Learning System with Spaced Repetition

## Overview
A full-stack math learning platform using Flask (Python), MongoDB, Vue 3, Pinia, Tailwind CSS, and FSRS spaced repetition algorithm.

## Features
- User authentication (JWT)
- FSRS-based spaced repetition
- Lesson management and progress tracking
- Responsive Vue.js frontend
- Dockerized deployment

## Quickstart

### 1. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Set environment variables in .env
# JWT_SECRET_KEY: `import secrets; print(secrets.token_urlsafe(32))`
# ENCRYPTION_KEY: `frome cryptography.fernet import Fernet; print(Fernet.generate_key().decod())`
python3 ../scripts/init_db.py
# If SSL error occured: 
# `/Applications/Python\ 3.x/Install\ Certificates.command`
# `pip install --upgrade certifi`
python3 ../scripts/seed_questions.py
flask run --host=0.0.0.0 --port=5000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. Run with Docker
```bash
docker-compose up --build
```

## Testing
- Backend: `python -m unittest discover ../tests`
- Frontend: `npm run test`

## Project Structure
- `backend/` - Flask API, models, utils
- `frontend/` - Vue 3 app
- `scripts/` - DB init/seed scripts
- `tests/` - Backend tests

## References
See `implementation_guide.md` for full technical details and code samples.
