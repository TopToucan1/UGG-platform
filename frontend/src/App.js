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
import FinancialPage from '@/pages/FinancialPage';
import PlayerSessionsPage from '@/pages/PlayerSessionsPage';
import MarketplacePage from '@/pages/MarketplacePage';
import JackpotPage from '@/pages/JackpotPage';
import ExportPage from '@/pages/ExportPage';
import CommandCenterPage from '@/pages/CommandCenterPage';
import ContentLabPage from '@/pages/ContentLabPage';
import RouteOpsPage from '@/pages/RouteOpsPage';
import RegulatoryDashboardPage from '@/pages/RegulatoryDashboardPage';
import RouteMapPage from '@/pages/RouteMapPage';
import CertificationPage from '@/pages/CertificationPage';
import DigitalTwinPage from '@/pages/DigitalTwinPage';
import AnalyzerPage from '@/pages/AnalyzerPage';
import ProxyControlPage from '@/pages/ProxyControlPage';
import FleetDashboardPage from '@/pages/FleetDashboardPage';
import ComplianceBrowserPage from '@/pages/ComplianceBrowserPage';

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

function FullscreenRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen flex items-center justify-center" style={{ background: '#0A0C10' }}><div className="w-8 h-8 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: '#00D4AA', borderTopColor: 'transparent' }} /></div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
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
      <Route path="/financial" element={<ProtectedRoute><FinancialPage /></ProtectedRoute>} />
      <Route path="/players" element={<ProtectedRoute><PlayerSessionsPage /></ProtectedRoute>} />
      <Route path="/jackpots" element={<ProtectedRoute><JackpotPage /></ProtectedRoute>} />
      <Route path="/connectors" element={<ProtectedRoute><ConnectorBuilderPage /></ProtectedRoute>} />
      <Route path="/marketplace" element={<ProtectedRoute><MarketplacePage /></ProtectedRoute>} />
      <Route path="/ai-studio" element={<ProtectedRoute><AIStudioPage /></ProtectedRoute>} />
      <Route path="/emulator" element={<ProtectedRoute><EmulatorLabPage /></ProtectedRoute>} />
      <Route path="/audit" element={<ProtectedRoute><AuditExplorerPage /></ProtectedRoute>} />
      <Route path="/alerts" element={<ProtectedRoute><AlertConsolePage /></ProtectedRoute>} />
      <Route path="/messages" element={<ProtectedRoute><MessageComposerPage /></ProtectedRoute>} />
      <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
      <Route path="/export" element={<ProtectedRoute><ExportPage /></ProtectedRoute>} />
      <Route path="/content-lab" element={<ProtectedRoute><ContentLabPage /></ProtectedRoute>} />
      <Route path="/route-ops" element={<ProtectedRoute><RouteOpsPage /></ProtectedRoute>} />
      <Route path="/regulatory" element={<ProtectedRoute><RegulatoryDashboardPage /></ProtectedRoute>} />
      <Route path="/map" element={<ProtectedRoute><RouteMapPage /></ProtectedRoute>} />
      <Route path="/certification" element={<ProtectedRoute><CertificationPage /></ProtectedRoute>} />
      <Route path="/digital-twin" element={<ProtectedRoute><DigitalTwinPage /></ProtectedRoute>} />
      <Route path="/analyzer" element={<ProtectedRoute><AnalyzerPage /></ProtectedRoute>} />
      <Route path="/proxy" element={<ProtectedRoute><ProxyControlPage /></ProtectedRoute>} />
      <Route path="/fleet" element={<ProtectedRoute><FleetDashboardPage /></ProtectedRoute>} />
      <Route path="/compliance" element={<ProtectedRoute><ComplianceBrowserPage /></ProtectedRoute>} />
      <Route path="/command-center" element={<FullscreenRoute><CommandCenterPage /></FullscreenRoute>} />
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
