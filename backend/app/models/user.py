from sqlalchemy import Column, BigInteger, String, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    preferences = Column(JSON, default=list)
    friends = Column(JSON, default=list)
    groups = Column(JSON, default=list)
    inc_requests = Column(JSON, default=list)
    out_requests = Column(JSON, default=list)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', name='{self.name}')>"
