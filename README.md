# Math Learning System with Spaced Repetition

## Overview
A full-stack adaptive math learning platform using Flask (Python), MongoDB, Vue 3, Pinia, Tailwind CSS, and the FSRS (Free Spaced Repetition Scheduler) algorithm. The system provides personalized learning experiences by adapting to each student's performance and optimizing review intervals.

## Features
- Adaptive learning with FSRS spaced repetition algorithm
- User authentication with JWT
- Multiple question types support (single answer & multiple choice)
- Real-time progress tracking and analytics
- Skill-based learning paths
- Robust math rendering with KaTeX (inline/display, bold, bullets)
- AI-generated explanations with consistent step titles and bullet lists
- Responsive Vue.js frontend with modern UI
- RESTful API with Flask backend
- MongoDB for flexible data storage
- Dockerized deployment for easy setup
- Test coverage

## Quickstart

### 1. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Set environment variables in .env
# JWT_SECRET_KEY: `python - <<'PY'\nimport secrets; print(secrets.token_urlsafe(32))\nPY`
# ENCRYPTION_KEY: `python - <<'PY'\nfrom cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\nPY`
# REPLICATE_API_TOKEN: your token for /lessons/explain
python3 ../scripts/init_db.py
python3 ../scripts/seed_sample_data.py  # optional sample data
flask run --host=0.0.0.0 --port=5000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env
# Configure VITE_API_URL (e.g. http://localhost:5000 or http://localhost:5050 when using Docker)
npm run dev
```

### 3. Run with Docker
```bash
docker-compose up --build
```

The application will be available at:
- Frontend (Docker): http://localhost/
- Backend API (Docker): http://localhost:5050
- Frontend (local dev default): http://localhost:5173
- Backend API (local dev): http://localhost:5000

## Testing
### Backend Tests
```bash
cd backend
python -m unittest discover ../tests
```

### Frontend Tests
```bash
cd frontend
npm run test
```

## Project Structure
```
.
├── backend/           # Flask API server
│   ├── models/       # Database models
│   ├── routes/       # API endpoints
│   └── utils/        # Helper functions
├── frontend/         # Vue 3 application
│   ├── src/
│   │   ├── components/  # Vue components (incl. MathDisplay, ExplanationPanel)
│   │   ├── views/      # Page components
│   │   ├── stores/     # Pinia stores
│   │   └── services/   # API services
│   └── tests/      # Frontend tests
├── scripts/        # Database setup and seeding
└── tests/         # Backend tests
```

## Documentation
- [Backend Documentation](backend/README.md) - API endpoints and database schema
- [Frontend Documentation](frontend/README.md) - Components and state management

## Environment Variables

### Backend (.env)
```
MONGODB_URI=mongodb://localhost:27017/innoserve-dev
JWT_SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key
CORS_ORIGINS=*
REPLICATE_API_TOKEN=your-replicate-token
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:5000
```

## Notes
- Explanations cache with 30-day TTL is enabled via `scripts/init_db.py`.
- The explanation viewer shows a disclaimer: 「AI 生成結果僅供參考。」
