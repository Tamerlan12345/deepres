import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import mermaid from 'mermaid';
import { Download, Search, RefreshCw, Zap, Activity, AlertCircle, BrainCircuit } from 'lucide-react';
import {
    BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const LogTerminal = ({ logs, active }) => {
    if (!logs || logs.length === 0) return null;

    return (
        <div className="card bg-black/80 border-brand-800 font-mono text-xs md:text-sm p-4 h-64 overflow-y-auto custom-scrollbar mb-6 flex flex-col-reverse">
            <div>
                {logs.map((log, i) => (
                    <div key={i} className={`mb-2 ${i === logs.length - 1 && active ? 'text-accent animate-pulse' : 'text-brand-400'}`}>
                        <span className="text-brand-600 mr-2">[{log.timestamp}]</span>
                        <span>{log.message}</span>
                    </div>
                ))}
                {active && (
                    <div className="text-accent mt-2">
                        <span className="animate-pulse">_</span>
                    </div>
                )}
            </div>
        </div>
    );
};

const MermaidChart = ({ chart }) => {
    const [svg, setSvg] = useState('');
    const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`;

    useEffect(() => {
      mermaid.render(id, chart).then((result) => {
          setSvg(result.svg);
      }).catch(err => {
          console.error("Mermaid error:", err);
          setSvg(`<div class="text-error">Error rendering diagram</div>`);
      });
    }, [chart, id]);

    return <div className="mermaid-container my-6 flex justify-center bg-brand-900/30 p-4 rounded-lg" dangerouslySetInnerHTML={{ __html: svg }} />;
};

const JsonChart = ({ json }) => {
    try {
        const data = JSON.parse(json);
        const { type, title, data: chartData } = data;

        const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

        const CustomTooltip = ({ active, payload, label }) => {
            if (active && payload && payload.length) {
                return (
                    <div className="bg-brand-900 border border-brand-700 p-2 rounded shadow-lg text-sm">
                        <p className="font-bold text-white">{label}</p>
                        <p className="text-accent">{`${payload[0].name}: ${payload[0].value}`}</p>
                    </div>
                );
            }
            return null;
        };

        const renderChart = () => {
             if (type === 'bar') {
                return (
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                            <XAxis dataKey="name" stroke="#94a3b8" tick={{fontSize: 12}} />
                            <YAxis stroke="#94a3b8" tick={{fontSize: 12}} />
                            <Tooltip content={<CustomTooltip />} cursor={{fill: 'transparent'}} />
                            <Legend wrapperStyle={{paddingTop: '10px'}} />
                            <Bar dataKey="value" fill="#3b82f6" name={title} radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                );
            } else if (type === 'line') {
                 return (
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                            <XAxis dataKey="name" stroke="#94a3b8" tick={{fontSize: 12}} />
                            <YAxis stroke="#94a3b8" tick={{fontSize: 12}} />
                            <Tooltip content={<CustomTooltip />} />
                            <Legend wrapperStyle={{paddingTop: '10px'}} />
                            <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} name={title} dot={{r: 4, fill:'#3b82f6'}} activeDot={{r: 6}} />
                        </LineChart>
                    </ResponsiveContainer>
                 );
            } else if (type === 'pie') {
                return (
                    <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                            <Pie
                                data={chartData}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                outerRadius={100}
                                fill="#8884d8"
                                dataKey="value"
                                nameKey="name"
                            >
                                {chartData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip />
                            <Legend />
                        </PieChart>
                    </ResponsiveContainer>
                );
            }
            return <div className="text-brand-400 p-4 text-center">Unsupported chart type: {type}</div>
        }

        return (
            <div className="card border-brand-800 bg-brand-900/50 p-6 my-8 break-inside-avoid">
                <h4 className="text-lg font-bold text-white mb-4 text-center">{title}</h4>
                {renderChart()}
            </div>
        );
    } catch (e) {
        return <div className="text-error border border-error/20 bg-error-bg p-3 rounded text-sm my-4">Error parsing chart data: {e.message}</div>;
    }
};

const Dashboard = ({ currentReportId, onNewReport }) => {
  const [query, setQuery] = useState("");
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      securityLevel: 'loose',
      fontFamily: 'Inter'
    });
  }, []);

  // Poll for report status if it's processing
  useEffect(() => {
    let interval;
    if (currentReportId) {
      setLoading(true);
      fetchReport(currentReportId);
      interval = setInterval(() => {
        fetchReport(currentReportId);
      }, 2000); // Faster polling for smoother log updates
    }
    return () => clearInterval(interval);
  }, [currentReportId]);

  const fetchReport = async (id) => {
    try {
      const res = await axios.get(`/api/reports/${id}`);
      const data = res.data;
      setReport(data);

      if (data.status === 'COMPLETED') {
        setLoading(false);
      } else if (data.status === 'FAILED') {
        setLoading(false);
        setError("Report generation failed.");
      } else {
        setLoading(true);
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

  const handlePrint = () => {
      window.print();
  };

  return (
    <div className="max-w-6xl mx-auto pb-12 pt-6 px-6">
      {/* Search / Hero Section */}
      <div className="card mb-8 relative overflow-hidden group print:hidden">
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
                <button onClick={() => handleScenario("Анализ динамики активов топ-5 страховых компаний РК за 2024 год (сравнение с 2023).")}
                    className="flex items-center gap-2 px-4 py-2 bg-brand-800/50 text-brand-300 border border-brand-700 rounded-full text-xs font-medium whitespace-nowrap hover:bg-brand-800 hover:text-white hover:border-brand-600 transition-all">
                    📊 Стратегия и Рынок
                </button>
                <button onClick={() => handleScenario("Сравнение условий и тарифов КАСКО для юридических лиц: Centras, Halyk, Eurasia. Плюсы и минусы.")}
                    className="flex items-center gap-2 px-4 py-2 bg-brand-800/50 text-brand-300 border border-brand-700 rounded-full text-xs font-medium whitespace-nowrap hover:bg-brand-800 hover:text-white hover:border-brand-600 transition-all">
                    🚗 Продукт (Авто)
                </button>
                <button onClick={() => handleScenario("Перспективы и объем рынка киберстрахования в Казахстане и СНГ: отчеты и прогнозы на 2025.")}
                    className="flex items-center gap-2 px-4 py-2 bg-brand-800/50 text-brand-300 border border-brand-700 rounded-full text-xs font-medium whitespace-nowrap hover:bg-brand-800 hover:text-white hover:border-brand-600 transition-all">
                    🚀 Новые ниши
                </button>
                <button onClick={() => handleScenario("Обзор жалоб клиентов на ДМС в Казахстане: основные проблемы и рейтинг лояльности.")}
                    className="flex items-center gap-2 px-4 py-2 bg-brand-800/50 text-brand-300 border border-brand-700 rounded-full text-xs font-medium whitespace-nowrap hover:bg-brand-800 hover:text-white hover:border-brand-600 transition-all">
                    🏥 Медицина (ДМС)
                </button>
                <button onClick={() => handleScenario("Последние постановления НБ РК по страхованию жизни: влияние на достаточность капитала.")}
                    className="flex items-center gap-2 px-4 py-2 bg-brand-800/50 text-brand-300 border border-brand-700 rounded-full text-xs font-medium whitespace-nowrap hover:bg-brand-800 hover:text-white hover:border-brand-600 transition-all">
                    ⚖️ Регуляторика
                </button>
                <button onClick={() => handleScenario("Статистика выплат по индексному страхованию влаги в зерновых регионах РК за прошлый сезон.")}
                    className="flex items-center gap-2 px-4 py-2 bg-brand-800/50 text-brand-300 border border-brand-700 rounded-full text-xs font-medium whitespace-nowrap hover:bg-brand-800 hover:text-white hover:border-brand-600 transition-all">
                    🌾 Агро
                </button>
            </div>
        </div>
      </div>

      {/* Report View */}
      <div className="space-y-8 animate-fade-in-up">
          {/* Logs / Progress View */}
          {(loading || (report && report.logs && report.logs.length > 0)) && (
              <div className={`${report && report.status === 'COMPLETED' ? 'mb-8' : ''}`}>
                  {(loading) && (
                     <div className="flex items-center gap-3 mb-4 text-brand-300">
                         <div className="relative">
                            <div className="absolute inset-0 bg-accent rounded-full animate-ping opacity-20"></div>
                            <Activity className="text-accent animate-pulse relative z-10" size={20} />
                         </div>
                         <span className="font-medium">Deep Research Agent Active</span>
                     </div>
                  )}
                  {report && <LogTerminal logs={report.logs} active={loading} />}
              </div>
          )}

          {error && (
               <div className="p-4 bg-error-bg text-error rounded-lg border border-error/20 flex items-center">
                   <AlertCircle className="mr-3" />
                   <span className="font-medium">{error}</span>
               </div>
          )}

          {report && report.status === 'COMPLETED' && report.result_json && (
              <div className="print:text-black animate-fade-in">
                  <div className="flex justify-between items-center mb-6 pb-4 border-b border-brand-800 print:hidden">
                        <h3 className="text-xl font-bold text-white flex items-center gap-3">
                            <BrainCircuit className="text-brand-400" size={24} />
                            Strategic Report
                        </h3>
                        <button onClick={handlePrint} className="btn-secondary flex items-center gap-2 text-sm">
                            <Download size={16} /> Print / Save PDF
                        </button>
                    </div>

                  {/* Markdown Content */}
                  <div className="prose prose-lg prose-invert prose-blue max-w-none
                    prose-headings:text-white prose-p:text-brand-300 prose-strong:text-brand-100 prose-li:text-brand-300
                    print:prose-p:text-black print:prose-headings:text-black print:prose-li:text-black">
                      <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                              code({node, inline, className, children, ...props}) {
                                  const match = /language-(\w+)(?::(\w+))?/.exec(className || '')
                                  const language = match ? match[1] : ''

                                  if (!inline && language === 'mermaid') {
                                      return <MermaidChart chart={String(children).replace(/\n$/, '')} />
                                  }

                                  if (!inline && language === 'json' && className.includes('language-json:chart')) {
                                      return <JsonChart json={String(children).replace(/\n$/, '')} />
                                  }

                                  return !inline ? (
                                      <pre className="bg-brand-900/50 p-4 rounded-lg overflow-x-auto border border-brand-800 print:border-gray-300 print:bg-gray-50">
                                          <code className={className} {...props}>
                                              {children}
                                          </code>
                                      </pre>
                                  ) : (
                                      <code className="bg-brand-900/50 px-1.5 py-0.5 rounded text-accent font-mono text-sm print:bg-gray-100 print:text-black" {...props}>
                                          {children}
                                      </code>
                                  )
                              }
                          }}
                      >
                          {report.result_json.markdown || report.result_json.detailed_analysis || "No content"}
                      </ReactMarkdown>
                  </div>
              </div>
          )}
      </div>
    </div>
  );
};

export default Dashboard;
