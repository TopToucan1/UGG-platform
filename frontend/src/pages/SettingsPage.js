import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { GearSix, Buildings, MapPin, Users, WifiHigh, ChartBar } from '@phosphor-icons/react';

export default function SettingsPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState(null);
  const [tenants, setTenants] = useState([]);
  const [sites, setSites] = useState([]);
  const [users, setUsers] = useState([]);
  const [agents, setAgents] = useState([]);

  useEffect(() => {
    api.get('/admin/stats').then(r => setStats(r.data)).catch(() => {});
    api.get('/admin/tenants').then(r => setTenants(r.data.tenants || [])).catch(() => {});
    api.get('/admin/sites').then(r => setSites(r.data.sites || [])).catch(() => {});
    api.get('/admin/agents').then(r => setAgents(r.data.agents || [])).catch(() => {});
    if (user?.role === 'admin') {
      api.get('/admin/users').then(r => setUsers(r.data.users || [])).catch(() => {});
    }
  }, [user]);

  const tabs = [
    { id: 'overview', label: 'Overview', icon: ChartBar },
    { id: 'tenants', label: 'Tenants', icon: Buildings },
    { id: 'sites', label: 'Sites', icon: MapPin },
    { id: 'users', label: 'Users', icon: Users },
    { id: 'agents', label: 'Agents', icon: WifiHigh },
  ];

  return (
    <div data-testid="settings-page" className="space-y-4">
      <h1 className="font-heading text-2xl font-bold tracking-tight flex items-center gap-3" style={{ color: '#E8ECF1' }}>
        <GearSix size={24} /> Settings
      </h1>

      <div className="flex gap-2 border-b pb-0" style={{ borderColor: '#272E3B' }}>
        {tabs.map(t => (
          <button
            key={t.id}
            data-testid={`settings-tab-${t.id}`}
            onClick={() => setActiveTab(t.id)}
            className="flex items-center gap-2 px-4 py-2.5 text-xs font-medium uppercase tracking-wider transition-colors"
            style={{
              color: activeTab === t.id ? '#00D4AA' : '#6B7A90',
              borderBottom: activeTab === t.id ? '2px solid #00D4AA' : '2px solid transparent',
            }}
          >
            <t.icon size={16} /> {t.label}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && stats && (
        <div className="grid grid-cols-3 gap-4" data-testid="settings-overview">
          {Object.entries(stats).map(([key, val]) => (
            <div key={key} className="rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
              <div className="text-[11px] uppercase tracking-wider mb-2" style={{ color: '#6B7A90' }}>{key.replace(/_/g, ' ')}</div>
              <div className="font-mono text-2xl font-bold" style={{ color: '#E8ECF1' }}>{val}</div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'tenants' && (
        <div className="space-y-2" data-testid="settings-tenants">
          {tenants.map(t => (
            <div key={t.id} className="rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium" style={{ color: '#E8ECF1' }}>{t.name}</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded capitalize" style={{ background: 'rgba(0,212,170,0.1)', color: '#00D4AA' }}>{t.status}</span>
              </div>
              <div className="text-xs font-mono mt-1" style={{ color: '#6B7A90' }}>Plan: {t.plan} | ID: {t.id?.slice(0, 8)}</div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'sites' && (
        <div className="space-y-2" data-testid="settings-sites">
          {sites.map(s => (
            <div key={s.id} className="rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium" style={{ color: '#E8ECF1' }}>{s.name}</span>
                <span className="font-mono text-xs" style={{ color: '#00D4AA' }}>{s.device_count} devices</span>
              </div>
              <div className="text-xs mt-1" style={{ color: '#6B7A90' }}>{s.location}</div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'users' && (
        <div className="rounded border overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="settings-users">
          <div className="grid grid-cols-4 gap-2 px-4 py-2 text-[11px] uppercase tracking-wider font-medium border-b" style={{ color: '#6B7A90', borderColor: '#272E3B' }}>
            <div>Name</div><div>Email</div><div>Role</div><div>Created</div>
          </div>
          {users.map(u => (
            <div key={u.id || u.email} className="grid grid-cols-4 gap-2 px-4 py-2.5 border-b text-xs" style={{ borderColor: '#272E3B20' }}>
              <div style={{ color: '#E8ECF1' }}>{u.name}</div>
              <div className="font-mono" style={{ color: '#A3AEBE' }}>{u.email}</div>
              <div><span className="px-1.5 py-0.5 rounded text-[10px] font-mono" style={{ background: 'rgba(0,212,170,0.1)', color: '#00D4AA' }}>{u.role}</span></div>
              <div className="font-mono" style={{ color: '#6B7A90' }}>{u.created_at ? new Date(u.created_at).toLocaleDateString() : '--'}</div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'agents' && (
        <div className="space-y-2" data-testid="settings-agents">
          {agents.map(a => (
            <div key={a.id} className="rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${a.status === 'connected' ? 'pulse-online' : ''}`} style={{ background: a.status === 'connected' ? '#00D4AA' : '#FF3B30' }} />
                  <span className="text-sm font-medium font-mono" style={{ color: '#E8ECF1' }}>{a.name}</span>
                </div>
                <span className="text-xs font-mono" style={{ color: '#6B7A90' }}>v{a.version}</span>
              </div>
              <div className="text-xs font-mono mt-1" style={{ color: '#6B7A90' }}>
                {a.os} | {a.ip_address} | Last heartbeat: {new Date(a.last_heartbeat).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
