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
- `REPLICATE_API_TOKEN`: API token for Replicate (LLM explanations)

4. Initialize database (create indexes):
```bash
python ../scripts/init_db.py
```

5. Run the development server:
```bash
flask run --host=0.0.0.0 --port=5000
```

## API Overview

### Learning Sessions
- `POST /lessons/start` — start a session (requires `skill_ids`, `type`)
- `POST /lessons/next` — get next question for the session
- `POST /lessons/submit` — submit answer; updates FSRS and user stats
- `GET  /lessons/progress-summary` — user progress summary
- `GET  /lessons/due-count` — number of due cards (FSRS)
- `POST /lessons/explain` — generate AI explanation for a question attempt

### Explanation API
- Caches explanations per `(question_id, selected_indices)` with 30‑day TTL.
- Backend normalizes formatting (step headers, bullet lists, inline math).

## Database Overview (key collections)

### users
```json
{
  "_id": ObjectId,
  "email": String,
  "password": String,
  "name": String,
  "selected_skills": [String],
  "stats": { "total_questions": Number, "correct_answers": Number, "current_streak": Number }
}
```

### questions
```json
{
  "_id": ObjectId,
  "question_text": String,
  "text": String,
  "type": String,
  "options": [String],
  "correct_answer": [Number],
  "category": String,
  "difficulty": Number
}
```

### lesson_sessions
```json
{
  "session_id": String,
  "user_id": ObjectId,
  "selected_categories": [String],
  "available_questions": [String],
  "used_questions": [String],
  "answers": [
    { "question_id": String, "answer": [Number], "correct": Boolean, "response_time": Number, "timestamp": Date }
  ],
  "completed": Boolean,
  "created_at": Date,
  "updated_at": Date,
  "last_answer_time": Date,
  "last_answer_correct": Boolean
}
```

### fsrs_cards
```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "question_id": ObjectId|String,
  "state": Number,
  "due_date": Date,
  "stability": Number,
  "difficulty": Number,
  "updated_at": Date
}
```

### explanation_cache
```json
{
  "key": String,  // "explanation:<question_id>:<sorted_indices>"
  "explanation": String,
  "created_at": Date,
  "question_id": String,
  "selected_indices": [Number]
}
```

Indexes are created by `scripts/init_db.py`, including TTL on `explanation_cache.created_at`.

## Testing

Run tests:
```bash
python -m unittest discover ../tests
```

Key test files:
- `test_fsrs_integration.py`: FSRS algorithm integration tests
- `test_fsrs_helper.py`: Helper tests
- `test_fsrs_card.py`: Model tests

## Notes
- Ensure environment variables are set (including `REPLICATE_API_TOKEN`) before using `/lessons/explain`.
