from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

    wishlist = relationship('WishlistItem', back_populates='user', cascade='all, delete-orphan')


class WishlistItem(Base):
    __tablename__ = 'wishlist'

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, nullable=False)  # This is the external game ID (e.g. from IGDB)
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship('User', back_populates='wishlist')


# Create DB engine and tables
engine = create_engine('sqlite:///user_info.db')
Base.metadata.create_all(engine)
