from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

# Base class for all models 
Base = declarative_base()

class User(Base):
    """User model for testing"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    position = Column(String(100), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), nullable=True)
    username = Column(String(100), unique=True, nullable=False) # for what?
    product_interest_1 = Column(String(100), nullable=True) #sera une liste de produits, à voir comment faire
    product_interest_2 = Column(String(100), nullable=True)
    product_interest_3 = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"