from sqlalchemy import Column, BigInteger, String, JSON
from .base import BaseModel

class User(BaseModel):
    __tablename__ = 'users'

    user_id = Column(BigInteger, primary_key=True)
    telegram_id = Column(BigInteger, unique=True)
    username = Column(String(255))
    preferences = Column(JSON)

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username={self.username})>" 