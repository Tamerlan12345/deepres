import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { Menu, Zap } from 'lucide-react';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import Home from './components/Home';

// Layout component to handle conditional Sidebar rendering
const Layout = () => {
    const location = useLocation();
    const [currentReportId, setCurrentReportId] = useState(null);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const isHome = location.pathname === '/';

    return (
        <div className="flex h-screen w-full bg-brand-950 overflow-hidden relative">
             {!isHome && (
                <Sidebar
                    onSelectReport={setCurrentReportId}
                    isOpen={isSidebarOpen}
                    onClose={() => setIsSidebarOpen(false)}
                />
             )}

             <main className="flex-1 overflow-y-auto bg-brand-950 text-brand-100 relative flex flex-col">
                 {/* Mobile Header */}
                 {!isHome && (
                    <div className="md:hidden flex items-center justify-between p-4 border-b border-brand-800 bg-brand-900 sticky top-0 z-30">
                        <div className="flex items-center gap-2">
                             <div className="w-8 h-8 bg-accent rounded-md flex items-center justify-center text-white">
                                <Zap size={16} fill="white" />
                             </div>
                             <span className="font-bold text-lg text-white">Centras AI</span>
                        </div>
                        <button
                            onClick={() => setIsSidebarOpen(true)}
                            className="text-brand-300 hover:text-white p-1"
                        >
                            <Menu size={24} />
                        </button>
                    </div>
                 )}

                 {/* Background Grid Pattern */}
                 <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none z-0 opacity-20"></div>

                 <div className="relative z-10 flex-1">
                     <Routes>
                         <Route path="/" element={<Home />} />
                         <Route path="/dashboard" element={<Dashboard currentReportId={currentReportId} onNewReport={setCurrentReportId} />} />
                     </Routes>
                 </div>
             </main>
        </div>
    );
};

function App() {
  return (
    <Router>
        <Layout />
    </Router>
  );
}

export default App;
