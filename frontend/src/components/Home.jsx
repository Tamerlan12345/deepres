import React from 'react';
import { useNavigate } from 'react-router-dom';
import { BrainCircuit, LogOut, ArrowRight, ShieldCheck, Zap } from 'lucide-react';

const Home = () => {
  const navigate = useNavigate();

  const handleStart = () => {
    navigate('/dashboard');
  };

  const handleLogout = () => {
    // Логика выхода (очистка токенов, если есть)
    console.log("User logged out");
    alert("Выход из системы...");
    // В реальности здесь был бы редирект на /login
  };

  return (
    <div className="min-h-screen bg-brand-950 text-white flex flex-col relative overflow-hidden font-sans selection:bg-accent selection:text-brand-950">

      {/* Header */}
      <header className="flex justify-between items-center p-6 border-b border-brand-800 bg-brand-950/80 backdrop-blur-md sticky top-0 z-50">
        <div className="flex items-center gap-2">
           <BrainCircuit className="text-accent" size={32} />
           <h1 className="text-xl font-bold tracking-tight">Centras <span className="text-brand-400">DeepResearch</span></h1>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-brand-300 hover:text-white hover:bg-brand-800 rounded-lg transition-all"
        >
          <LogOut size={18} />
          <span>Выйти</span>
        </button>
      </header>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col justify-center items-center text-center px-6 relative z-10">
        {/* Background Glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-accent/10 rounded-full blur-[100px] -z-10 animate-pulse-slow"></div>

        <div className="max-w-3xl space-y-8 animate-fade-in-up">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-accent/30 bg-accent/10 text-accent text-xs font-bold uppercase tracking-widest mb-4">
                <Zap size={14} /> AI-Powered Analytics v2.0
            </div>

            <h2 className="text-5xl md:text-7xl font-extrabold tracking-tight leading-tight">
                Стратегическое превосходство <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-accent">через данные</span>
            </h2>

            <p className="text-lg md:text-xl text-brand-300 max-w-2xl mx-auto leading-relaxed">
                Автономный AI-агент для глубокого анализа страхового рынка, конкурентной разведки и мониторинга регуляторных рисков.
            </p>

            <div className="flex flex-col sm:flex-row justify-center gap-4 pt-4">
                <button
                    onClick={handleStart}
                    className="btn-primary px-8 py-4 text-lg shadow-xl shadow-accent/20 flex items-center justify-center gap-3 group"
                >
                    Начать исследование
                    <ArrowRight className="group-hover:translate-x-1 transition-transform" />
                </button>
                <button className="px-8 py-4 rounded-lg border border-brand-700 hover:bg-brand-800 hover:border-brand-600 text-brand-200 transition-all font-medium flex items-center justify-center gap-2">
                    <ShieldCheck size={20} />
                    Документация
                </button>
            </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="p-6 text-center text-brand-500 text-sm border-t border-brand-900">
        &copy; 2026 Centras Insurance. Confidential. Powered by Gemini Pro.
      </footer>
    </div>
  );
};

export default Home;
