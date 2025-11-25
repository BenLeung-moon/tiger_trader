from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, func
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

# Define the database URL (SQLite for local storage)
DATABASE_URL = "sqlite:///./data/trade.db"

# Create the engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class
Base = declarative_base()

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    action = Column(String)  # BUY, SELL
    quantity = Column(Integer)
    price = Column(Float)
    strategy = Column(String, nullable=True)
    reason = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    order_id = Column(String, nullable=True)
    status = Column(String, default="FILLED")

class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    total_equity = Column(Float)
    cash_balance = Column(Float)
    market_value = Column(Float)
    pnl_daily = Column(Float, nullable=True)

def init_db():
    import os
    if not os.path.exists("./data"):
        os.makedirs("./data")
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

