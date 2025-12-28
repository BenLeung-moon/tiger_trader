/**
 * Equity Chart Component (资产曲线图组件)
 * 
 * Visualizes the portfolio's performance over time using Recharts.
 * Displays Total Equity (Net Liquidation).
 */
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { formatLargeNumber } from '../utils/formatters';

const EquityChart = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setError(null);
        const res = await axios.get('/api/performance');
        // Format date
        const formatted = res.data.map(item => ({
          ...item,
          time: new Date(item.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
          date: new Date(item.timestamp).toLocaleDateString()
        }));
        setData(formatted);
        setLoading(false);
      } catch (err) {
        console.error(err);
        setError(err.message || 'Failed to load performance data');
        setLoading(false);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, []);

  // Custom tooltip formatter
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
          <p className="text-sm text-gray-600">{payload[0].payload.date}</p>
          <p className="text-sm text-gray-600">{payload[0].payload.time}</p>
          <p className="text-sm font-bold text-blue-600">
            ${formatLargeNumber(payload[0].value)}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-lg font-semibold mb-4">Performance (Total Equity) - 资产走势</h2>
      
      {loading && (
        <div className="h-64 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-500 text-sm">Loading chart...</p>
          </div>
        </div>
      )}

      {error && !loading && (
        <div className="h-64 flex items-center justify-center">
          <p className="text-red-500 text-sm">{error}</p>
        </div>
      )}

      {!loading && !error && data.length === 0 && (
        <div className="h-64 flex items-center justify-center">
          <p className="text-gray-500 text-sm">No performance data available yet</p>
        </div>
      )}

      {!loading && !error && data.length > 0 && (
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis domain={['auto', 'auto']} />
              <Tooltip content={<CustomTooltip />} />
              <Line type="monotone" dataKey="total_equity" stroke="#2563eb" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

export default EquityChart;

