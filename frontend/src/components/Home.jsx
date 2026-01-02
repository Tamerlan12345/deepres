import React from 'react';
import { useNavigate } from 'react-router-dom';
import { BrainCircuit } from 'lucide-react';

const Home = () => {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-brand-950 flex flex-col items-center justify-center text-white relative overflow-hidden">
             {/* Background Decoration */}
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none z-0 opacity-20"></div>

             <div className="relative z-10 text-center space-y-8 p-6">
                <div className="flex justify-center mb-6">
                    <div className="p-4 bg-brand-800 rounded-2xl border border-brand-700 shadow-2xl shadow-accent/20">
                        <BrainCircuit className="text-accent w-24 h-24" />
                    </div>
                </div>

                <h1 className="text-5xl md:text-6xl font-bold tracking-tight">
                    Centras Strategic AI-Agent
                </h1>

                <p className="text-xl text-brand-300 max-w-2xl mx-auto font-light leading-relaxed">
                    Интеллектуальная система глубокого поиска и анализа страхового рынка.
                </p>

                <div className="pt-8">
                     <button
                        onClick={() => navigate('/dashboard')}
                        className="px-8 py-4 bg-accent hover:bg-accent/90 text-brand-950 font-bold text-lg rounded-full shadow-[0_0_20px_rgba(56,189,248,0.3)] hover:shadow-[0_0_30px_rgba(56,189,248,0.5)] transition-all transform hover:scale-105"
                     >
                        Начать работу
                     </button>
                </div>
             </div>
        </div>
    );
};

export default Home;
