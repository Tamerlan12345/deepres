import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { MessageSquare, BarChart2, FileText } from 'lucide-react';

const Sidebar = ({ onSelectReport }) => {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    fetchHistory();
    const interval = setInterval(fetchHistory, 10000); // Poll for updates
    return () => clearInterval(interval);
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await axios.get('/api/reports?limit=20');
      setHistory(res.data);
    } catch (e) {
      console.error("Failed to fetch history", e);
    }
  };

  return (
    <div className="w-64 bg-brand-900 text-white flex flex-col h-full shadow-lg">
      <div className="p-4 border-b border-brand-700 flex items-center space-x-2">
        <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center text-brand-900 font-bold">C</div>
        <h1 className="font-bold text-lg">Centras AI</h1>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        <h2 className="text-xs uppercase text-brand-500 font-semibold mb-2 px-2">History</h2>
        <ul>
          {history.map((report) => (
            <li
              key={report.id}
              onClick={() => onSelectReport(report.id)}
              className="p-2 hover:bg-brand-800 rounded cursor-pointer text-sm truncate flex items-center space-x-2 text-brand-100"
            >
              {report.status === 'COMPLETED' ? <BarChart2 size={14} className="text-green-400" /> : <MessageSquare size={14} className="text-yellow-400" />}
              <span className="truncate">{report.query}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default Sidebar;
