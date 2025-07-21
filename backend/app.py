from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Dish, MealLog
from passlib.hash import bcrypt
import os
from db_config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
from datetime import date, datetime

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
    user = User(full_name=full_name, email=email, password_hash=password_hash, monthly_budget=budget, budget=budget)

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
        user.monthly_budget = budget
        user.budget = budget
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

@app.route('/api/meals/today', methods=['GET'])
def get_todays_meals():
    email = request.args.get('email')
    if not email:
        return jsonify({'error': 'Missing email'}), 400
    session = SessionLocal()
    today = date.today()
    meals = session.query(MealLog).filter_by(user_email=email).all()
    result = []
    for m in meals:
        # Only include if meal date matches system date
        meal_date = m.date if isinstance(m.date, date) else datetime.strptime(str(m.date), '%Y-%m-%d').date()
        if meal_date == today:
            dish = session.query(Dish).filter_by(name=m.dish_name).first()
            dish_type = dish.type if dish else ''
            result.append({'dish_name': m.dish_name, 'date': m.date.isoformat(), 'type': dish_type})
    session.close()
    return jsonify(result), 200

@app.route('/api/meals/history', methods=['GET'])
def get_meal_history():
    email = request.args.get('email')
    if not email:
        return jsonify({'error': 'Missing email'}), 400
    session = SessionLocal()
    meals = session.query(MealLog).filter_by(user_email=email).order_by(MealLog.date.desc()).all()
    result = []
    for m in meals:
        dish = session.query(Dish).filter_by(name=m.dish_name).first()
        price = float(dish.price) if dish else 0.0
        dish_type = dish.type if dish else ''
        result.append({'id': m.id, 'dish_name': m.dish_name, 'date': m.date.isoformat(), 'price': price, 'type': dish_type})
    session.close()
    return jsonify(result), 200

@app.route('/api/meals/summary', methods=['GET'])
def get_meal_summary():
    email = request.args.get('email')
    if not email:
        return jsonify({'error': 'Missing email'}), 400
    session = SessionLocal()
    user = session.query(User).filter_by(email=email).first()
    if not user:
        session.close()
        return jsonify({'error': 'User not found'}), 404
    # Calculate total spent
    meals = session.query(MealLog).filter_by(user_email=email).all()
    total_spent = 0.0
    for m in meals:
        dish = session.query(Dish).filter_by(name=m.dish_name).first()
        if dish:
            total_spent += float(dish.price)
    remaining_balance = float(user.budget)
    monthly_budget = float(user.monthly_budget)
    session.close()
    return jsonify({
        'monthly_budget': monthly_budget,
        'total_spent': total_spent,
        'remaining_balance': remaining_balance
    }), 200

@app.route('/api/meals/<int:meal_id>', methods=['DELETE'])
def delete_meal(meal_id):
    session = SessionLocal()
    meal = session.query(MealLog).filter_by(id=meal_id).first()
    if not meal:
        session.close()
        return jsonify({'error': 'Meal not found'}), 404
    # Refund the price to the user's budget
    dish = session.query(Dish).filter_by(name=meal.dish_name).first()
    user = session.query(User).filter_by(email=meal.user_email).first()
    if dish and user:
        user.budget = float(user.budget) + float(dish.price)
    session.delete(meal)
    session.commit()
    session.close()
    return jsonify({'message': 'Meal deleted successfully'}), 200

@app.route('/api/meals', methods=['POST'])
def log_meal():
    data = request.json
    user_email = data.get('user_email')
    dish_name = data.get('dish_name')
    date_str = data.get('date')
    if not (user_email and dish_name and date_str):
        return jsonify({'error': 'Missing required fields'}), 400
    session = SessionLocal()
    # Get dish price
    dish = session.query(Dish).filter_by(name=dish_name).first()
    if not dish:
        session.close()
        return jsonify({'error': 'Dish not found in menu'}), 404
    price = float(dish.price)
    # Log meal
    meal = MealLog(user_email=user_email, dish_name=dish_name, date=date_str)
    session.add(meal)
    # Deduct price from user's budget
    user = session.query(User).filter_by(email=user_email).first()
    if user:
        user.budget = float(user.budget) - price
    session.commit()
    session.close()
    return jsonify({'message': 'Meal logged successfully', 'deducted': price}), 201

@app.route('/api/change_password', methods=['POST'])
def change_password():
    data = request.json
    email = data.get('email')
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    if not (email and old_password and new_password):
        return jsonify({'error': 'Missing required fields'}), 400
    session = SessionLocal()
    user = session.query(User).filter_by(email=email).first()
    if not user or not bcrypt.verify(old_password, user.password_hash):
        session.close()
        return jsonify({'error': 'Invalid email or old password'}), 401
    user.password_hash = bcrypt.hash(new_password)
    session.commit()
    session.close()
    return jsonify({'message': 'Password changed successfully'}), 200

if __name__ == "__main__":
    app.run(debug=True)
