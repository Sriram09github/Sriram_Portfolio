from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Ensure instance folder exists
try:
    os.makedirs('instance')
except OSError:
    pass

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///portfolio.db')
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Contact model
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'mobile': self.mobile,
            'message': self.message,
            'created_at': self.created_at.isoformat()
        }

# Create database tables
def init_db():
    with app.app_context():
        try:
            db.create_all()
            print("Database initialized successfully!")
        except Exception as e:
            print(f"Error initializing database: {e}")
            # If there's an error, try to recreate the database
            if os.path.exists('instance/portfolio.db'):
                os.remove('instance/portfolio.db')
            db.create_all()
            print("Database recreated successfully!")

# Initialize database
init_db()

# Serve static files
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

# API endpoint for contact form
@app.route('/api/contact', methods=['POST'])
def submit_contact():
    try:
        data = request.json
        new_contact = Contact(
            name=data['name'],
            email=data['email'],
            mobile=data['mobile'],
            message=data['message']
        )
        db.session.add(new_contact)
        db.session.commit()
        return jsonify({'message': 'Message sent successfully!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# API endpoint to retrieve all messages
@app.route('/api/messages', methods=['GET'])
def get_messages():
    try:
        messages = Contact.query.order_by(Contact.created_at.desc()).all()
        return jsonify([message.to_dict() for message in messages]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# API endpoint to retrieve a specific message
@app.route('/api/messages/<int:message_id>', methods=['GET'])
def get_message(message_id):
    try:
        message = Contact.query.get_or_404(message_id)
        return jsonify(message.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 