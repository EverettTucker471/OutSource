from sqlalchemy import Column, Integer, String, JSON
from .base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    preferences = Column(JSON, default=list)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', name='{self.name}')>"
