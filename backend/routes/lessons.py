from flask import Blueprint, request, jsonify
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

lessons_bp = Blueprint('lessons', __name__)
limiter = Limiter(key_func=get_remote_address)

class LessonStartSchema(Schema):
    skill_ids = fields.List(fields.String(), required=True, validate=validate.Length(min=1, max=10))
    type = fields.String(required=True, validate=validate.OneOf(['initial', 'review', 'practice']))

def validate_input(schema_class):
    def decorator(f):
        def decorated_function(*args, **kwargs):
            schema = schema_class()
            try:
                data = schema.load(request.get_json())
                request.validated_data = data
                return f(*args, **kwargs)
            except ValidationError as err:
                return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
        return decorated_function
    return decorator

@lessons_bp.route('/start', methods=['POST'])
@limiter.limit("10 per minute")
@jwt_required()
@log_errors
@validate_input(LessonStartSchema)
def start_lesson():
    data = request.validated_data
    user_id = get_jwt_identity()
    skill_ids = [s.lower() for s in data['skill_ids']]
    lesson_type = data['type']
    db = Question.get_db() if hasattr(Question, 'get_db') else None
    if db is None:
        from utils.database import get_db
        db = get_db()
    import uuid
    from datetime import datetime
    session_id = str(uuid.uuid4())
    # Get user's seen questions
    user = db.users.find_one({'_id': ObjectId(user_id)})
    seen_ids = user.get('seen_question_ids', [])
    db.lesson_sessions.insert_one({
        'session_id': session_id,
        'user_id': user_id,
        'selected_skills': skill_ids,
        'question_ids': [],
        'created_at': datetime.utcnow()
    })
    # Find first question not in question_ids or seen_question_ids
    print(f"[DEBUG] skill_ids received: {skill_ids}")
    question_doc = db.questions.aggregate([
        {'$match': {'skill_category': {'$in': skill_ids}, '_id': {'$nin': seen_ids}}},
        {'$sample': {'size': 10}}
    ])
    question_doc = list(question_doc)
    if not question_doc:
        available_skills = list(db.questions.distinct('skill_category'))
        print(f"[DEBUG] No questions found. Available skill_category values: {available_skills}")
        return jsonify({'error': 'No questions found for selected skills', 'available_skills': available_skills, 'requested_skills': skill_ids}), 404
    import random
    first_question = random.choice(question_doc)
    db.lesson_sessions.update_one(
        {'session_id': session_id},
        {'$push': {'question_ids': first_question['_id']}}
    )
    # Add to user's seen_question_ids (do NOT increment total_questions_answered here)
    db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$addToSet': {'seen_question_ids': first_question['_id']}}
    )
    question = {
        'id': str(first_question['_id']),
        'text': first_question.get('question_text') or first_question.get('text'),
        'options': first_question.get('options', []),
        'skill_category': first_question.get('skill_category'),
        'difficulty': first_question.get('difficulty_level', first_question.get('difficulty', None)),
        'explanation': first_question.get('explanation', None)
    }
    return jsonify({'session_id': session_id, 'question': question})

@lessons_bp.route('/next', methods=['POST'])
@jwt_required()
def next_question():
    data = request.get_json()
    session_id = data.get('session_id')
    db = Question.get_db() if hasattr(Question, 'get_db') else None
    if db is None:
        from utils.database import get_db
        db = get_db()
    session = db.lesson_sessions.find_one({'session_id': session_id})
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    skill_ids = [s.lower() for s in session['selected_skills']]
    used_ids = session['question_ids']
    user = db.users.find_one({'_id': ObjectId(session['user_id'])})
    seen_ids = user.get('seen_question_ids', [])
    # Exclude both session and user seen questions
    exclude_ids = list(set(used_ids) | set(seen_ids))
    question_doc = db.questions.aggregate([
        {'$match': {'skill_category': {'$in': skill_ids}, '_id': {'$nin': exclude_ids}}},
        {'$sample': {'size': 10}}
    ])
    question_doc = list(question_doc)
    if not question_doc:
        return jsonify({'message': 'Session complete'}), 200
    import random
    next_q = random.choice(question_doc)
    db.lesson_sessions.update_one(
        {'session_id': session_id},
        {'$push': {'question_ids': next_q['_id']}}
    )
    db.users.update_one(
        {'_id': ObjectId(session['user_id'])},
        {'$addToSet': {'seen_question_ids': next_q['_id']}}
    )
    question = {
        'id': str(next_q['_id']),
        'text': next_q.get('question_text') or next_q.get('text'),
        'options': next_q.get('options', []),
        'skill_category': next_q.get('skill_category'),
        'difficulty': next_q.get('difficulty_level', next_q.get('difficulty', None)),
        'explanation': next_q.get('explanation', None)
    }
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
    try:
        user = User.get_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        db = Question.get_db() if hasattr(Question, 'get_db') else None
        if db is None:
            from utils.database import get_db
            db = get_db()
        skills_progress = {}
        seen_ids = user.seen_question_ids
        seen_obj_ids = [ObjectId(qid) if not isinstance(qid, ObjectId) else qid for qid in seen_ids]
        if seen_obj_ids:
            questions = db.questions.find({'_id': {'$in': seen_obj_ids}})
            skill_count = {}
            for q in questions:
                skill = q.get('skill_category', '').lower()
                if skill:
                    skill_count[skill] = skill_count.get(skill, 0) + 1
            for skill in [s.lower() for s in getattr(user, 'selected_skills', [])]:
                skills_progress[skill] = {'answered': skill_count.get(skill, 0)}
        else:
            for skill in [s.lower() for s in getattr(user, 'selected_skills', [])]:
                skills_progress[skill] = {'answered': 0}
        total = getattr(user, 'total_questions_answered', 0)
        correct = getattr(user, 'correct_answers', 0)
        accuracy_rate = round((correct / total) * 100, 2) if total > 0 else 0
        return jsonify({
            'total_questions': total,
            'accuracy_rate': accuracy_rate,
            'skills_progress': skills_progress
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lessons_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit_answer():
    data = request.get_json()
    session_id = data.get('session_id')
    question_id = data.get('question_id')
    answer_index = data.get('answer_index')
    db = Question.get_db() if hasattr(Question, 'get_db') else None
    if db is None:
        from utils.database import get_db
        db = get_db()
    session = db.lesson_sessions.find_one({'session_id': session_id})
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    user_id = session['user_id']
    question = db.questions.find_one({'_id': ObjectId(question_id)})
    if not question:
        return jsonify({'error': 'Question not found'}), 404
    is_correct = False
    correct_index = question.get('correct_answer')
    if correct_index is not None and int(answer_index) == int(correct_index):
        is_correct = True
        db.users.update_one({'_id': ObjectId(user_id)}, {'$inc': {'correct_answers': 1}})
    # Always increment total_questions_answered (already done in /next, but for robustness)
    db.users.update_one({'_id': ObjectId(user_id)}, {'$inc': {'total_questions_answered': 1}})
    # Optionally, store answer history (not implemented here)
    return jsonify({'correct': is_correct, 'correct_index': correct_index, 'explanation': question.get('explanation', '')})
