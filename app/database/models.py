from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from app.database.custom_types import Cube
 
Base = declarative_base()
class Face(Base):
    __tablename__ = 'faces'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)
    gender = Column(String(1))
    embedding = Column(Cube)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    __table_args__ = (
        UniqueConstraint('name'),
        )

    def __repr__(self):
        return "<Face(name='%s', age='%d', gender='%s')>" % (
            self.name, self.age, self.gender)