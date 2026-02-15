from sqlalchemy import Column, Integer, Boolean, ForeignKey, String
from .base import Base


class Circle(Base):
    __tablename__ = "circles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    public = Column(Boolean, nullable=False, default=False)
    owner = Column(Integer, ForeignKey("users.id"), nullable=False)

    def __repr__(self):
        return f"<Circle(id={self.id}, name='{self.name}', public={self.public}, owner={self.owner})>"
