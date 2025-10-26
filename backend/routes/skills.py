from flask import Blueprint, jsonify, current_app
from utils.database import get_db
from flask_jwt_extended import jwt_required, get_jwt_identity

skills_bp = Blueprint('skills', __name__)

@skills_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """Get all unique categories from questions collection"""
    try:
        user_id = get_jwt_identity()
        current_app.logger.info(f"Fetching categories for user {user_id}")
        
        db = get_db()
        categories = db.questions.distinct('category')
        current_app.logger.info(f"Found categories: {categories}")
        
        return jsonify({
            'success': True,
            'categories': sorted(categories) if categories else []
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching categories: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
