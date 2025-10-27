# Backend Service Documentation

## Overview
The backend service is built with Flask and provides a RESTful API for the math learning platform. It integrates with MongoDB for data storage and implements the FSRS algorithm for spaced repetition learning.

## Technology Stack
- Python 3.10+
- Flask
- MongoDB
- JWT for authentication
- FSRS for spaced repetition

## Setup

### Local Development
1. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
```

Required environment variables:
- `MONGODB_URI`: MongoDB connection string
- `JWT_SECRET_KEY`: Secret key for JWT tokens
- `ENCRYPTION_KEY`: Key for password encryption
- `CORS_ORIGINS`: Allowed origins for CORS

4. Initialize database:
```bash
python ../scripts/init_db.py
python ../scripts/seed_questions.py
```

5. Run the development server:
```bash
flask run --host=0.0.0.0 --port=5000
```

## API Documentation

### Authentication

#### POST /auth/register
Register a new user.
```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "User Name"
}
```

#### POST /auth/login
Login and receive JWT token.
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

### Learning Sessions

#### GET /lessons/categories
Get available learning categories.

#### POST /lessons/start
Start a new learning session.
```json
{
  "categories": ["algebra", "geometry"]
}
```

#### GET /lessons/next
Get next question in current session.

#### POST /lessons/answer
Submit answer for current question.
```json
{
  "answer": ["A"] or "42",
  "time_spent": 30
}
```

#### GET /lessons/progress-summary
Get learning progress summary.

### User Management

#### GET /user/profile
Get user profile and statistics.

#### PUT /user/skills
Update user's selected learning skills.
```json
{
  "skills": ["algebra", "geometry"]
}
```

## Database Schema

### Users Collection
```json
{
  "_id": ObjectId,
  "email": String,
  "password": String,
  "name": String,
  "selected_skills": [String],
  "stats": {
    "total_questions": Number,
    "correct_answers": Number
  }
}
```

### Questions Collection
```json
{
  "_id": ObjectId,
  "question_text": String,
  "type": String,
  "options": [String],
  "correct_answer": [String],
  "category": String,
  "difficulty": Number
}
```

### Sessions Collection
```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "start_time": DateTime,
  "end_time": DateTime,
  "questions": [{
    "question_id": ObjectId,
    "answered": Boolean,
    "correct": Boolean,
    "time_spent": Number
  }]
}
```

### FSRS Cards Collection
```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "question_id": ObjectId,
  "state": FSRSState,
  "due": DateTime,
  "stability": Number,
  "difficulty": Number
}
```

## Error Handling
The API uses standard HTTP status codes and returns error responses in the format:
```json
{
  "error": "Error message",
  "status": 400
}
```

Common status codes:
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 500: Internal Server Error

## Testing

Run tests:
```bash
python -m unittest discover ../tests
```

Key test files:
- `test_fsrs_integration.py`: FSRS algorithm integration tests
- `test_auth.py`: Authentication endpoint tests
- `test_lessons.py`: Learning session endpoint tests
