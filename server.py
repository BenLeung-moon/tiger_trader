from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import database
from portfolio import PortfolioManager
from log_parser import LogParser
import config
from utils import setup_loggers

# Setup logging
trading_logger, error_logger = setup_loggers()

app = FastAPI(title="Tiger Trader Dashboard API")

# Ensure DB is initialized on startup
@app.on_event("startup")
def on_startup():
    try:
        database.init_db()
    except Exception as e:
        print(f"DB init skipped or failed: {e}")

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

# Initialize PortfolioManager and LogParser (Shared instances)
# Note: In a real prod app, we might want to handle singletons or dependency injection better.
portfolio_mgr = PortfolioManager()
log_parser = LogParser()

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
def get_summary(db: Session = Depends(get_db)):
    """
    Get current account summary with fallback logic (三层数据回退策略)
    Tier 1: Live API -> Tier 2: Database cache -> Tier 3: Log parser
    """
    # Tier 1: Try live API first (most accurate)
    try:
        summary = portfolio_mgr.get_portfolio_summary()
        if summary and summary.get('net_liquidation', 0) > 0:
            summary['source'] = 'live_api'
            return summary
    except Exception as e:
        error_logger.error(f"Live API failed: {e}")
    
    # Tier 2: Fallback to latest database snapshot
    try:
        latest = db.query(database.PortfolioSnapshot).order_by(
            database.PortfolioSnapshot.timestamp.desc()
        ).first()
        
        if latest:
            # Check if data is recent (within 10 minutes)
            age = datetime.utcnow() - latest.timestamp
            if age < timedelta(minutes=10):
                return {
                    'net_liquidation': latest.total_equity,
                    'cash_balance': latest.cash_balance,
                    'gross_position_value': latest.market_value,
                    'source': 'database_cache',
                    'age_minutes': age.total_seconds() / 60
                }
    except Exception as e:
        error_logger.error(f"Database fallback failed: {e}")
    
    # Tier 3: Fallback to log parser
    try:
        latest_snapshot = log_parser.get_latest_snapshot()
        if latest_snapshot:
            summary = log_parser.calculate_portfolio_summary(latest_snapshot['positions'])
            summary['source'] = 'log_parser'
            summary['timestamp'] = latest_snapshot['timestamp'].isoformat()
            return summary
    except Exception as e:
        error_logger.error(f"Log parser fallback failed: {e}")
    
    # Ultimate fallback - return zeros with error message
    return {
        'net_liquidation': 0.0,
        'cash_balance': 0.0,
        'gross_position_value': 0.0,
        'source': 'fallback',
        'error': 'All data sources unavailable'
    }

@app.get("/api/performance/from-logs")
def get_performance_from_logs(days: int = 30):
    """
    Get performance data from logs (faster than database for recent data)
    从日志获取性能数据 (比数据库更快，用于最近数据)
    
    Args:
        days: Number of days to look back (default: 30)
    """
    try:
        data = log_parser.get_performance_data(days)
        return data
    except Exception as e:
        error_logger.error(f"Error parsing logs for performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/positions/history")
def get_position_history(symbol: str, days: int = 30):
    """
    Get historical position data for a specific symbol
    获取特定股票的历史持仓数据
    
    Args:
        symbol: Stock symbol
        days: Number of days to look back
    """
    try:
        history = log_parser.get_position_history(symbol, days)
        return history
    except Exception as e:
        error_logger.error(f"Error getting position history for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/log-stats")
def get_log_stats():
    """
    Get log parser statistics
    获取日志解析器统计信息
    """
    try:
        latest = log_parser.get_latest_snapshot()
        performance = log_parser.get_performance_data(days=7)
        
        return {
            'log_file_exists': log_parser.log_file.exists(),
            'log_file_path': str(log_parser.log_file),
            'latest_snapshot_time': latest['timestamp'].isoformat() if latest else None,
            'data_points_last_7_days': len(performance),
            'positions_in_latest': len(latest['positions']) if latest else 0
        }
    except Exception as e:
        return {
            'error': str(e),
            'log_file_exists': log_parser.log_file.exists()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

