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
        print("Received request:", request.method, request.content_type)
        
        # Check content type
        if request.content_type and 'application/json' in request.content_type:
            # Handle JSON data
            data = request.get_json()
            files = {}
            print("Processing JSON data:", list(data.keys()) if data else "No data")
        else:
            # Handle form data with files
            data = request.form.to_dict()
            files = request.files
            print("Processing form data:", list(data.keys()) if data else "No data")
        
        # Validate required fields
        required_fields = ['fullNames', 'dateOfBirth', 'gender', 'fatherName', 'motherName', 
                          'districtOfBirth', 'tribe', 'homeDistrict', 'division', 
                          'constituency', 'location', 'subLocation', 'villageEstate', 'occupation']
        
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            print("Missing required fields:", missing_fields)
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        # Get officer ID from token (you'd normally verify JWT here)
        officer_id = 1  # Temporary - should get from JWT token
        
        # Generate application number
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current count for application number
        cursor.execute("SELECT COUNT(*) FROM applications")
        count = cursor.fetchone()[0]
        application_number = f"APP{datetime.now().year}{count + 1:06d}"
        
        print(f"Generated application number: {application_number}")
        
        # Insert application
        cursor.execute("""
            INSERT INTO applications (
                application_number, officer_id, application_type,
                full_names, date_of_birth, gender, father_name, mother_name,
                marital_status, husband_name, husband_id_no,
                district_of_birth, tribe, clan, family, home_district,
                division, constituency, location, sub_location, village_estate,
                home_address, occupation, supporting_documents, status, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
            json.dumps(data.get('supportingDocuments', {})), 'submitted', datetime.now()
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

@app.route('/api/admin/applications', methods=['GET'])
def get_all_applications():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT a.id, a.application_number, a.full_names, a.status, 
                   a.application_type, a.created_at, a.updated_at,
                   o.full_name as officer_name
            FROM applications a 
            LEFT JOIN officers o ON a.officer_id = o.id
            WHERE a.application_type != 'renewal'
            ORDER BY a.created_at DESC
        """)
        
        applications = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({'applications': applications}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/applications/<int:application_id>', methods=['GET'])
def get_application_details(application_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get application details
        cursor.execute("""
            SELECT a.*, o.full_name as officer_name
            FROM applications a 
            LEFT JOIN officers o ON a.officer_id = o.id
            WHERE a.id = %s
        """, (application_id,))
        
        application = cursor.fetchone()
        
        if not application:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Application not found'}), 404
        
        # Get supporting documents
        cursor.execute("""
            SELECT document_type, file_path
            FROM documents WHERE application_id = %s
        """, (application_id,))
        
        documents = cursor.fetchall()
        application['documents'] = documents
        
        cursor.close()
        conn.close()
        
        return jsonify({'application': application}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/applications/<int:application_id>/approve', methods=['PUT'])
def approve_application(application_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Generate ID number
        cursor.execute("SELECT COUNT(*) as count FROM applications WHERE status = 'approved'")
        count = cursor.fetchone()['count']
        id_number = f"ID{datetime.now().year}{count + 1:08d}"
        
        # Update application status and assign ID number
        cursor.execute("""
            UPDATE applications 
            SET status = 'approved', generated_id_number = %s, updated_at = %s
            WHERE id = %s
        """, (id_number, datetime.now(), application_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Application not found'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'message': 'Application approved successfully',
            'id_number': id_number
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/applications/<int:application_id>/reject', methods=['PUT'])
def reject_application(application_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Update application status
        cursor.execute("""
            UPDATE applications 
            SET status = 'rejected', updated_at = %s
            WHERE id = %s
        """, (datetime.now(), application_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Application not found'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Application rejected successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/applications/approved', methods=['GET'])
def get_approved_applications():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT a.id, a.application_number, a.full_names, a.application_type, 
                   a.generated_id_number, a.created_at, a.updated_at, o.full_name as officer_name
            FROM applications a
            LEFT JOIN officers o ON a.officer_id = o.id
            WHERE a.status = 'approved'
            ORDER BY a.updated_at DESC
        """
        
        cursor.execute(query)
        applications = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'applications': applications}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/applications/<int:application_id>/dispatch', methods=['PUT'])
def dispatch_application(application_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Update application status to dispatched
        cursor.execute("""
            UPDATE applications 
            SET status = 'dispatched', updated_at = %s
            WHERE id = %s AND status = 'approved'
        """, (datetime.now(), application_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Application not found or not approved'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Application dispatched successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Officer application routes
@app.route('/api/officer/applications', methods=['GET'])
def get_officer_applications():
    try:
        officer_id = request.args.get('officer_id')
        if not officer_id:
            return jsonify({'error': 'Officer ID is required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, application_number, full_names as fullName, date_of_birth as dateOfBirth,
                   status, created_at as applicationDate, generated_id_number as idNumber,
                   card_arrived, collected, father_name as phoneNumber, application_type
            FROM applications 
            WHERE officer_id = %s
            ORDER BY created_at DESC
        """, (officer_id,))
        
        applications = cursor.fetchall()
        
        # Convert boolean values and format dates
        for app in applications:
            app['cardArrived'] = bool(app.get('card_arrived', 0))
            app['collected'] = bool(app.get('collected', 0))
            if app['applicationDate']:
                app['applicationDate'] = app['applicationDate'].isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify(applications), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/applications/<int:application_id>/card-arrived', methods=['PUT'])
def update_card_arrived(application_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE applications 
            SET card_arrived = 1, updated_at = %s
            WHERE id = %s AND status = 'approved'
        """, (datetime.now(), application_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Application not found or not approved'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Card arrival updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/applications/<int:application_id>/collected', methods=['PUT'])
def update_collected(application_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE applications 
            SET collected = 1, updated_at = %s
            WHERE id = %s AND status = 'approved' AND card_arrived = 1
        """, (datetime.now(), application_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Application not found, not approved, or card not arrived'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Collection status updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin renewal applications route
@app.route('/api/admin/applications/renewals', methods=['GET'])
def get_renewal_applications():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT a.id, a.application_number, a.full_names, a.status, a.application_type,
                   a.created_at, a.updated_at, a.generated_id_number,
                   o.full_name as officer_name
            FROM applications a
            LEFT JOIN officers o ON a.officer_id = o.id
            WHERE a.application_type = 'renewal'
            ORDER BY a.created_at DESC
        """)
        
        applications = cursor.fetchall()
        
        # Convert datetime objects to strings
        for app in applications:
            if app['created_at']:
                app['created_at'] = app['created_at'].isoformat()
            if app['updated_at']:
                app['updated_at'] = app['updated_at'].isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({'applications': applications}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)