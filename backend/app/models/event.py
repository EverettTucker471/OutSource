from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from .base import Base
import enum


class EventState(str, enum.Enum):
    UPCOMING = "upcoming"
    PASSED = "passed"


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    start_at = Column(DateTime, nullable=False)
    end_at = Column(DateTime, nullable=False)
    state = Column(SQLEnum(EventState), nullable=False, default=EventState.UPCOMING)

    def __repr__(self):
        return f"<Event(id={self.id}, name='{self.name}', state='{self.state}')>"
