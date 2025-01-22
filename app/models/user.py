from sqlalchemy import Column, Integer, String, Date, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.db.db import Base

__all__ = [
    "User",
    "DailyData"
]


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    weight = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    age = Column(Integer, nullable=False)
    city = Column(String, nullable=False)
    water_level = Column(Float, nullable=False)
    calorie_level = Column(Float, nullable=False)

    daily_data = relationship(
        "DailyData",
        back_populates="user"
    )


class DailyData(Base):
    __tablename__ = "daily_data"

    daily_data_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    date = Column(Date, nullable=False)
    logged_water = Column(Float, nullable=True)
    logged_calories = Column(Float, nullable=True)
    burned_calories = Column(Float, nullable=True)

    user = relationship(
        "User",
        back_populates="daily_data"
    )
