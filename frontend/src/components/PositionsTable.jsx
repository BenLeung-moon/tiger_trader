/**
 * Positions Table Component (持仓表格组件)
 * 
 * Displays current stock holdings, including quantity and P/L.
 * Auto-refreshes every 30 seconds.
 */
import React, { useEffect, useState } from 'react';
import axios from 'axios';

const PositionsTable = () => {
  const [positions, setPositions] = useState([]);

  const fetchPositions = async () => {
    try {
      const res = await axios.get('/api/positions');
      setPositions(res.data);
    } catch (err) {
      console.error(err);
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
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Symbol</th>
              <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Qty</th>
              <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">P/L</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {positions.length === 0 ? (
               <tr><td colSpan="3" className="p-4 text-center text-gray-500 text-sm">No active positions</td></tr>
            ) : (
              positions.map((pos, idx) => (
                <tr key={idx}>
                  <td className="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-900">{pos.symbol}</td>
                  <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500 text-right">{pos.quantity}</td>
                  <td className={`px-3 py-2 whitespace-nowrap text-sm text-right font-bold ${pos.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {pos.unrealized_pnl?.toFixed(2)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PositionsTable;

