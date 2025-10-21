from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.user import User
from utils.security import PasswordManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from bson import ObjectId

auth_bp = Blueprint('auth', __name__)

# Rate limit login
limiter = Limiter(key_func=get_remote_address)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    required_fields = ['username', 'email', 'password']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} required'}), 400
    if User.find_by_email(data['email']):
        return jsonify({'error': 'Email already registered'}), 409
    if User.find_by_username(data['username']):
        return jsonify({'error': 'Username already taken'}), 409
    try:
        user = User.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )
        return jsonify({'message': 'User created successfully', 'user_id': str(user.id)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    user = User.find_by_email(data['email'])
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    user.update_last_login()
    access_token = create_access_token(identity=str(user.id))
    # Return user info including selected_skills
    user_data = {
        'id': str(user.id),
        'username': user.username,
        'email': user.email,
        'selected_skills': getattr(user, 'selected_skills', []),
        'role': getattr(user, 'role', 'user')
    }
    return jsonify({'access_token': access_token, 'user': user_data})

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.get_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user_data = {
        'id': str(user.id),
        'username': user.username,
        'email': user.email,
        'selected_skills': getattr(user, 'selected_skills', []),
        'role': getattr(user, 'role', 'user')
    }
    return jsonify(user_data)

@auth_bp.route('/skills', methods=['PATCH'])
@jwt_required()
def update_skills():
    user_id = get_jwt_identity()
    data = request.get_json()
    selected_skills = data.get('selected_skills')
    if not isinstance(selected_skills, list):
        return jsonify({'error': 'selected_skills must be a list'}), 400
    # Normalize all skills to lowercase
    selected_skills = [s.lower() for s in selected_skills]
    db = User.get_db()
    result = db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'selected_skills': selected_skills}})
    if result.modified_count == 1:
        return jsonify({'message': 'Skills updated successfully'})
    else:
        return jsonify({'error': 'User not found or no change'}), 404
