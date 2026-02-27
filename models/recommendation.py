from db_utils import get_db_connection
import logging
import os

# Suppress verbose AI library logs
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

AI_AVAILABLE = True # Assume available, will check inside lazy loader

class AIRecommendationEngine:
    def __init__(self):
        self._model = None
        self._initialized = False

    @property
    def model(self):
        global AI_AVAILABLE
        if not self._initialized:
            try:
                # Lazy import heavy libraries
                from sentence_transformers import SentenceTransformer
                import transformers
                transformers.logging.set_verbosity_error()
                
                print("[AI] Initializing Recommendation Engine (SentenceTransformer)...")
                # Use a lightweight model for local performance
                self._model = SentenceTransformer('all-MiniLM-L6-v2')
                print("[AI] Engine ready.")
                AI_AVAILABLE = True
            except (ImportError, Exception) as e:
                logging.error(f"AI Model Error: {e}")
                print(f"[AI] Model loading failed or not installed: {e}. AI features will be disabled.")
                AI_AVAILABLE = False
            self._initialized = True
        return self._model

    def get_semantic_score(self, text1, text2):
        if not self.model or not text1 or not text2:
            return 0
        try:
            from sentence_transformers import util
            emb1 = self.model.encode(text1, convert_to_tensor=True)
            emb2 = self.model.encode(text2, convert_to_tensor=True)
            return round(util.cos_sim(emb1, emb2).item() * 10)
        except Exception:
            return 0

# Initialize global engine
ai_engine = AIRecommendationEngine()


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

    # PRE-FETCH: Current user's direct connection IDs for mutual score
    user_conn_ids = set()
    user_conns_db = c.execute(
        'SELECT user_id_1, user_id_2 FROM connections WHERE user_id_1 = ? OR user_id_2 = ?',
        (user.id, user.id)
    ).fetchall()
    for uc in user_conns_db:
        user_conn_ids.add(uc['user_id_1'] if uc['user_id_1'] != user.id else uc['user_id_2'])

    # Fetch potential candidates
    query = f"SELECT * FROM users WHERE role = ? AND id NOT IN ({','.join(['?']*len(excluded_ids))}) LIMIT 50"
    candidates = c.execute(query, [target_role] + excluded_ids).fetchall()

    # PRE-FETCH: Connections for all candidates to calculate mutuals efficiently
    cand_conn_map = {}
    if candidates:
        candidate_ids = [cand['id'] for cand in candidates]
        placeholders = ','.join(['?'] * len(candidate_ids))
        all_cand_conns = c.execute(
            f'SELECT user_id_1, user_id_2 FROM connections WHERE user_id_1 IN ({placeholders}) OR user_id_2 IN ({placeholders})',
            candidate_ids + candidate_ids
        ).fetchall()
        
        cand_conn_map = {cid: set() for cid in candidate_ids}
        for row in all_cand_conns:
            u1, u2 = row['user_id_1'], row['user_id_2']
            if u1 in cand_conn_map: cand_conn_map[u1].add(u2)
            if u2 in cand_conn_map: cand_conn_map[u2].add(u1)

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

        # Rule 3: Mutual Connections (+2 per mutual connection)
        if cand['id'] in cand_conn_map:
            mutuals = cand_conn_map[cand['id']].intersection(user_conn_ids)
            score += (len(mutuals) * 2)
                
        # Rule 3: Same domain
        if cand['current_domain'] and user.current_domain and cand['current_domain'].lower() == user.current_domain.lower():
            score += 3
            
        # Rule 4: Same city
        if cand['city'] and user.city and cand['city'].lower() == user.city.lower():
            score += 2
            
        # Rule 5: AI Semantic Match (+0 to 10 points based on Bio/Interests)
        if AI_AVAILABLE and ai_engine.model:
            # Defensive access for object attributes
            u_bio = getattr(user, 'bio', '') or ''
            u_interests = getattr(user, 'interests', '') or ''
            text1 = f"{u_bio} {u_interests}"
            
            # Dictionary access for candidates (Safe check for sqlite3.Row)
            cand_dict = dict(cand)
            c_bio = cand_dict.get('bio', '') or ''
            c_interests = cand_dict.get('interests', '') or ''
            text2 = f"{c_bio} {c_interests}"
            
            if text1.strip() and text2.strip():
                score += ai_engine.get_semantic_score(text1, text2)

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

def get_recommended_jobs(user):
    """
    Job Recommendation Engine
    - Matches user skills against job requirements.
    - Limits to Top 5 matches.
    """
    if not user or user.role != 'student' or not user.id:
        return []

    conn = get_db_connection()
    c = conn.cursor()
    
    # Fetch all jobs
    jobs = c.execute('''
        SELECT j.*, u.name as posted_by_name 
        FROM jobs j 
        JOIN users u ON j.posted_by = u.id 
        ORDER BY j.created_at DESC
    ''').fetchall()
    
    user_skills = set([s.strip().lower() for s in (user.skills or "").split(',') if s.strip()])
    recommended = []
    
    for job in jobs:
        job_skills = set([s.strip().lower() for s in (job['required_skills'] or "").split(',') if s.strip()])
        match_count = len(user_skills.intersection(job_skills))
        
        # AI Semantic Job Matching
        if AI_AVAILABLE and ai_engine.model:
            u_bio = getattr(user, 'bio', '') or ''
            u_skills = getattr(user, 'skills', '') or ''
            user_text = f"{u_bio} {u_skills}"
            job_text = f"{job['title']} {job['description']}"
            semantic_boost = ai_engine.get_semantic_score(user_text, job_text) / 2
            match_count += semantic_boost

        if match_count > 0:
            job_dict = dict(job)
            job_dict['match_score'] = match_count
            recommended.append(job_dict)
            
    # Sort by match_score descending
    recommended.sort(key=lambda x: x['match_score'], reverse=True)
    conn.close()
    
    return recommended[:5]
