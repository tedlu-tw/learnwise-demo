from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.fsrs_helper import FSRSHelper
from models.user import User
from models.question import Question
from models.fsrs_card import FSRSCard
from utils.security import log_errors
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from marshmallow import Schema, fields, validate, ValidationError
from bson import ObjectId
from datetime import datetime, timezone
import logging
import re
from fsrs import State, Rating
from utils.database import get_db

logger = logging.getLogger(__name__)
lessons_bp = Blueprint('lessons', __name__)
limiter = Limiter(key_func=get_remote_address)

class LessonStartSchema(Schema):
    skill_ids = fields.List(fields.String(), required=True, validate=validate.Length(min=1, max=10))
    type = fields.String(required=True, validate=validate.OneOf(['initial', 'review', 'practice']))

@lessons_bp.route('/start', methods=['POST'])
@limiter.limit("10 per minute")
@jwt_required()
@log_errors
def start_lesson():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate input
        schema = LessonStartSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            logger.error(f"Validation error in start_lesson: {err.messages}")
            return jsonify({'error': 'Validation failed', 'details': err.messages}), 400

        user_id = get_jwt_identity()
        categories = [s.lower() for s in validated_data['skill_ids']]
        lesson_type = validated_data['type']

        logger.info(f"Starting lesson for user {user_id} with categories: {categories}")

        db = Question.get_db() if hasattr(Question, 'get_db') else None
        if db is None:
            from utils.database import get_db
            db = get_db()

        # Verify user exists
        user = db.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            logger.error(f"User {user_id} not found")
            return jsonify({'error': 'User not found'}), 404

        # Log available categories first
        available_cats = list(db.questions.distinct('category'))
        logger.info(f"Available categories in DB: {available_cats}")
        logger.info(f"Requested categories: {categories}")
        
        # Find questions for selected categories
        pipeline = [
            {'$match': {'category': {'$in': categories}}},
            {'$project': {'_id': 1, 'category': 1, 'question_text': 1, 'text': 1, 'options': 1}}
        ]
        questions = list(db.questions.aggregate(pipeline))
        logger.info(f"Found {len(questions)} questions matching categories: {categories}")
        
        if not questions:
            # Try case-insensitive search
            pipeline = [
                {'$match': {'category': {'$regex': '|'.join(map(re.escape, categories)), '$options': 'i'}}},
                {'$project': {'_id': 1, 'category': 1, 'question_text': 1, 'text': 1, 'options': 1}}
            ]
            questions = list(db.questions.aggregate(pipeline))
            logger.info(f"Case-insensitive search found {len(questions)} questions")
        
        if not questions:
            logger.error(f"No questions found for categories: {categories}")
            return jsonify({'error': 'No questions found for selected categories'}), 404
            
        # Limit to 10 random questions
        import random
        if len(questions) > 10:
            questions = random.sample(questions, 10)

        # Create a new session
        session_id = str(ObjectId())
        session = {
            'session_id': session_id,
            'user_id': user_id,
            'selected_categories': categories,
            'type': lesson_type,
            'available_questions': [str(q['_id']) for q in questions],
            'used_questions': [],
            'completed': False,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        db.lesson_sessions.insert_one(session)
        logger.info(f"Created new lesson session {session_id} for user {user_id}")

        return jsonify({
            'session_id': session_id,
            'total_questions': len(questions),
            'categories': categories,
            'type': lesson_type
        })

    except Exception as e:
        logger.error(f"Error in start_lesson: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@lessons_bp.route('/next', methods=['POST'])
@jwt_required()
def next_question():
    data = request.get_json()
    session_id = data.get('session_id')
    logger.info(f"Fetching next question for session: {session_id}")
    
    db = Question.get_db() if hasattr(Question, 'get_db') else None
    if db is None:
        from utils.database import get_db
        db = get_db()
    
    session = db.lesson_sessions.find_one({'session_id': session_id})
    if not session:
        logger.error(f"Session not found: {session_id}")
        return jsonify({'error': 'Session not found'}), 404
    
    # Get session state
    skill_ids = [s.lower() for s in session['selected_categories']]
    available_questions = session.get('available_questions', [])
    used_questions = session.get('used_questions', [])
    
    logger.info(f"Session found. Categories: {skill_ids}, Available: {len(available_questions)}, Used: {len(used_questions)}")
    
    # Log sample question to check schema
    sample_question = db.questions.find_one({'category': {'$in': skill_ids}})
    if sample_question:
        logger.info(f"Sample question fields: {list(sample_question.keys())}")
        logger.info(f"Sample question category: {sample_question.get('category')}")
    
    # Check if we've used all available questions
    if not available_questions:
        logger.info("No more available questions - session complete")
        return jsonify({'message': 'Session complete'}), 200
    
    # Get next question from available questions
    if available_questions:
        next_q_id = available_questions[0]
        next_q = db.questions.find_one({'_id': ObjectId(next_q_id)})
        
        if next_q:
            user_id = session['user_id']
            # Check if user has seen this question before
            existing_card = FSRSCard.get_by_user_and_question(user_id, next_q_id)
            # A question is considered for review if it exists and has been reviewed before
            is_review = existing_card is not None and existing_card.last_review is not None

            # Update session state
            db.lesson_sessions.update_one(
                {'session_id': session_id},
                {
                    '$pop': {'available_questions': -1},  # Remove from front
                    '$push': {'used_questions': next_q_id}
                }
            )
            
            logger.info(f"Using {'review' if is_review else 'new'} question: {next_q_id}")
            
            # Create or get FSRS card
            FSRSHelper.ensure_card(user_id, str(next_q['_id']))
        else:
            logger.error(f"Question {next_q_id} not found in database")
            return jsonify({'error': 'Question not found'}), 404
    else:
        logger.info("No more available questions")
        return jsonify({'message': 'Session complete'}), 200
        
        # Log the first question to debug category matching
        if question_doc:
            logger.info(f"Sample new question - category: {question_doc[0].get('category')}, id: {question_doc[0].get('_id')}")
    
    # Update seen_question_ids since this is a new question
    db.users.update_one(
        {'_id': ObjectId(session['user_id'])},
        {'$addToSet': {'seen_question_ids': next_q['_id']}}
    )
    
    # Ensure FSRS card exists for this question/user
    FSRSHelper.ensure_card(session['user_id'], str(next_q['_id']))
    # Log full question document for debugging
    logger.info(f"Selected question document fields: {list(next_q.keys())}")
    
    # Convert correct_answer to correct_indices if needed
    correct_indices = next_q.get('correct_answer', [])
    if not isinstance(correct_indices, list):
        correct_indices = [correct_indices] if correct_indices is not None else []
    
    question = {
        'id': str(next_q['_id']),
        'text': next_q.get('question_text') or next_q.get('text'),
        'options': next_q.get('options', []),
        'category': next_q.get('category'),  # Use consistent field name
        'difficulty': next_q.get('difficulty_level', next_q.get('difficulty', None)),
        'explanation': next_q.get('explanation', None),
        'is_review': is_review,
        'type': next_q.get('type', 'single'),  # Add type field with default as single
        'correct_indices': correct_indices  # Use consistent field name with submit endpoint
    }
    
    # Validate question data before returning
    if not question['text'] or not question['options']:
        logger.error(f"Invalid question data: {question}")
        return jsonify({'error': 'Invalid question data'}), 500
        
    logger.info(f"Returning question: {question['id']} with {len(question['options'])} options")
    return jsonify({'question': question})

@lessons_bp.route('/due-count', methods=['GET'])
@jwt_required()
def get_due_count():
    user_id = get_jwt_identity()
    try:
        due_cards = FSRSHelper.get_due_cards(user_id, limit=100)
        return jsonify({'due_count': len(due_cards), 'review_count': len(due_cards)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lessons_bp.route('/progress-summary', methods=['GET'])
@jwt_required()
def get_progress_summary():
    user_id = get_jwt_identity()
    logger.info(f"Getting progress summary for user: {user_id}")
    try:
        # Get the database connection
        db = get_db()
        
        # Get the user and their skills
        user = db.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Get selected skills (case-insensitive)
        selected_skills = [s.lower() for s in user.get('selected_skills', [])]
        
        # Initialize the response structure
        skills_progress = {}
        total_questions = 0
        total_correct = 0
        total_answered = 0
        
        # Get total questions per skill
        pipeline = [
            {'$match': {'category': {'$in': selected_skills}}},
            {'$group': {
                '_id': '$category',
                'total': {'$sum': 1}
            }}
        ]
        skill_totals = {doc['_id']: doc['total'] for doc in db.questions.aggregate(pipeline)}
        
        # Get completed questions per skill with more reliable counting
        pipeline = [
            {'$match': {'user_id': ObjectId(user_id)}},
            {'$lookup': {
                'from': 'questions',
                'localField': 'question_id',
                'foreignField': '_id',
                'as': 'question'
            }},
            {'$unwind': '$question'},
            {'$group': {
                '_id': '$question.category',
                'answered': {'$sum': 1},
                'total_correct': {'$sum': {'$cond': {'if': {'$eq': ['$is_correct', True]}, 'then': 1, 'else': 0}}},
                'questions': {'$addToSet': '$question_id'}  # Track unique questions
            }},
            {'$project': {
                '_id': 1,
                'answered': {'$size': '$questions'},  # Count unique questions only
                'total_correct': 1
            }}
        ]
        skill_progress = db.lesson_reports.aggregate(pipeline)
        
        # Calculate overall stats and build response
        for skill in selected_skills:
            skill_stats = next((s for s in skill_progress if s['_id'].lower() == skill.lower()), {'answered': 0, 'total_correct': 0})
            total_for_skill = skill_totals.get(skill, 0)
            
            skills_progress[skill] = {
                'answered': skill_stats['answered'],
                'total': total_for_skill,
                'correct': skill_stats['total_correct']
            }
            
            total_questions += total_for_skill
            total_correct += skill_stats['total_correct']
            total_answered += skill_stats['answered']
            
        # Calculate mastery rate (weighted by skill progress)
        mastery_rate = 0
        if total_questions > 0:
            mastery_weights = {skill: total/total_questions for skill, total in skill_totals.items()}
            for skill, progress in skills_progress.items():
                if progress['total'] > 0:
                    skill_mastery = (progress['correct'] / progress['total']) * 100
                    mastery_rate += skill_mastery * mastery_weights.get(skill, 0)
        
        # Get FSRS stats
        fsrs_stats = db.fsrs_cards.aggregate([
            {'$match': {'user_id': ObjectId(user_id)}},
            {'$group': {
                '_id': None,
                'learning_count': {'$sum': {'$cond': [{'$eq': ['$state', 1]}, 1, 0]}},
                'review_count': {'$sum': {'$cond': [{'$eq': ['$state', 2]}, 1, 0]}},
                'relearning_count': {'$sum': {'$cond': [{'$eq': ['$state', 3]}, 1, 0]}}
            }}
        ])
        fsrs_stats = next(fsrs_stats, {'learning_count': 0, 'review_count': 0, 'relearning_count': 0})
        
        return jsonify({
            'total_questions': total_answered,
            'accuracy_rate': round((total_correct / total_answered * 100), 2) if total_answered > 0 else 0,
            'debug_stats': {
                'total_correct': total_correct,
                'total_answered': total_answered,
                'skills_count': len(selected_skills)
            },
            'mastery_rate': round(mastery_rate, 2),
            'skills_progress': skills_progress,
            'learning_stats': {
                'learning': fsrs_stats['learning_count'],
                'review': fsrs_stats['review_count'],
                'relearning': fsrs_stats['relearning_count']
            }
        })
    except Exception as e:
        logger.error(f"Error in progress-summary: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

class AnswerSubmissionSchema(Schema):
    session_id = fields.String(required=True)
    question_id = fields.String(required=True)
    answer_indices = fields.List(fields.Integer(), required=True)
    response_time = fields.Float(required=True, validate=validate.Range(min=0))

@lessons_bp.route('/submit', methods=['POST'])
@jwt_required()
@log_errors
def submit_answer():
    """Process answer submission with FSRS integration"""
    try:
        # Validate input
        schema = AnswerSubmissionSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            logger.error(f"Validation error in submit_answer: {err.messages}")
            return jsonify({'error': 'Validation failed', 'details': err.messages}), 400

        user_id = get_jwt_identity()
        session_id = data['session_id']
        question_id = data['question_id']
        answer_indices = data['answer_indices']
        response_time = data['response_time']

        # Get the question and session
        db = get_db()
        question = db.questions.find_one({'_id': ObjectId(question_id)})
        session = db.lesson_sessions.find_one({'session_id': session_id})

        if not question or not session:
            logger.error(f"Question or session not found - question_id: {question_id}, session_id: {session_id}")
            return jsonify({'error': 'Question or session not found'}), 404

        # Validate answer
        correct_indices = question.get('correct_answer', [])
        if not isinstance(correct_indices, list):
            correct_indices = [correct_indices] if correct_indices is not None else []
        is_correct = sorted(answer_indices) == sorted(correct_indices)
        
        # Get or create FSRS card
        card = FSRSHelper.ensure_card(user_id, question_id)
        if not card:
            logger.error(f"Failed to create/get FSRS card for user {user_id}, question {question_id}")
            return jsonify({'error': 'Internal server error'}), 500

        # Get user stats for streak
        user_stats = db.users.find_one(
            {'_id': ObjectId(user_id)},
            {'stats': 1}
        ) or {'stats': {}}
        
        streak = user_stats.get('stats', {}).get('current_streak', 0)
        
        # Review card with performance data
        helper = FSRSHelper()
        performance_data = {
            'is_correct': is_correct,
            'response_time': response_time,
            'question_difficulty': question.get('difficulty', 3),
            'consecutive_correct': streak if is_correct else 0
        }
        
        updated_card, review_log = helper.review_card(
            card=card,
            performance_data=performance_data,
            question_data=question
        )

        # Update session
        db.sessions.update_one(
            {'session_id': session_id},
            {
                '$push': {
                    'used_questions': question_id,
                    'answers': {
                        'question_id': question_id,
                        'answer': answer_indices,
                        'correct': is_correct,
                        'response_time': response_time,
                        'timestamp': datetime.now(timezone.utc)
                    }
                },
                '$set': {
                    'last_answer_time': datetime.now(timezone.utc),
                    'last_answer_correct': is_correct
                }
            }
        )

        # Initialize user stats if they don't exist
        db.users.update_one(
            {'_id': ObjectId(user_id), 'stats': {'$exists': False}},
            {'$set': {'stats': {
                'total_questions': 0,
                'correct_answers': 0,
                'current_streak': 0
            }}}
        )

        # Update user stats - handle streak properly
        if is_correct:
            update = {
                '$inc': {
                    'stats.total_questions': 1,
                    'stats.correct_answers': 1,
                    'stats.current_streak': 1
                }
            }
        else:
            update = {
                '$inc': {
                    'stats.total_questions': 1
                },
                '$set': {
                    'stats.current_streak': 0  # Reset streak on incorrect answer
                }
            }

        db.users.update_one(
            {'_id': ObjectId(user_id)},
            update
        )

        # Prepare response with learning feedback
        next_review_delta = round(updated_card.days_until_due, 1) if updated_card.due_date else 0.0
        feedback_message = {
            Rating.Again: "Keep practicing! You'll get it next time.",
            Rating.Hard: "Good effort! This one needs more review.",
            Rating.Good: "Well done! You're making progress.",
            Rating.Easy: "Excellent! You've mastered this concept."
        }.get(review_log.rating, "Keep going!")

        return jsonify({
            'correct': is_correct,
            'feedback': {
                'message': feedback_message,
                'next_review': str(updated_card.due_date) if updated_card.due_date else None,
                'days_until_review': round(next_review_delta, 1),
                'state': updated_card.state_name,
                'stability': round(updated_card.stability, 2),
                'difficulty': FSRSCard.convert_difficulty_to_db(updated_card.difficulty),
                'correct': is_correct,  # Add correct flag to feedback object
                'correct_indices': correct_indices  # Rename from correct_answer to match frontend
            },
            'selected_indices': answer_indices,  # Rename from selected_answer to match frontend
            'streak': streak + 1 if is_correct else 0,
            'explanation': question.get('explanation', '')  # Include question explanation if available
        })

    except Exception as e:
        logger.error(f"Error in submit_answer: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
