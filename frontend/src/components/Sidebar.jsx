import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { MessageSquare, BarChart2, Search, Zap, Clock, ChevronRight, LogOut, X } from 'lucide-react';

const Sidebar = ({ onSelectReport, isOpen, onClose }) => {
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [activeId, setActiveId] = useState(null);

  useEffect(() => {
    fetchHistory();
    const interval = setInterval(fetchHistory, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get('/api/reports?limit=20', {
          headers: { Authorization: `Bearer ${token}` }
      });
      setHistory(res.data);
    } catch (e) {
      console.error("Failed to fetch history", e);
    }
  };

  const handleSelect = (id) => {
    setActiveId(id);
    onSelectReport(id);
    if (onClose) onClose();
  };

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-40 md:hidden backdrop-blur-sm transition-opacity"
          onClick={onClose}
        />
      )}

      <div className={`
        fixed inset-y-0 left-0 w-72 bg-brand-900 border-r border-brand-800 flex flex-col h-full shadow-2xl z-50
        transition-transform duration-300 ease-in-out
        md:relative md:translate-x-0
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        {/* Header */}
        <div className="p-6 border-b border-brand-800 flex items-center justify-between bg-gradient-to-r from-brand-900 to-brand-950">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-accent rounded-lg flex items-center justify-center text-white font-bold shadow-glow">
              <Zap size={20} fill="white" />
            </div>
            <div>
              <h1 className="font-bold text-xl text-white tracking-tight">Centras AI</h1>
              <p className="text-xs text-brand-400 font-mono tracking-wider">STRATEGIC AGENT</p>
            </div>
          </div>
          <button onClick={onClose} className="md:hidden text-brand-400 hover:text-white">
            <X size={24} />
          </button>
        </div>

      {/* Navigation / History */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6 custom-scrollbar">
        <div>
          <h2 className="text-xs uppercase text-brand-500 font-bold tracking-widest mb-3 px-2 flex items-center gap-2">
            <Clock size={12} /> Recent Analysis
          </h2>
          <ul className="space-y-1">
            {history.map((report) => (
              <li
                key={report.id}
                onClick={() => handleSelect(report.id)}
                className={`
                  group flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all duration-200 border border-transparent
                  ${activeId === report.id
                    ? 'bg-brand-800 border-brand-700 shadow-md text-white'
                    : 'text-brand-400 hover:bg-brand-800/50 hover:text-brand-200'}
                `}
              >
                <div className="flex items-center space-x-3 overflow-hidden">
                  {report.status === 'COMPLETED' ? (
                    <BarChart2 size={16} className={activeId === report.id ? 'text-accent' : 'text-brand-600 group-hover:text-accent transition-colors'} />
                  ) : (
                    <div className="relative">
                      <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-accent rounded-full animate-ping"></span>
                      <Search size={16} className="text-brand-500 group-hover:text-brand-300" />
                    </div>
                  )}
                  <span className="truncate text-sm font-medium">{report.query}</span>
                </div>
                {activeId === report.id && <ChevronRight size={14} className="text-accent" />}
              </li>
            ))}
            {history.length === 0 && (
                <li className="p-4 text-center text-brand-600 text-sm italic">
                    No history found. Start a new search.
                </li>
            )}
          </ul>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-brand-800 bg-brand-900 space-y-3">
        <button
          onClick={() => {
              localStorage.removeItem('token');
              navigate('/');
          }}
          className="w-full flex items-center justify-center gap-2 p-2 rounded-lg bg-brand-800/50 hover:bg-red-900/20 text-brand-300 hover:text-red-400 border border-brand-700 hover:border-red-900/50 transition-all text-sm font-medium"
        >
            <LogOut size={16} />
            <span>Выйти</span>
        </button>

        <div className="bg-brand-800/50 rounded-lg p-3 border border-brand-700">
            <div className="flex items-center gap-2 mb-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-xs font-mono text-brand-300">System Online</span>
            </div>
            <p className="text-[10px] text-brand-500">Gemini 2.0 Flash Exp • V1.0.4</p>
        </div>
      </div>
    </div>
    </>
  );
};

export default Sidebar;
