from sqlalchemy import Column, Integer, String, DateTime,func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__= "users"

    id = Column(Integer, primary_key=True, index=True)
    userName = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    firstName = Column(String, nullable=False)
    lastName = Column(String, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
