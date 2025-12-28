/**
 * Positions Table Component (持仓表格组件)
 * 
 * Displays current stock holdings, including quantity and P/L.
 * Auto-refreshes every 30 seconds.
 */
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { formatCurrency, formatLargeNumber } from '../utils/formatters';

const PositionsTable = () => {
  const [positions, setPositions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchPositions = async () => {
    try {
      setError(null);
      const res = await axios.get('/api/positions');
      setPositions(res.data);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to load positions');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPositions();
    const interval = setInterval(fetchPositions, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-white p-6 rounded-lg shadow-md h-full">
      <h2 className="text-lg font-semibold mb-4">Current Holdings (当前持仓)</h2>
      
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
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Symbol</th>
                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Qty</th>
                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Avg Cost</th>
                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Price</th>
                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">P/L</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {positions.length === 0 ? (
                 <tr><td colSpan="5" className="p-4 text-center text-gray-500 text-sm">No active positions</td></tr>
              ) : (
                positions.map((pos, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-900">{pos.symbol}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-700 text-right">{pos.quantity}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-700 text-right">
                      ${pos.average_cost != null ? formatCurrency(pos.average_cost) : '0.00'}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-700 text-right">
                      ${pos.market_price != null ? formatCurrency(pos.market_price) : '0.00'}
                    </td>
                    <td className={`px-3 py-2 whitespace-nowrap text-sm text-right font-bold ${pos.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {pos.unrealized_pnl >= 0 ? '+' : ''}${pos.unrealized_pnl != null ? formatCurrency(pos.unrealized_pnl) : '0.00'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default PositionsTable;

