from flask import Blueprint, request, jsonify, current_app
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
        return jsonify({'error': '該電子郵件信箱已被註冊'}), 409
    if User.find_by_username(data['username']):
        return jsonify({'error': '該使用者名稱已被註冊'}), 409
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
    try:
        data = request.get_json()
        
        # Validate input
        if not data:
            current_app.logger.error("No JSON data in request")
            return jsonify({'error': 'Invalid request format'}), 400
            
        if not data.get('email') or not data.get('password'):
            current_app.logger.error("Missing email or password in login request")
            return jsonify({'error': '請輸入電子郵件信箱和密碼'}), 400
            
        current_app.logger.info(f"Login attempt for email: {data.get('email')}")
        
        user = User.find_by_email(data['email'])
        if not user:
            current_app.logger.warning(f"Login failed: User not found for email {data.get('email')}")
            return jsonify({'error': '電子郵件信箱或密碼有誤'}), 401
            
        if not user.check_password(data['password']):
            current_app.logger.warning(f"Login failed: Invalid password for email {data.get('email')}")
            return jsonify({'error': '電子郵件信箱或密碼有誤'}), 401
            
        user.update_last_login()
        access_token = create_access_token(identity=str(user.id))
        
        # Return user info including selected_skills
        user_data = {
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'selected_skills': user.selected_skills
        }
        
        current_app.logger.info(f"Login successful for user: {user.username}")
        return jsonify({
            'access_token': access_token,
            'user': user_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

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
