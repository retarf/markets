from sqlalchemy import Column, String, DateTime, Float
from .database import Base

class Trend(Base):
    __tablename__ = 'markets.dev.mart_trend_data'

    trading_date = Column(DateTime, primary_key=True)
    ticker = Column(String, primary_key=True)
    close = Column(Float)
    trend_sma_5 = Column(String)
    trend_sma_10 = Column(String)
    trend_sma_20 = Column(String)
    trend = Column(String)
    signal_sma_5 = Column(Float)
    signal_sma_10 = Column(Float)
    signal_sma_20 = Column(Float)
    trend = Column(String)
