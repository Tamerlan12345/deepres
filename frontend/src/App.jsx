import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';

function App() {
  const [currentReportId, setCurrentReportId] = useState(null);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar onSelectReport={setCurrentReportId} />
      <main className="flex-1 overflow-y-auto p-4 bg-gray-100">
        <Dashboard currentReportId={currentReportId} onNewReport={setCurrentReportId} />
      </main>
    </div>
  );
}

export default App;
