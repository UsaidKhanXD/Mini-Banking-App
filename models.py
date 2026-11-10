from database import Base
from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    balance = Column(Float, default=0.00)
    withdraw_history = Column(String, default="")
    deposit_history = Column(String, default="")

