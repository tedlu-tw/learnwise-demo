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
        
        # Try both field names and merge results
        categories_by_category = db.questions.distinct('category')
        categories_by_skill = db.questions.distinct('skill_category')
        
        # Combine and deduplicate categories
        all_categories = list(set([c.lower() for c in categories_by_category + categories_by_skill if c]))
        
        current_app.logger.info(f"Found categories: {all_categories}")
        
        if not all_categories:
            # Return default categories if none found in database
            default_categories = ['arithmetic', 'algebra', 'geometry', 'trigonometry', 'calculus']
            current_app.logger.warning("No categories found in DB, using defaults")
            return jsonify({
                'success': True,
                'categories': default_categories,
                'is_default': True
            })
            
        return jsonify({
            'success': True,
            'categories': sorted(all_categories),
            'is_default': False
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching categories: {str(e)}", exc_info=True)
        # Return default categories on error
        default_categories = ['arithmetic', 'algebra', 'geometry', 'trigonometry', 'calculus']
        return jsonify({
            'success': True,
            'categories': default_categories,
            'is_default': True,
            'error': str(e)
        })
