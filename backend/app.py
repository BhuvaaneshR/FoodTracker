from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Dish
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
    budget = data.get('budget', 0)

    if not (full_name and email and password):
        return jsonify({'error': 'Missing required fields'}), 400

    session = SessionLocal()
    if session.query(User).filter_by(email=email).first():
        session.close()
        return jsonify({'error': 'Email already registered'}), 409

    password_hash = bcrypt.hash(password)
    user = User(full_name=full_name, email=email, password_hash=password_hash, budget=budget)

    session.add(user)
    session.commit()
    session.close()

    return jsonify({'message': 'User registered successfully'}), 201

# ✅ Login route
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

# ✅ Get budget
@app.route('/api/budget', methods=['GET'])
def get_budget():
    email = request.args.get('email')
    if not email:
        return jsonify({'error': 'Missing email'}), 400
    session = SessionLocal()
    user = session.query(User).filter_by(email=email).first()
    if user:
        budget = float(user.budget) if user.budget is not None else 0.0
        session.close()
        return jsonify({'budget': budget}), 200
    session.close()
    return jsonify({'error': 'User not found'}), 404

# ✅ Set budget
@app.route('/api/budget', methods=['POST'])
def set_budget():
    data = request.json
    email = data.get('email')
    budget = data.get('budget')
    if not (email and budget is not None):
        return jsonify({'error': 'Missing email or budget'}), 400
    session = SessionLocal()
    user = session.query(User).filter_by(email=email).first()
    if user:
        user.budget = float(budget)
        session.commit()
        session.close()
        return jsonify({'message': 'Budget updated successfully'}), 200
    session.close()
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/dishes', methods=['GET'])
def get_dishes():
    session = SessionLocal()
    dishes = session.query(Dish).all()
    session.close()
    return jsonify([
        {'id': d.id, 'name': d.name, 'type': d.type, 'price': float(d.price)} for d in dishes
    ])

@app.route('/api/dishes', methods=['POST'])
def add_dish():
    data = request.json
    name = data.get('name')
    type_ = data.get('type')
    price = data.get('price')
    if not (name and type_ and price is not None):
        return jsonify({'error': 'Missing required fields'}), 400
    session = SessionLocal()
    dish = Dish(name=name, type=type_, price=price)
    session.add(dish)
    session.commit()
    session.close()
    return jsonify({'message': 'Dish added successfully'}), 201

@app.route('/api/dishes/<int:dish_id>', methods=['DELETE'])
def delete_dish(dish_id):
    session = SessionLocal()
    dish = session.query(Dish).filter_by(id=dish_id).first()
    if not dish:
        session.close()
        return jsonify({'error': 'Dish not found'}), 404
    session.delete(dish)
    session.commit()
    session.close()
    return jsonify({'message': 'Dish deleted successfully'}), 200

@app.route('/api/dishes/<int:dish_id>', methods=['PUT'])
def edit_dish(dish_id):
    data = request.json
    session = SessionLocal()
    dish = session.query(Dish).filter_by(id=dish_id).first()
    if not dish:
        session.close()
        return jsonify({'error': 'Dish not found'}), 404
    name = data.get('name')
    type_ = data.get('type')
    price = data.get('price')
    if name:
        dish.name = name
    if type_:
        dish.type = type_
    if price is not None:
        dish.price = price
    session.commit()
    session.close()
    return jsonify({'message': 'Dish updated successfully'}), 200

if __name__ == "__main__":
    app.run(debug=True)
