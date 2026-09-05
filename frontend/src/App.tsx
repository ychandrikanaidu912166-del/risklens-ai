import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from './layouts/DashboardLayout';
import { Overview } from './pages/Overview';
import { InvestigationQueue } from './pages/InvestigationQueue';
import { InvestigationDetail } from './pages/InvestigationDetail';
import { ModelMonitoring } from './pages/ModelMonitoring';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardLayout />}>
          <Route index element={<Overview />} />
          <Route path="investigations" element={<InvestigationQueue />} />
          <Route path="investigations/:id" element={<InvestigationDetail />} />
          <Route path="model-monitoring" element={<ModelMonitoring />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
