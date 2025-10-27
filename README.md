# Math Learning System with Spaced Repetition

## Overview
A full-stack adaptive math learning platform using Flask (Python), MongoDB, Vue 3, Pinia, Tailwind CSS, and the FSRS (Free Spaced Repetition Scheduler) algorithm. The system provides personalized learning experiences by adapting to each student's performance and optimizing review intervals.

## Features
- Adaptive learning with FSRS spaced repetition algorithm
- User authentication with JWT
- Multiple question types support (single answer & multiple choice)
- Real-time progress tracking and analytics
- Skill-based learning paths
- Interactive math formula rendering with KaTeX
- Responsive Vue.js frontend with modern UI
- RESTful API with Flask backend
- MongoDB for flexible data storage
- Dockerized deployment for easy setup
- Comprehensive test coverage

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
# ENCRYPTION_KEY: `from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())`
python3 ../scripts/init_db.py
# If SSL error occurs: 
# `/Applications/Python\ 3.x/Install\ Certificates.command`
# `pip install --upgrade certifi`
python3 ../scripts/seed_questions.py
flask run --host=0.0.0.0 --port=5000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env
# Configure VITE_API_URL in .env
npm run dev
```

### 3. Run with Docker
```bash
# Create and configure .env files first
docker-compose up --build
```

The application will be available at:
- Frontend: http://localhost:8080
- Backend API: http://localhost:5000

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
│   │   ├── components/  # Vue components
│   │   ├── views/      # Page components
│   │   ├── stores/     # Pinia stores
│   │   └── services/   # API services
│   └── tests/      # Frontend tests
├── scripts/        # Database setup and seeding
├── tests/         # Backend tests
└── question_source/ # Source materials
```

## Documentation
- [Backend Documentation](backend/README.md) - API endpoints and database schema
- [Frontend Documentation](frontend/README.md) - Components and state management
- [Implementation Guide](implementation_guide.md) - Technical architecture and decisions
- [FSRS Documentation](fsrs_readme.md) - Spaced repetition implementation details

## Environment Variables

### Backend (.env)
```
MONGODB_URI=mongodb+srv://...
JWT_SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key
CORS_ORIGINS=http://localhost:8080
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:5000
VITE_AUTH_TOKEN_KEY=auth_token
```

## License
GPLv3 License - See LICENSE file for details.
