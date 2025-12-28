/**
 * Trade History Component (交易历史组件)
 * 
 * Displays a list of recent trades executed by the bot.
 * Fetches data from the local database via API.
 */
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { formatCurrency, formatRelativeTime } from '../utils/formatters';

const TradeHistory = () => {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchTrades = async () => {
    try {
      setError(null);
      const res = await axios.get('/api/trades?limit=20');
      setTrades(res.data);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to load trade history');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrades();
    const interval = setInterval(fetchTrades, 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Recent Trades (近期交易)</h2>
        {!loading && trades.length > 0 && (
          <span className="text-sm text-gray-500">{trades.length} trade{trades.length !== 1 ? 's' : ''}</span>
        )}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )}

      {error && !loading && (
        <div className="p-4 text-center">
          <p className="text-red-500 text-sm">{error}</p>
        </div>
      )}

      {!loading && !error && (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Symbol</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Price</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Qty</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
               {trades.length === 0 ? (
                 <tr><td colSpan="6" className="p-4 text-center text-gray-500 text-sm">No trades recorded yet</td></tr>
              ) : (
                trades.map((trade) => {
                  const tradeTime = new Date(trade.timestamp);
                  const isRecent = (new Date() - tradeTime) < 3600000; // Less than 1 hour
                  
                  return (
                    <tr key={trade.id} className={`hover:bg-gray-50 ${isRecent ? 'bg-blue-50' : ''}`}>
                      <td className="px-4 py-2 whitespace-nowrap text-xs text-gray-500">
                        <div>{tradeTime.toLocaleDateString()}</div>
                        <div className="text-gray-400">{tradeTime.toLocaleTimeString()}</div>
                        <div className="text-gray-400 italic">{formatRelativeTime(tradeTime)}</div>
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm font-bold text-gray-900">{trade.symbol}</td>
                      <td className={`px-4 py-2 whitespace-nowrap text-sm font-bold ${trade.action === 'BUY' ? 'text-blue-600' : 'text-orange-600'}`}>
                        {trade.action}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-right text-gray-700">
                        ${trade.price != null ? formatCurrency(trade.price) : '0.00'}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-right text-gray-700">{trade.quantity}</td>
                      <td className="px-4 py-2 whitespace-nowrap text-xs">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${trade.status === 'FILLED' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                          {trade.status}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default TradeHistory;

