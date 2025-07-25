from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
import os
import json

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

# Admin Authentication
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get admin details
        cursor.execute("""
            SELECT id, username, full_name, password_hash 
            FROM admins WHERE username = %s
        """, (username,))
        admin = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not admin:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not check_password_hash(admin['password_hash'], password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate JWT token
        token = jwt.encode({
            'admin_id': admin['id'],
            'username': admin['username'],
            'role': 'admin',
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'token': token,
            'admin': {
                'id': admin['id'],
                'username': admin['username'],
                'fullName': admin['full_name']
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

# Application Routes
@app.route('/api/applications', methods=['POST'])
def submit_application():
    try:
        # Check content type
        if request.content_type and 'application/json' in request.content_type:
            # Handle JSON data
            data = request.get_json()
            files = {}
        else:
            # Handle form data with files
            data = request.form.to_dict()
            files = request.files
        
        # Get officer ID from token (you'd normally verify JWT here)
        officer_id = 1  # Temporary - should get from JWT token
        
        # Generate application number
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current count for application number
        cursor.execute("SELECT COUNT(*) FROM applications")
        count = cursor.fetchone()[0]
        application_number = f"APP{datetime.now().year}{count + 1:06d}"
        
        # Insert application
        cursor.execute("""
            INSERT INTO applications (
                application_number, officer_id, application_type,
                full_names, date_of_birth, gender, father_name, mother_name,
                marital_status, husband_name, husband_id_no,
                district_of_birth, tribe, clan, family, home_district,
                division, constituency, location, sub_location, village_estate,
                home_address, occupation, supporting_documents, status
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            application_number, officer_id, 'new',
            data['fullNames'], data['dateOfBirth'], data['gender'],
            data['fatherName'], data['motherName'], data.get('maritalStatus'),
            data.get('husbandName'), data.get('husbandIdNo'),
            data['districtOfBirth'], data['tribe'], data.get('clan'),
            data.get('family'), data['homeDistrict'], data['division'],
            data['constituency'], data['location'], data['subLocation'],
            data['villageEstate'], data.get('homeAddress'), data['occupation'],
            json.dumps(data.get('supportingDocuments', {})), 'submitted'
        ))
        
        application_id = cursor.lastrowid
        
        # Handle file uploads (only if files were sent)
        upload_dir = 'uploads'
        os.makedirs(upload_dir, exist_ok=True)
        
        for file_key, file in files.items():
            if file and file.filename:
                # Create safe filename
                filename = f"{application_number}_{file_key}_{file.filename}"
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                
                # Map file types
                doc_type_mapping = {
                    'passportPhoto': 'passport_photo',
                    'birthCertificate': 'birth_certificate', 
                    'parentsId': 'parent_id_front'
                }
                
                doc_type = doc_type_mapping.get(file_key, file_key)
                
                # Insert document record
                cursor.execute("""
                    INSERT INTO documents (application_id, document_type, file_path)
                    VALUES (%s, %s, %s)
                """, (application_id, doc_type, file_path))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'message': 'Application submitted successfully',
            'applicationNumber': application_number
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/applications/track/<application_number>', methods=['GET'])
def track_application(application_number):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT application_number, full_names, status, created_at, updated_at
            FROM applications WHERE application_number = %s
        """, (application_number,))
        
        application = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not application:
            return jsonify({'error': 'Application not found'}), 404
            
        return jsonify({'application': application}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)