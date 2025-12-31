import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { Download, Send, RefreshCw, AlertCircle, BrainCircuit, Search, FileText, Database } from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              {chartsData.map((chart, idx) => {
                  if (chart.type === 'bar') {
                    const data = {
                        labels: chart.labels,
                        datasets: chart.datasets.map(ds => ({
                            label: ds.label,
                            data: ds.data,
                            backgroundColor: 'rgba(0, 51, 102, 0.7)',
                        }))
                    };
                    return (
                        <div key={idx} className="bg-white p-4 rounded shadow">
                            <Bar options={{ responsive: true, plugins: { title: { display: true, text: chart.title } } }} data={data} />
                        </div>
                    );
                  }
                  return null;
              })}
          </div>
      );
  };

  return (
    <div className="max-w-5xl mx-auto pb-10">
      {/* Header */}
      <div className="bg-white p-6 rounded-lg shadow-sm mb-6 border-t-4 border-centrasBlue">
        <div className="flex items-center gap-2 mb-4">
            <BrainCircuit className="text-centrasBlue" size={32} />
            <h2 className="text-2xl font-bold text-gray-800">Centras Deep Research Agent</h2>
        </div>
        <p className="text-gray-500 mb-4">
            Powered by Gemini Deep Research Pro. Capable of autonomous iterative search and complex reasoning.
        </p>

        <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
            <button onClick={() => handleScenario("Анализ конкурентов (Евразия, Халык, Фридом): Прибыль и GWP за Q3 2024")} className="px-4 py-2 bg-blue-50 text-blue-700 border border-blue-200 rounded-full text-sm whitespace-nowrap hover:bg-blue-100 transition">
                🏢 Competitor Deep Dive
            </button>
            <button onClick={() => handleScenario("Мониторинг регуляторных изменений в страховании РК за последние 3 месяца")} className="px-4 py-2 bg-green-50 text-green-700 border border-green-200 rounded-full text-sm whitespace-nowrap hover:bg-green-100 transition">
                ⚖️ Regulatory Check
            </button>
            <button onClick={() => handleScenario("Сравни условия КАСКО (Centras vs Freedom) по данным с сайтов")} className="px-4 py-2 bg-purple-50 text-purple-700 border border-purple-200 rounded-full text-sm whitespace-nowrap hover:bg-purple-100 transition">
                🛡️ Product Benchmark
            </button>
        </div>

        <form onSubmit={handleSubmit} className="relative">
            <div className="relative">
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Enter your strategic question (e.g., 'Why is competitor profit margin declining?')"
                    className="w-full p-4 pr-32 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:outline-none shadow-sm text-lg"
                />
                <button
                    type="submit"
                    disabled={loading || !query.trim()}
                    className="absolute right-2 top-2 bottom-2 px-4 bg-centrasBlue text-white rounded-md hover:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition"
                >
                    {loading ? <RefreshCw className="animate-spin" size={18} /> : <Search size={18} />}
                    <span>Deep Analysis</span>
                </button>
            </div>
        </form>
      </div>

      {/* Report View */}
      <div className="space-y-6">
          {loading && (!report || report.status !== 'COMPLETED' && report.status !== 'FAILED') && (
              <div className="flex flex-col items-center justify-center p-12 bg-white rounded-lg shadow-sm border border-gray-100">
                  <div className="relative mb-6">
                    <div className="absolute inset-0 bg-blue-100 rounded-full animate-ping opacity-75"></div>
                    <div className="relative bg-white p-4 rounded-full border-2 border-blue-100 shadow-sm">
                        <BrainCircuit className="text-centrasBlue animate-pulse" size={40} />
                    </div>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-800 mb-2">Deep Research in Progress</h3>
                  <p className="text-gray-500 text-center max-w-md animate-fade-in-up">
                      {LOADING_MESSAGES[loadingMsgIndex]}
                  </p>
                  <div className="mt-6 flex gap-2">
                      <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0s'}}></div>
                      <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                      <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0.4s'}}></div>
                  </div>
              </div>
          )}

          {error && (
               <div className="p-4 bg-red-50 text-red-700 rounded border border-red-200 flex items-center">
                   <AlertCircle className="mr-2" />
                   {error}
               </div>
          )}

          {report && report.status === 'COMPLETED' && report.result_json && (
              <>
                {/* Summary Card */}
                <div className="bg-white p-6 rounded-lg shadow-sm border-l-4 border-centrasRed">
                    <div className="flex items-center gap-2 mb-3 text-centrasRed">
                        <FileText size={20} />
                        <h3 className="text-lg font-bold uppercase tracking-wide">Executive Summary</h3>
                    </div>
                    <p className="text-gray-800 text-lg leading-relaxed">{report.result_json.summary}</p>
                </div>

                {/* Key Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {report.result_json.key_metrics?.map((metric, i) => (
                        <div key={i} className="bg-white p-5 rounded-lg shadow-sm border border-gray-100 hover:shadow-md transition">
                            <p className="text-sm text-gray-500 font-medium uppercase mb-1">{metric.label}</p>
                            <p className="text-3xl font-bold text-gray-900 mb-1">{metric.value}</p>
                            {metric.change && (
                                <div className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${metric.change?.includes('+') || metric.trend === 'Рост' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                    {metric.change} {metric.trend && `• ${metric.trend}`}
                                </div>
                            )}
                        </div>
                    ))}
                </div>

                {/* Charts */}
                {renderCharts(report.result_json.charts_data)}

                {/* Detailed Analysis */}
                <div className="bg-white p-8 rounded-lg shadow-sm border border-gray-100">
                    <div className="flex justify-between items-center mb-6 pb-4 border-b border-gray-100">
                        <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                            <BrainCircuit className="text-gray-400" size={24} />
                            Detailed Analysis
                        </h3>
                        <a href={`/api/reports/${report.id}/pdf`} target="_blank" rel="noreferrer" className="flex items-center px-3 py-1.5 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition text-sm font-medium">
                            <Download size={16} className="mr-2" /> Export PDF
                        </a>
                    </div>
                    <div className="prose prose-blue max-w-none text-gray-700">
                        <ReactMarkdown>{report.result_json.detailed_analysis}</ReactMarkdown>
                    </div>
                </div>

                 {/* Sources */}
                 {report.result_json.sources && report.result_json.sources.length > 0 && (
                    <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                        <div className="flex items-center gap-2 mb-2 text-gray-600">
                            <Database size={16} />
                            <h4 className="text-sm font-bold uppercase">Sources & Grounding</h4>
                        </div>
                        <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
                            {report.result_json.sources.map((s, i) => (
                                <li key={i} className="text-sm truncate">
                                    <a href={s} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline flex items-center gap-1">
                                        <span className="w-1.5 h-1.5 bg-blue-400 rounded-full flex-shrink-0"></span>
                                        {s}
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
