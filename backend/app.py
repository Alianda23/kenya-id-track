from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # Your MySQL username
    'password': '',  # Your MySQL password
    'database': 'digital_id_system'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Officer Authentication Routes
@app.route('/api/officer/signup', methods=['POST'])
def officer_signup():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['idNumber', 'email', 'phoneNumber', 'fullName', 'station', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if officer already exists
        cursor.execute("SELECT id FROM officers WHERE id_number = %s OR email = %s", 
                      (data['idNumber'], data['email']))
        if cursor.fetchone():
            return jsonify({'error': 'Officer with this ID number or email already exists'}), 400
        
        # Hash password
        hashed_password = generate_password_hash(data['password'])
        
        # Insert new officer (pending approval)
        cursor.execute("""
            INSERT INTO officers (id_number, email, phone_number, full_name, station, password_hash, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, 'pending', %s)
        """, (data['idNumber'], data['email'], data['phoneNumber'], 
              data['fullName'], data['station'], hashed_password, datetime.now()))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Application submitted successfully. Awaiting admin approval.'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/officer/login', methods=['POST'])
def officer_login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get officer details
        cursor.execute("""
            SELECT id, email, full_name, station, password_hash, status 
            FROM officers WHERE email = %s
        """, (email,))
        officer = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not officer:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if officer['status'] != 'approved':
            return jsonify({'error': 'Account not approved by admin'}), 403
        
        if not check_password_hash(officer['password_hash'], password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate JWT token
        token = jwt.encode({
            'officer_id': officer['id'],
            'email': officer['email'],
            'role': 'officer',
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'token': token,
            'officer': {
                'id': officer['id'],
                'email': officer['email'],
                'fullName': officer['full_name'],
                'station': officer['station']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin Routes
@app.route('/api/admin/officers/pending', methods=['GET'])
def get_pending_officers():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, id_number, email, phone_number, full_name, station, created_at
            FROM officers WHERE status = 'pending'
            ORDER BY created_at DESC
        """)
        officers = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'officers': officers}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/officers/<int:officer_id>/approve', methods=['PUT'])
def approve_officer(officer_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE officers SET status = 'approved' WHERE id = %s", (officer_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Officer approved successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/officers/<int:officer_id>/reject', methods=['PUT'])
def reject_officer(officer_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE officers SET status = 'rejected' WHERE id = %s", (officer_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Officer rejected'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)