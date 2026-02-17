from db_utils import get_db_connection

def get_recommended_users(user):
    """
    Expert Rule-Based Recommendation System Logic
    
    🎯 SCORING RULES:
    - Same Branch: +5 Points
    - Skill Match: +5 Points per matching skill
    - Same Domain: +3 Points
    - Same City: +2 Points
    
    🛡️ EXCLUSIONS:
    - Excludes self, already connected users, and pending requests.
    - Limits to Top 5 recommendations.
    """
    if not user or user.role not in ['student', 'alumni'] or not user.id:
        return []

    conn = get_db_connection()
    c = conn.cursor()

    # Determine target role (Students get Alumni, Alumni get Students)
    target_role = 'alumni' if user.role == 'student' else 'student'

    # Get already connected or pending user IDs to exclude
    excluded_ids = [user.id]
    
    # Already connected
    connections = c.execute(
        'SELECT user_id_1, user_id_2 FROM connections WHERE user_id_1 = ? OR user_id_2 = ?',
        (user.id, user.id)
    ).fetchall()
    for conn_row in connections:
        excluded_ids.append(conn_row['user_id_1'] if conn_row['user_id_1'] != user.id else conn_row['user_id_2'])
    
    # Pending requests (sent or received)
    pending = c.execute(
        'SELECT sender_id, receiver_id FROM connection_requests WHERE (sender_id = ? OR receiver_id = ?) AND status = "pending"',
        (user.id, user.id)
    ).fetchall()
    for p_row in pending:
        excluded_ids.append(p_row['sender_id'] if p_row['sender_id'] != user.id else p_row['receiver_id'])

    # Fetch potential candidates
    query = f"SELECT * FROM users WHERE role = ? AND id NOT IN ({','.join(['?']*len(excluded_ids))}) LIMIT 50"
    candidates = c.execute(query, [target_role] + excluded_ids).fetchall()

    recommendations = []
    user_skills = set([s.strip().lower() for s in (user.skills or "").split(',') if s.strip()])
    
    for cand in candidates:
        score = 0
        
        # Rule 1: Same branch
        if cand['branch'] and user.branch and cand['branch'].lower() == user.branch.lower():
            score += 5
            
        # Rule 2: Skill match (+5 per matching skill)
        cand_skills = [s.strip().lower() for s in (cand['skills'] or "").split(',') if s.strip()]
        for skill in cand_skills:
            if skill in user_skills:
                score += 5
                
        # Rule 3: Same domain
        if cand['current_domain'] and user.current_domain and cand['current_domain'].lower() == user.current_domain.lower():
            score += 3
            
        # Rule 4: Same city
        if cand['city'] and user.city and cand['city'].lower() == user.city.lower():
            score += 2
            
        if score > 0:
            recommendations.append({
                'id': cand['id'],
                'name': cand['name'],
                'role': cand['role'],
                'branch': cand['branch'],
                'skills': cand['skills'],
                'score': score,
                'profile_pic': cand['profile_pic'] or f"https://ui-avatars.com/api/?name={cand['name']}&background=random"
            })

    # Sort by score descending and return top 5
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    conn.close()
    
    # FUTURE SCOPE:
    # 1. AI-based recommendation using Sentence Transformers
    # 2. Collaborative filtering based on connection history
    # 3. Job recommendation based on skills/domain
    # 4. Mentor matching algorithms
    
    return recommendations[:5]
