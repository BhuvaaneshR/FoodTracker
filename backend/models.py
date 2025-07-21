from sqlalchemy import Column, Integer, String, DateTime, Numeric, Date
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    monthly_budget = Column(Numeric(10, 2), default=0)  # Original monthly budget
    budget = Column(Numeric(10, 2), default=0)  # Remaining balance
    created_at = Column(DateTime, default=datetime.utcnow)

class Dish(Base):
    __tablename__ = 'dishes'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

class MealLog(Base):
    __tablename__ = 'meal_logs'
    id = Column(Integer, primary_key=True)
    user_email = Column(String(255), nullable=False)
    dish_name = Column(String(255), nullable=False)
    date = Column(Date, nullable=False) 