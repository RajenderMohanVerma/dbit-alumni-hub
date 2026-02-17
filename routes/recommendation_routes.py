from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from models.recommendation import get_recommended_users

recommendation_bp = Blueprint('recommendation', __name__)

@recommendation_bp.route('/recommendations')
@login_required
def recommendations():
    """
    API endpoint to fetch top 5 recommended connections for the current user.
    """
    if current_user.role not in ['student', 'alumni']:
        return jsonify([])
        
    try:
        recs = get_recommended_users(current_user)
        return jsonify(recs)
    except Exception as e:
        # Standard expert practice: log and return empty rather than breaking UI
        print(f"Expert-level error handling: Error in recommendations: {e}")
        return jsonify([])
