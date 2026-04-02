import Sidebar from './Sidebar';
import Header from './Header';
import VipAlertOverlay from '@/components/VipAlertOverlay';

export default function AppShell({ children }) {
  return (
    <div className="flex h-screen overflow-hidden" style={{ background: '#0A0C10' }}>
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-6" data-testid="main-content">
          {children}
        </main>
      </div>
      <VipAlertOverlay />
    </div>
  );
}
