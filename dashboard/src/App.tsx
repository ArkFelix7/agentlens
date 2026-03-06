/** Root application component with React Router and all routes. */

import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MainLayout } from '@/components/layout/MainLayout';
import { ToastProvider } from '@/components/shared/Toast';
import { TracesPage } from '@/pages/TracesPage';
import { CostsPage } from '@/pages/CostsPage';
import { HallucinationsPage } from '@/pages/HallucinationsPage';
import { MemoryPage } from '@/pages/MemoryPage';
import { ReplayPage } from '@/pages/ReplayPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { useWebSocket } from '@/hooks/useWebSocket';
import { WebSocketContext } from '@/contexts/WebSocketContext';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 30_000,
    },
  },
});

/** Inner component that calls useWebSocket — requires Router context. */
function AppInner() {
  const wsControls = useWebSocket();
  return (
    <WebSocketContext.Provider value={wsControls}>
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<TracesPage />} />
        <Route path="costs" element={<CostsPage />} />
        <Route path="hallucinations" element={<HallucinationsPage />} />
        <Route path="memory" element={<MemoryPage />} />
        <Route path="replay" element={<ReplayPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
    </WebSocketContext.Provider>
  );
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>
          <AppInner />
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
}
