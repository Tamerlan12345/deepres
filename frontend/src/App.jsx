import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';

function App() {
  const [currentReportId, setCurrentReportId] = useState(null);

  return (
    <div className="flex h-screen w-full bg-brand-950 overflow-hidden">
      <Sidebar onSelectReport={setCurrentReportId} />
      <main className="flex-1 overflow-y-auto bg-brand-950 text-brand-100 relative">
        {/* Background Grid Pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none z-0 opacity-20"></div>

        <div className="relative z-10">
            <Dashboard currentReportId={currentReportId} onNewReport={setCurrentReportId} />
        </div>
      </main>
    </div>
  );
}

export default App;
