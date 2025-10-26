// MongoDB Index Creation Script for Math Learning System
// Run this in the MongoDB shell or with `mongosh scripts/index_setup.js`

db = db.getSiblingDB('learnwise-demo')

// Users collection
print('Creating indexes for users...')
db.users.createIndex({ "email": 1 }, { unique: true })
db.users.createIndex({ "username": 1 }, { unique: true })

// Questions collection
print('Creating indexes for questions...')
db.questions.createIndex({ "skill_category": 1, "difficulty_level": 1 })
db.questions.createIndex({ "tags": 1 })
db.questions.createIndex({ "sub_topic": 1 })

// FSRS Cards collection
print('Creating indexes for fsrs_cards...')
db.fsrs_cards.createIndex({ "user_id": 1, "due_date": 1 })
db.fsrs_cards.createIndex({ "user_id": 1, "question_id": 1 }, { unique: true })
db.fsrs_cards.createIndex({ "due_date": 1, "state": 1 })

// Lesson Reports collection
print('Creating indexes for lesson_reports...')
db.lesson_reports.createIndex({ "user_id": 1, "timestamp": -1 })
db.lesson_reports.createIndex({ "session_id": 1 })
db.lesson_reports.createIndex({ "user_id": 1, "question_id": 1 })

// Lesson Sessions collection
print('Creating indexes for lesson_sessions...')
db.lesson_sessions.createIndex({ "user_id": 1, "start_time": -1 })
db.lesson_sessions.createIndex({ "user_id": 1, "completed": 1 })

print('All indexes created.')
