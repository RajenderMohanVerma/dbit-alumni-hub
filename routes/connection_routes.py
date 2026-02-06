from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
import sqlite3
from flask_mail import Mail, Message
from app import app, get_db_connection, mail

connection_bp = Blueprint('connection', __name__, url_prefix='/api/connection-request')

@connection_bp.route('/send', methods=['POST'])
@login_required
def send_connection_request():
    """Send a connection request to another user"""
    try:
        data = request.get_json()
        receiver_id = data.get('receiver_id')
        
        if not receiver_id:
            return jsonify({'success': False, 'error': 'Receiver ID required'}), 400
        
        if int(receiver_id) == current_user.id:
            return jsonify({'success': False, 'error': 'Cannot send request to yourself'}), 400
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # Check if already connected
        existing = c.execute(
            'SELECT * FROM connections WHERE (user_id_1 = ? AND user_id_2 = ?) OR (user_id_1 = ? AND user_id_2 = ?)',
            (current_user.id, receiver_id, receiver_id, current_user.id)
        ).fetchone()
        
        if existing:
            conn.close()
            return jsonify({'success': False, 'error': 'Already connected'}), 400
        
        # Check if request already exists
        existing_request = c.execute(
            'SELECT * FROM connection_requests WHERE sender_id = ? AND receiver_id = ? AND status = "pending"',
            (current_user.id, receiver_id)
        ).fetchone()
        
        if existing_request:
            conn.close()
            return jsonify({'success': False, 'error': 'Request already sent'}), 400
        
        # Insert connection request
        try:
            c.execute(
                'INSERT INTO connection_requests (sender_id, receiver_id, status) VALUES (?, ?, "pending")',
                (current_user.id, receiver_id)
            )
            conn.commit()
            
            # Send email notification
            sender = c.execute('SELECT * FROM users WHERE id = ?', (current_user.id,)).fetchone()
            receiver = c.execute('SELECT * FROM users WHERE id = ?', (receiver_id,)).fetchone()
            
            if sender and receiver:
                subject = f"New Connection Request from {sender['name']}"
                body = f"""
                Hi {receiver['name']},
                
                {sender['name']} has sent you a connection request!
                
                Click the link below to view their profile and respond to the request:
                http://yourapp.com/profile/{sender['id']}
                
                Best regards,
                Alumni Hub Team
                """
                
                msg = Message(subject=subject, recipients=[receiver['email']], body=body)
                try:
                    mail.send(msg)
                except Exception as e:
                    print(f"Email error: {e}")
            
            conn.close()
            return jsonify({'success': True, 'message': 'Connection request sent'}), 200
            
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'success': False, 'error': 'Request already exists'}), 400
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@connection_bp.route('/accept/<int:request_id>', methods=['POST'])
@login_required
def accept_connection_request(request_id):
    """Accept a connection request"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get the request
        req = c.execute(
            'SELECT * FROM connection_requests WHERE id = ? AND receiver_id = ?',
            (request_id, current_user.id)
        ).fetchone()
        
        if not req:
            conn.close()
            return jsonify({'success': False, 'error': 'Request not found'}), 404
        
        # Update request status
        c.execute(
            'UPDATE connection_requests SET status = "accepted" WHERE id = ?',
            (request_id,)
        )
        
        # Create connection (ensure user_id_1 < user_id_2 for consistency)
        user_id_1 = min(req['sender_id'], current_user.id)
        user_id_2 = max(req['sender_id'], current_user.id)
        
        c.execute(
            'INSERT OR IGNORE INTO connections (user_id_1, user_id_2) VALUES (?, ?)',
            (user_id_1, user_id_2)
        )
        
        conn.commit()
        
        # Send email notification
        sender = c.execute('SELECT * FROM users WHERE id = ?', (req['sender_id'],)).fetchone()
        receiver = c.execute('SELECT * FROM users WHERE id = ?', (current_user.id,)).fetchone()
        
        if sender and receiver:
            subject = f"{receiver['name']} accepted your connection request"
            body = f"""
            Hi {sender['name']},
            
            {receiver['name']} has accepted your connection request!
            
            You can now connect and collaborate together.
            
            Best regards,
            Alumni Hub Team
            """
            
            msg = Message(subject=subject, recipients=[sender['email']], body=body)
            try:
                mail.send(msg)
            except Exception as e:
                print(f"Email error: {e}")
        
        conn.close()
        return jsonify({'success': True, 'message': 'Connection request accepted'}), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@connection_bp.route('/reject/<int:request_id>', methods=['POST'])
@login_required
def reject_connection_request(request_id):
    """Reject a connection request"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get the request
        req = c.execute(
            'SELECT * FROM connection_requests WHERE id = ? AND receiver_id = ?',
            (request_id, current_user.id)
        ).fetchone()
        
        if not req:
            conn.close()
            return jsonify({'success': False, 'error': 'Request not found'}), 404
        
        # Update request status
        c.execute(
            'UPDATE connection_requests SET status = "rejected" WHERE id = ?',
            (request_id,)
        )
        
        conn.commit()
        
        # Send email notification
        sender = c.execute('SELECT * FROM users WHERE id = ?', (req['sender_id'],)).fetchone()
        receiver = c.execute('SELECT * FROM users WHERE id = ?', (current_user.id,)).fetchone()
        
        if sender and receiver:
            subject = f"{receiver['name']} rejected your connection request"
            body = f"""
            Hi {sender['name']},
            
            {receiver['name']} has rejected your connection request.
            
            You can try connecting with other professionals on the platform.
            
            Best regards,
            Alumni Hub Team
            """
            
            msg = Message(subject=subject, recipients=[sender['email']], body=body)
            try:
                mail.send(msg)
            except Exception as e:
                print(f"Email error: {e}")
        
        conn.close()
        return jsonify({'success': True, 'message': 'Connection request rejected'}), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@connection_bp.route('/pending', methods=['GET'])
@login_required
def get_pending_requests():
    """Get all pending connection requests for current user"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        requests = c.execute('''
            SELECT cr.*, u.name, u.email, u.profile_pic
            FROM connection_requests cr
            JOIN users u ON cr.sender_id = u.id
            WHERE cr.receiver_id = ? AND cr.status = "pending"
            ORDER BY cr.created_at DESC
        ''', (current_user.id,)).fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'requests': [
                {
                    'id': req['id'],
                    'sender_id': req['sender_id'],
                    'sender_name': req['name'],
                    'sender_email': req['email'],
                    'sender_pic': req['profile_pic'],
                    'created_at': req['created_at']
                }
                for req in requests
            ]
        }), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@connection_bp.route('/list', methods=['GET'])
@login_required
def get_connections():
    """Get all connections for current user"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        connections = c.execute('''
            SELECT u.id, u.name, u.email, u.role, u.profile_pic, c.connected_at
            FROM connections c
            JOIN users u ON (
                (c.user_id_1 = ? AND u.id = c.user_id_2) OR
                (c.user_id_2 = ? AND u.id = c.user_id_1)
            )
            ORDER BY c.connected_at DESC
        ''', (current_user.id, current_user.id)).fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'connections': [
                {
                    'id': conn['id'],
                    'name': conn['name'],
                    'email': conn['email'],
                    'role': conn['role'],
                    'profile_pic': conn['profile_pic'],
                    'connected_at': conn['connected_at']
                }
                for conn in connections
            ]
        }), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
