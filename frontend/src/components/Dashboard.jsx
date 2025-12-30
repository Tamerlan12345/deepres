import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { Download, Send, RefreshCw, AlertCircle } from 'lucide-react';
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

const Dashboard = ({ currentReportId, onNewReport }) => {
  const [query, setQuery] = useState("");
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Poll for report status if it's processing
  useEffect(() => {
    let interval;
    if (currentReportId) {
      fetchReport(currentReportId);
      interval = setInterval(() => {
        fetchReport(currentReportId);
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [currentReportId]);

  const fetchReport = async (id) => {
    try {
      const res = await axios.get(`/api/reports/${id}`);
      setReport(res.data);
      if (res.data.status === 'COMPLETED' || res.data.status === 'FAILED') {
        // Stop polling done inside useEffect cleanup or manually if I managed interval state
        // Here simply relying on React to update and next render might clear it if I change logic
        // But simpler: just check status in render.
      }
    } catch (e) {
        console.error(e);
        setError("Could not fetch report");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const res = await axios.post('/api/reports', { query });
      onNewReport(res.data.id);
      setQuery("");
    } catch (e) {
      setError("Failed to create report");
    } finally {
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
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="bg-white p-6 rounded-lg shadow-sm mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Strategic Analysis Center</h2>

        <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
            <button onClick={() => handleScenario("Анализ конкурентов (Евразия, Халык, Фридом)")} className="px-4 py-2 bg-blue-100 text-blue-800 rounded-full text-sm whitespace-nowrap hover:bg-blue-200">
                🏢 Competitor Deep Dive
            </button>
            <button onClick={() => handleScenario("Мониторинг регуляторных изменений в страховании")} className="px-4 py-2 bg-green-100 text-green-800 rounded-full text-sm whitespace-nowrap hover:bg-green-200">
                ⚖️ Regulatory Check
            </button>
            <button onClick={() => handleScenario("Сравнение условий КАСКО (Centras vs Freedom)")} className="px-4 py-2 bg-purple-100 text-purple-800 rounded-full text-sm whitespace-nowrap hover:bg-purple-200">
                🛡️ Product Benchmark
            </button>
        </div>

        <form onSubmit={handleSubmit} className="relative">
            <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask for strategic analysis (e.g., 'Compare our Q3 GWP with competitors')"
                className="w-full p-4 pr-12 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
            <button type="submit" disabled={loading} className="absolute right-3 top-3 p-2 bg-centrasBlue text-white rounded hover:bg-blue-800 disabled:opacity-50">
                <Send size={20} />
            </button>
        </form>
      </div>

      {/* Report View */}
      {report && (
          <div className="space-y-6">
              {/* Status */}
              {report.status !== 'COMPLETED' && report.status !== 'FAILED' && (
                  <div className="flex items-center justify-center p-10 bg-white rounded shadow animate-pulse">
                      <RefreshCw className="animate-spin mr-2 text-blue-600" />
                      <span className="text-lg text-gray-600">Deep Research in Progress... This may take a minute.</span>
                  </div>
              )}

              {report.status === 'FAILED' && (
                   <div className="p-4 bg-red-100 text-red-700 rounded flex items-center">
                       <AlertCircle className="mr-2" />
                       Failed to generate report. Please try again.
                   </div>
              )}

              {report.status === 'COMPLETED' && report.result_json && (
                  <>
                    {/* Summary Card */}
                    <div className="bg-white p-6 rounded shadow border-l-4 border-centrasRed">
                        <h3 className="text-xl font-bold mb-2">Executive Summary</h3>
                        <p className="text-gray-700 leading-relaxed">{report.result_json.summary}</p>
                    </div>

                    {/* Key Metrics */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {report.result_json.key_metrics?.map((metric, i) => (
                            <div key={i} className="bg-white p-4 rounded shadow">
                                <p className="text-sm text-gray-500">{metric.label}</p>
                                <p className="text-2xl font-bold text-gray-800">{metric.value}</p>
                                <p className={`text-sm ${metric.change?.includes('+') ? 'text-green-600' : 'text-red-600'}`}>
                                    {metric.change} {metric.trend}
                                </p>
                            </div>
                        ))}
                    </div>

                    {/* Charts */}
                    {renderCharts(report.result_json.charts_data)}

                    {/* Detailed Analysis */}
                    <div className="bg-white p-8 rounded shadow">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-bold">Detailed Analysis</h3>
                            <a href={`/api/reports/${report.id}/pdf`} target="_blank" rel="noreferrer" className="flex items-center text-blue-600 hover:text-blue-800">
                                <Download size={18} className="mr-1" /> Download PDF
                            </a>
                        </div>
                        <div className="prose max-w-none text-gray-800">
                            <ReactMarkdown>{report.result_json.detailed_analysis}</ReactMarkdown>
                        </div>
                    </div>

                     {/* Sources */}
                     <div className="text-sm text-gray-500 mt-4">
                        <strong>Sources:</strong>
                        <ul className="list-disc pl-5">
                            {report.result_json.sources?.map((s, i) => (
                                <li key={i}><a href={s} target="_blank" rel="noreferrer" className="text-blue-500 hover:underline">{s}</a></li>
                            ))}
                        </ul>
                    </div>
                  </>
              )}
          </div>
      )}
    </div>
  );
};

export default Dashboard;
