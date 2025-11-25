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

const Dashboard = () => {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchSummary = async () => {
    try {
      const res = await axios.get('/api/summary');
      setSummary(res.data);
    } catch (error) {
      console.error("Error fetching summary", error);
    }
  };

  useEffect(() => {
    fetchSummary();
    const interval = setInterval(fetchSummary, 60000); // Update every min (每分钟更新)
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Cards - 关键指标卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Net Liquidation Card */}
        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Net Liquidation (净资产)</p>
              <p className="text-2xl font-bold text-blue-600">
                ${summary?.net_liquidation?.toLocaleString() || '0.00'}
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
                 ${summary?.gross_position_value?.toLocaleString() || '0.00'}
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
                 ${summary?.cash_balance?.toLocaleString() || '0.00'}
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

