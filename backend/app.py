from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User
from passlib.hash import bcrypt
import os
from db_config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

app = Flask(__name__)
CORS(app)

# Database connection
DATABASE_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

# ✅ Test route
@app.route('/')
def index():
    return "Flask backend is running"

# ✅ Signup route
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    full_name = data.get('full_name')
    email = data.get('email')
    password = data.get('password')

    if not (full_name and email and password):
        return jsonify({'error': 'Missing required fields'}), 400

    session = SessionLocal()
    if session.query(User).filter_by(email=email).first():
        session.close()
        return jsonify({'error': 'Email already registered'}), 409

    password_hash = bcrypt.hash(password)
    user = User(full_name=full_name, email=email, password_hash=password_hash)

    session.add(user)
    session.commit()
    session.close()

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    if not (email and password):
        return jsonify({'error': 'Missing email or password'}), 400
    session = SessionLocal()
    user = session.query(User).filter_by(email=email).first()
    if user and bcrypt.verify(password, user.password_hash):
        full_name = user.full_name
        session.close()
        return jsonify({'message': 'Login successful', 'full_name': full_name}), 200
    session.close()
    return jsonify({'error': 'Invalid email or password'}), 401

if __name__ == "__main__":
    app.run(debug=True)
