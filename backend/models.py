from sqlalchemy import Column, Integer, Float
from .db import Base


class Forage(Base):
    __tablename__ = "forages"

    id = Column(Integer, primary_key=True, index=True)
    x_coord = Column(Float, nullable=False)
    y_coord = Column(Float, nullable=False)
    z_coord = Column(Float, nullable=False)
    teneur = Column(Float, nullable=False)
