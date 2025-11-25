from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import database
from portfolio import PortfolioManager
import config

app = FastAPI(title="Tiger Trader Dashboard API")

# Ensure DB is initialized on startup
@app.on_event("startup")
def on_startup():
    database.init_db()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize PortfolioManager (Shared instance)
# Note: In a real prod app, we might want to handle singletons or dependency injection better.
portfolio_mgr = PortfolioManager()

@app.get("/")
def read_root():
    return {"status": "running", "service": "Tiger Trader Bot"}

@app.get("/api/positions")
def get_positions():
    """
    Get current live positions from Tiger Broker.
    """
    try:
        positions = portfolio_mgr.get_all_positions()
        return positions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trades")
def get_trades(limit: int = 50, db: Session = Depends(get_db)):
    """
    Get historical trades from local database.
    """
    trades = db.query(database.Trade).order_by(database.Trade.timestamp.desc()).limit(limit).all()
    return trades

@app.get("/api/performance")
def get_performance(limit: int = 100, db: Session = Depends(get_db)):
    """
    Get portfolio performance snapshots (Equity Curve).
    """
    snapshots = db.query(database.PortfolioSnapshot).order_by(database.PortfolioSnapshot.timestamp.asc()).all()
    # If too many, we might want to downsample, but for now just return all or limit
    # Actually, for a chart, we want all points usually, or a date range. 
    # Let's return last 'limit' points for now.
    return snapshots[-limit:]

@app.get("/api/summary")
def get_summary():
    """
    Get current account summary (Net Liquidation, Cash).
    """
    try:
        summary = portfolio_mgr.get_portfolio_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

