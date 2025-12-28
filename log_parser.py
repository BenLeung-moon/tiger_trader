"""
Log Parser Module (日志解析模块)

Parses positions.log to extract historical portfolio data for dashboard.
解析 positions.log 提取历史组合数据用于仪表板显示。
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional


class LogParser:
    """
    Parse positions.log to extract historical portfolio data
    解析 positions.log 提取历史组合数据
    """
    
    def __init__(self, log_file='logs/positions.log'):
        self.log_file = Path(log_file)
    
    def parse_log_line(self, line: str) -> Optional[Dict]:
        """
        Parse single log line to extract timestamp and positions
        解析单行日志提取时间戳和持仓数据
        
        Args:
            line: Log line in format "2025-12-24 03:54:44,584 - Positions: [{...}]"
            
        Returns:
            Dictionary with timestamp and positions, or None if parsing fails
        """
        # Format: "2025-12-24 03:54:44,584 - Positions: [{...}]"
        match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - Positions: (.+)', line)
        if not match:
            return None
        
        timestamp_str, positions_json = match.groups()
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            positions = json.loads(positions_json)
            return {'timestamp': timestamp, 'positions': positions}
        except Exception as e:
            # Silently skip malformed lines
            return None
    
    def get_latest_snapshot(self) -> Optional[Dict]:
        """
        Get the most recent position snapshot from logs
        从日志获取最新的持仓快照
        
        Returns:
            Dictionary with timestamp and positions, or None if not found
        """
        if not self.log_file.exists():
            return None
        
        # Read last 100 lines (more efficient than reading entire file)
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Parse in reverse to get most recent first
            for line in reversed(lines[-100:]):
                snapshot = self.parse_log_line(line)
                if snapshot:
                    return snapshot
        except Exception as e:
            print(f"Error reading log file: {e}")
            
        return None
    
    def get_snapshots_since(self, since: datetime) -> List[Dict]:
        """
        Get all position snapshots since a given timestamp
        获取指定时间之后的所有持仓快照
        
        Args:
            since: Starting timestamp
            
        Returns:
            List of snapshots with timestamp and positions
        """
        if not self.log_file.exists():
            return []
        
        snapshots = []
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    snapshot = self.parse_log_line(line)
                    if snapshot and snapshot['timestamp'] >= since:
                        snapshots.append(snapshot)
        except Exception as e:
            print(f"Error parsing log file: {e}")
        
        return snapshots
    
    def get_performance_data(self, days: int = 30) -> List[Dict]:
        """
        Get equity curve data for charts
        获取资产曲线数据用于图表显示
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of performance data points with timestamp and metrics
        """
        since = datetime.now() - timedelta(days=days)
        snapshots = self.get_snapshots_since(since)
        
        # Calculate total equity for each snapshot
        performance = []
        seen_timestamps = set()  # Deduplicate by timestamp
        
        for snapshot in snapshots:
            # Round to minute to deduplicate
            ts_key = snapshot['timestamp'].replace(second=0, microsecond=0)
            if ts_key in seen_timestamps:
                continue
            seen_timestamps.add(ts_key)
            
            summary = self.calculate_portfolio_summary(snapshot['positions'])
            performance.append({
                'timestamp': snapshot['timestamp'].isoformat(),
                'total_equity': summary['net_liquidation'],
                'cash_balance': summary['cash_balance'],
                'market_value': summary['gross_position_value']
            })
        
        return performance
    
    def calculate_portfolio_summary(self, positions: List[Dict]) -> Dict:
        """
        Calculate net_liquidation, cash, position value from positions
        从持仓数据计算净资产、现金、持仓市值
        
        Args:
            positions: List of position dictionaries
            
        Returns:
            Dictionary with net_liquidation, gross_position_value, cash_balance
        """
        if not positions:
            return {
                'net_liquidation': 0.0,
                'gross_position_value': 0.0,
                'cash_balance': 0.0
            }
        
        # Calculate total market value from all positions
        total_market_value = sum(pos.get('market_value', 0) for pos in positions)
        
        # Note: Cash balance is not directly in positions log
        # We would need to track it separately or estimate
        # For now, set to 0 as positions already include all value
        
        return {
            'net_liquidation': total_market_value,
            'gross_position_value': total_market_value,
            'cash_balance': 0.0  # Would need from account info API
        }
    
    def get_position_history(self, symbol: str, days: int = 30) -> List[Dict]:
        """
        Get historical position data for a specific symbol
        获取特定股票的历史持仓数据
        
        Args:
            symbol: Stock symbol to track
            days: Number of days to look back
            
        Returns:
            List of position snapshots for the symbol
        """
        since = datetime.now() - timedelta(days=days)
        snapshots = self.get_snapshots_since(since)
        
        position_history = []
        for snapshot in snapshots:
            # Find this symbol in positions
            for pos in snapshot['positions']:
                if pos.get('symbol') == symbol:
                    position_history.append({
                        'timestamp': snapshot['timestamp'].isoformat(),
                        **pos
                    })
                    break
        
        return position_history


# CLI for testing
if __name__ == '__main__':
    parser = LogParser()
    
    print("=== Log Parser Test ===\n")
    
    # Test 1: Get latest snapshot
    print("1. Testing get_latest_snapshot()...")
    latest = parser.get_latest_snapshot()
    if latest:
        print(f"   Found snapshot from: {latest['timestamp']}")
        print(f"   Number of positions: {len(latest['positions'])}")
        if latest['positions']:
            print(f"   Sample position: {latest['positions'][0]['symbol']}")
    else:
        print("   No snapshots found")
    
    print()
    
    # Test 2: Get performance data
    print("2. Testing get_performance_data(7 days)...")
    performance = parser.get_performance_data(days=7)
    print(f"   Found {len(performance)} data points")
    if performance:
        print(f"   Latest equity: ${performance[-1]['total_equity']:,.2f}")
    
    print()
    
    # Test 3: Calculate summary
    if latest:
        print("3. Testing calculate_portfolio_summary()...")
        summary = parser.calculate_portfolio_summary(latest['positions'])
        print(f"   Net Liquidation: ${summary['net_liquidation']:,.2f}")
        print(f"   Position Value: ${summary['gross_position_value']:,.2f}")
    
    print("\n✓ Log Parser Test Complete")

