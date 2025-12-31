import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { Download, Send, RefreshCw, AlertCircle, BrainCircuit, Search, FileText, Database, ArrowRight, Zap, Activity } from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  defaults
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

// Chart.js Global Configuration for Dark Mode
defaults.color = '#94a3b8';
defaults.font.family = 'Inter';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const LOADING_MESSAGES = [
    "Initializing Deep Research Agent...",
    "Understanding context and strategic intent...",
    "Accessing Google Search Tool...",
    "Searching 'kase.kz' for financial reports...",
    "Analyzing competitor quarterly results...",
    "Cross-referencing data from National Bank...",
    "Synthesizing key metrics...",
    "Generating strategic insights...",
    "Finalizing report format..."
];

const Dashboard = ({ currentReportId, onNewReport }) => {
  const [query, setQuery] = useState("");
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [loadingMsgIndex, setLoadingMsgIndex] = useState(0);

  // Poll for report status if it's processing
  useEffect(() => {
    let interval;
    if (currentReportId) {
      setLoading(true);
      fetchReport(currentReportId);
      interval = setInterval(() => {
        fetchReport(currentReportId);
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [currentReportId]);

  // Rotate loading messages
  useEffect(() => {
      let msgInterval;
      if (loading && (!report || report.status !== 'COMPLETED')) {
          msgInterval = setInterval(() => {
              setLoadingMsgIndex((prev) => (prev + 1) % LOADING_MESSAGES.length);
          }, 4000);
      }
      return () => clearInterval(msgInterval);
  }, [loading, report]);

  const fetchReport = async (id) => {
    try {
      const res = await axios.get(`/api/reports/${id}`);
      setReport(res.data);
      if (res.data.status === 'COMPLETED') {
        setLoading(false);
      } else if (res.data.status === 'FAILED') {
        setLoading(false);
        setError("Report generation failed.");
      }
    } catch (e) {
        console.error(e);
        setError("Could not fetch report");
        setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setReport(null);
    setError(null);
    setLoadingMsgIndex(0);
    try {
      const res = await axios.post('/api/reports', { query });
      onNewReport(res.data.id);
      setQuery("");
    } catch (e) {
      setError("Failed to create report");
      setLoading(false);
    }
  };

  const handleScenario = (text) => {
    setQuery(text);
  };

  const renderCharts = (chartsData) => {
      if (!chartsData || chartsData.length === 0) return null;
      return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              {chartsData.map((chart, idx) => {
                  if (chart.type === 'bar') {
                    const data = {
                        labels: chart.labels,
                        datasets: chart.datasets.map(ds => ({
                            label: ds.label,
                            data: ds.data,
                            backgroundColor: 'rgba(59, 130, 246, 0.8)', // Accent Blue
                            borderColor: '#3b82f6',
                            borderWidth: 1,
                            borderRadius: 4,
                        }))
                    };
                    const options = {
                        responsive: true,
                        plugins: {
                            title: { display: true, text: chart.title, color: '#f1f5f9', font: { size: 16, weight: 'bold' } },
                            legend: { labels: { color: '#cbd5e1' } }
                        },
                        scales: {
                            y: { grid: { color: '#334155' }, ticks: { color: '#94a3b8' } },
                            x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
                        }
                    };
                    return (
                        <div key={idx} className="card border-brand-800 bg-brand-900/50">
                            <Bar options={options} data={data} />
                        </div>
                    );
                  }
                  return null;
              })}
          </div>
      );
  };

  return (
    <div className="max-w-6xl mx-auto pb-12 pt-6 px-6">
      {/* Search / Hero Section */}
      <div className="card mb-8 relative overflow-hidden group">
         {/* Background decoration */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-accent/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 group-hover:bg-accent/15 transition-all duration-700"></div>

        <div className="relative z-10">
            <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-brand-800 rounded-lg border border-brand-700">
                    <BrainCircuit className="text-accent" size={28} />
                </div>
                <div>
                    <h2 className="text-2xl font-bold text-white tracking-tight">Research Command Center</h2>
                    <p className="text-brand-400 text-sm">Autonomous Strategic Agent • Deep Research Pro</p>
                </div>
            </div>

            <form onSubmit={handleSubmit} className="relative mb-6">
                <div className="relative group/input">
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Ask a complex strategic question..."
                        className="input-field pl-14 py-5 text-lg shadow-inner bg-brand-950/50 border-brand-800 focus:border-accent transition-all"
                    />
                    <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-brand-500 group-focus-within/input:text-accent transition-colors" size={24} />
                    <button
                        type="submit"
                        disabled={loading || !query.trim()}
                        className="absolute right-3 top-3 bottom-3 btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-accent/20"
                    >
                        {loading ? <RefreshCw className="animate-spin" size={18} /> : <Zap size={18} />}
                        <span>Analyze</span>
                    </button>
                </div>
            </form>

            <div className="flex gap-3 overflow-x-auto pb-2 custom-scrollbar">
                <button onClick={() => handleScenario("Анализ конкурентов (Евразия, Халык, Фридом): Прибыль и GWP за Q3 2024")}
                    className="flex items-center gap-2 px-4 py-2 bg-brand-800/50 text-brand-300 border border-brand-700 rounded-full text-xs font-medium whitespace-nowrap hover:bg-brand-800 hover:text-white hover:border-brand-600 transition-all">
                    🏢 Competitor Deep Dive
                </button>
                <button onClick={() => handleScenario("Мониторинг регуляторных изменений в страховании РК за последние 3 месяца")}
                    className="flex items-center gap-2 px-4 py-2 bg-brand-800/50 text-brand-300 border border-brand-700 rounded-full text-xs font-medium whitespace-nowrap hover:bg-brand-800 hover:text-white hover:border-brand-600 transition-all">
                    ⚖️ Regulatory Check
                </button>
                <button onClick={() => handleScenario("Сравни условия КАСКО (Centras vs Freedom) по данным с сайтов")}
                    className="flex items-center gap-2 px-4 py-2 bg-brand-800/50 text-brand-300 border border-brand-700 rounded-full text-xs font-medium whitespace-nowrap hover:bg-brand-800 hover:text-white hover:border-brand-600 transition-all">
                    🛡️ Product Benchmark
                </button>
            </div>
        </div>
      </div>

      {/* Report View */}
      <div className="space-y-8 animate-fade-in-up">
          {loading && (!report || report.status !== 'COMPLETED' && report.status !== 'FAILED') && (
              <div className="flex flex-col items-center justify-center py-20 card border-dashed border-2 border-brand-800 bg-transparent">
                  <div className="relative mb-8">
                    <div className="absolute inset-0 bg-accent rounded-full animate-ping opacity-20"></div>
                    <div className="relative bg-brand-900 p-6 rounded-full border border-brand-700 shadow-glow">
                        <Activity className="text-accent animate-pulse" size={48} />
                    </div>
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-3">Conducting Deep Research</h3>
                  <p className="text-brand-400 text-center max-w-lg font-mono text-sm h-6">
                      {'>'} {LOADING_MESSAGES[loadingMsgIndex]}<span className="animate-pulse">_</span>
                  </p>
              </div>
          )}

          {error && (
               <div className="p-4 bg-error-bg text-error rounded-lg border border-error/20 flex items-center">
                   <AlertCircle className="mr-3" />
                   <span className="font-medium">{error}</span>
               </div>
          )}

          {report && report.status === 'COMPLETED' && report.result_json && (
              <>
                {/* Summary Card */}
                <div className="card relative overflow-hidden border-l-4 border-l-accent">
                    <div className="absolute top-0 right-0 p-6 opacity-5">
                        <FileText size={120} />
                    </div>
                    <div className="flex items-center gap-3 mb-4 text-accent">
                        <div className="p-1.5 bg-accent/10 rounded">
                            <FileText size={20} />
                        </div>
                        <h3 className="text-sm font-bold uppercase tracking-widest text-brand-300">Executive Summary</h3>
                    </div>
                    <p className="text-brand-100 text-lg leading-relaxed font-light">{report.result_json.summary}</p>
                </div>

                {/* Key Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {report.result_json.key_metrics?.map((metric, i) => (
                        <div key={i} className="card p-5 group hover:border-brand-600 transition-colors">
                            <div className="flex justify-between items-start mb-2">
                                <p className="text-xs text-brand-500 font-bold uppercase tracking-wider">{metric.label}</p>
                                {metric.trend && (
                                     <span className={`text-[10px] px-1.5 py-0.5 rounded border ${
                                         metric.trend === 'Рост' ? 'text-emerald-400 border-emerald-900/50 bg-emerald-900/20' :
                                         metric.trend === 'Падение' ? 'text-red-400 border-red-900/50 bg-red-900/20' :
                                         'text-brand-400 border-brand-700'
                                     }`}>
                                         {metric.trend}
                                     </span>
                                )}
                            </div>
                            <p className="text-3xl font-bold text-white mb-2 tracking-tight group-hover:text-accent transition-colors">{metric.value}</p>
                            {metric.change && (
                                <div className={`text-sm font-medium ${metric.change?.includes('+') ? 'text-emerald-500' : 'text-red-500'}`}>
                                    {metric.change} <span className="text-brand-600 text-xs font-normal">vs prev. period</span>
                                </div>
                            )}
                        </div>
                    ))}
                </div>

                {/* Charts */}
                {renderCharts(report.result_json.charts_data)}

                {/* Detailed Analysis */}
                <div className="card">
                    <div className="flex justify-between items-center mb-6 pb-4 border-b border-brand-800">
                        <h3 className="text-xl font-bold text-white flex items-center gap-3">
                            <BrainCircuit className="text-brand-400" size={24} />
                            Detailed Analysis
                        </h3>
                        <a href={`/api/reports/${report.id}/pdf`} target="_blank" rel="noreferrer" className="btn-secondary flex items-center gap-2 text-sm">
                            <Download size={16} /> Export PDF
                        </a>
                    </div>
                    <div className="prose prose-invert prose-brand max-w-none text-brand-300 prose-headings:text-white prose-a:text-accent prose-strong:text-brand-100">
                        <ReactMarkdown>{report.result_json.detailed_analysis}</ReactMarkdown>
                    </div>
                </div>

                 {/* Sources */}
                 {report.result_json.sources && report.result_json.sources.length > 0 && (
                    <div className="bg-brand-950/50 p-6 rounded-xl border border-brand-800/50">
                        <div className="flex items-center gap-2 mb-4 text-brand-500">
                            <Database size={16} />
                            <h4 className="text-xs font-bold uppercase tracking-wider">Sources & Grounding</h4>
                        </div>
                        <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {report.result_json.sources.map((s, i) => (
                                <li key={i} className="text-sm truncate group">
                                    <a href={s} target="_blank" rel="noreferrer" className="text-brand-400 group-hover:text-accent transition-colors flex items-center gap-2">
                                        <div className="w-1.5 h-1.5 bg-brand-700 rounded-full group-hover:bg-accent transition-colors flex-shrink-0"></div>
                                        <span className="truncate">{s}</span>
                                        <ArrowRight size={12} className="opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all" />
                                    </a>
                                </li>
                            ))}
                        </ul>
                    </div>
                 )}
              </>
          )}
      </div>
    </div>
  );
};

export default Dashboard;
