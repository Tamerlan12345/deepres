import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { BrainCircuit, Lock, User, ArrowRight, Zap } from 'lucide-react';

const Home = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
        const res = await axios.post('/api/login', { username, password });
        localStorage.setItem('token', res.data.access_token);
        localStorage.setItem('admin', res.data.admin);
        navigate('/dashboard');
    } catch (err) {
        console.error(err);
        setError('Неверный логин или пароль');
        setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-brand-950 text-white flex flex-col items-center justify-center relative overflow-hidden font-sans selection:bg-accent selection:text-brand-950">
       {/* Background Glow */}
       <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-accent/5 rounded-full blur-[100px] -z-10 animate-pulse-slow"></div>

       <div className="w-full max-w-md p-8 bg-brand-900/50 backdrop-blur-xl border border-brand-800 rounded-2xl shadow-2xl animate-fade-in-up mx-4">
          <div className="flex flex-col items-center mb-8">
               <div className="w-16 h-16 bg-brand-800 rounded-2xl flex items-center justify-center mb-4 border border-brand-700 shadow-glow">
                   <img src="https://centras.kz/wp-content/uploads/2023/12/centras-insurance-col.png" alt="Logo" className="w-30 h-30 object-contain" />
               </div>
               <h1 className="text-2xl font-bold tracking-tight">Centras <span className="text-brand-400">DeepResearch</span></h1>
               <p className="text-brand-500 text-sm mt-2">Вход в систему</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
              {error && (
                  <div className="p-3 bg-red-900/20 border border-red-900/50 rounded-lg text-red-400 text-sm text-center">
                      {error}
                  </div>
              )}

              <div className="space-y-2">
                  <label className="text-sm font-medium text-brand-300 ml-1">Логин</label>
                  <div className="relative group">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 text-brand-500 group-focus-within:text-accent transition-colors" size={18} />
                      <input
                          type="text"
                          value={username}
                          onChange={(e) => setUsername(e.target.value)}
                          className="w-full bg-brand-950 border border-brand-800 text-white rounded-lg py-3 pl-10 pr-4 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-all placeholder:text-brand-700"
                          placeholder="Введите имя пользователя"
                      />
                  </div>
              </div>

              <div className="space-y-2">
                  <label className="text-sm font-medium text-brand-300 ml-1">Пароль</label>
                  <div className="relative group">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-brand-500 group-focus-within:text-accent transition-colors" size={18} />
                      <input
                          type="password"
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          className="w-full bg-brand-950 border border-brand-800 text-white rounded-lg py-3 pl-10 pr-4 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-all placeholder:text-brand-700"
                          placeholder="Введите пароль"
                      />
                  </div>
              </div>

              <button
                  type="submit"
                  disabled={loading}
                  className="w-full btn-primary py-3 text-base shadow-lg shadow-accent/20 flex items-center justify-center gap-2 group"
              >
                  {loading ? <Zap className="animate-spin" size={20} /> : <span>Войти</span>}
                  {!loading && <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />}
              </button>
          </form>

          <div className="mt-8 text-center">
              <p className="text-xs text-brand-600">
                  &copy; 2026 Centras Insurance. <br/>Authorized personnel only.
              </p>
          </div>
       </div>
    </div>
  );
};

export default Home;
