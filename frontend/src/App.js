import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import AppShell from '@/components/layout/AppShell';
import LoginPage from '@/pages/LoginPage';
import DashboardPage from '@/pages/DashboardPage';
import DevicesPage from '@/pages/DevicesPage';
import ConnectorBuilderPage from '@/pages/ConnectorBuilderPage';
import AIStudioPage from '@/pages/AIStudioPage';
import EmulatorLabPage from '@/pages/EmulatorLabPage';
import AuditExplorerPage from '@/pages/AuditExplorerPage';
import AlertConsolePage from '@/pages/AlertConsolePage';
import MessageComposerPage from '@/pages/MessageComposerPage';
import SettingsPage from '@/pages/SettingsPage';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#0A0C10' }}>
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-t-transparent rounded-full animate-spin mx-auto" style={{ borderColor: '#00D4AA', borderTopColor: 'transparent' }} />
          <div className="text-sm mt-3" style={{ color: '#6B7A90' }}>Loading UGG Platform...</div>
        </div>
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  return <AppShell>{children}</AppShell>;
}

function AppRoutes() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#0A0C10' }}>
        <div className="w-8 h-8 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: '#00D4AA', borderTopColor: 'transparent' }} />
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <LoginPage />} />
      <Route path="/" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
      <Route path="/devices" element={<ProtectedRoute><DevicesPage /></ProtectedRoute>} />
      <Route path="/connectors" element={<ProtectedRoute><ConnectorBuilderPage /></ProtectedRoute>} />
      <Route path="/ai-studio" element={<ProtectedRoute><AIStudioPage /></ProtectedRoute>} />
      <Route path="/emulator" element={<ProtectedRoute><EmulatorLabPage /></ProtectedRoute>} />
      <Route path="/audit" element={<ProtectedRoute><AuditExplorerPage /></ProtectedRoute>} />
      <Route path="/alerts" element={<ProtectedRoute><AlertConsolePage /></ProtectedRoute>} />
      <Route path="/messages" element={<ProtectedRoute><MessageComposerPage /></ProtectedRoute>} />
      <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
