from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

"""
Represents user accounts in the database
allows username and password storage for user
includes password verification functionality

id: key used for user identification
username is a uniqe string that acts as the users account name
password is a hashed string used for authentication
todos: the users created todos
"""

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    # wishlist = relationship('ToDo', back_populates='user')


# class ToDo(Base):
#     __tablename__ = 'todo'
#     id = Column(Integer, primary_key=True)
#     task = Column(String, nullable=False)
#     category = Column(String, nullable=False)
#     completed = Column(Boolean, default=False)
#     due_date = Column(DateTime, nullable=True)
#     user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
#     user = relationship('User', back_populates='todos')

# # Database setup using sqlite, creates database table
# engine = create_engine('sqlite:///userdata.db')
# Base.metadata.create_all(engine)