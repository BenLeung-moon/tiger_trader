/**
 * Dashboard Component (仪表盘组件)
 * 
 * Main dashboard view acting as the container for all widgets.
 * Displays high-level metrics (Net Liquidation, Market Value, Cash)
 * and arranges charts and tables.
 */
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import EquityChart from './EquityChart';
import PositionsTable from './PositionsTable';
import TradeHistory from './TradeHistory';
import { Activity, TrendingUp, DollarSign } from 'lucide-react';
import { formatLargeNumber } from '../utils/formatters';

const Dashboard = () => {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSummary = async () => {
    try {
      setError(null);
      const res = await axios.get('/api/summary');
      setSummary(res.data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching summary", error);
      setError(error.message || 'Failed to load portfolio data');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
    const interval = setInterval(fetchSummary, 60000); // Update every min (每分钟更新)
    return () => clearInterval(interval);
  }, []);

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 text-lg">Loading portfolio data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded-md">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Top Cards - 关键指标卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Net Liquidation Card */}
        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Net Liquidation (净资产)</p>
              <p className="text-2xl font-bold text-blue-600">
                ${summary?.net_liquidation != null ? formatLargeNumber(summary.net_liquidation) : '0.00'}
              </p>
            </div>
            <Activity className="text-blue-500" size={24} />
          </div>
        </div>
        
        {/* Market Value Card */}
        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-100">
           <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Market Value (持仓市值)</p>
              <p className="text-2xl font-bold text-green-600">
                 ${summary?.gross_position_value != null ? formatLargeNumber(summary.gross_position_value) : '0.00'}
              </p>
            </div>
            <TrendingUp className="text-green-500" size={24} />
          </div>
        </div>

        {/* Cash Balance Card */}
        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-100">
           <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Cash Balance (现金余额)</p>
              <p className="text-2xl font-bold text-purple-600">
                 ${summary?.cash_balance != null ? formatLargeNumber(summary.cash_balance) : '0.00'}
              </p>
            </div>
            <DollarSign className="text-purple-500" size={24} />
          </div>
        </div>
      </div>

      {/* Charts & Tables - 图表与表格 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
           <EquityChart />
           <TradeHistory />
        </div>
        <div>
           <PositionsTable />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

