import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import Home from './components/Home';

// Layout component to handle conditional Sidebar rendering
const Layout = () => {
    const location = useLocation();
    const [currentReportId, setCurrentReportId] = useState(null);
    const isHome = location.pathname === '/';

    return (
        <div className="flex h-screen w-full bg-brand-950 overflow-hidden">
             {!isHome && <Sidebar onSelectReport={setCurrentReportId} />}
             <main className="flex-1 overflow-y-auto bg-brand-950 text-brand-100 relative">
                 {/* Background Grid Pattern */}
                 <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none z-0 opacity-20"></div>

                 <div className="relative z-10">
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
