from sqlalchemy import Column, Integer, Float
from .db import Base


class Sample(Base):
    __tablename__ = "samples"

    id = Column(Integer, primary_key=True, index=True)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    z = Column(Float, nullable=False)
    grade_percent = Column(Float, nullable=False)
