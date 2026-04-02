import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import { Desktop, Warning, Queue, Lightning, SealCheck, WifiX, Wrench, XCircle } from '@phosphor-icons/react';
import Marquee from 'react-fast-marquee';
import { useNavigate } from 'react-router-dom';

function SummaryCard({ title, icon: Icon, data, color, onClick, testId }) {
  return (
    <button
      data-testid={testId}
      onClick={onClick}
      className="rounded border p-4 text-left transition-all duration-150 hover:-translate-y-[1px]"
      style={{ background: '#12151C', borderColor: '#272E3B' }}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium uppercase tracking-wider" style={{ color: '#6B7A90' }}>{title}</span>
        <Icon size={20} style={{ color }} />
      </div>
      <div className="font-mono text-2xl font-bold" style={{ color: '#E8ECF1' }}>{data.main}</div>
      {data.sub && <div className="text-xs mt-1 font-mono" style={{ color: '#A3AEBE' }}>{data.sub}</div>}
    </button>
  );
}

function StatusBadge({ status }) {
  const colors = { online: '#00D4AA', offline: '#FF3B30', error: '#FF3B30', maintenance: '#F5A623' };
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`w-2 h-2 rounded-full ${status === 'online' ? 'pulse-online' : ''}`} style={{ background: colors[status] || '#6B7A90' }} />
      <span className="text-xs font-mono capitalize" style={{ color: colors[status] || '#6B7A90' }}>{status}</span>
    </span>
  );
}

function SeverityBadge({ severity }) {
  const colors = { critical: '#FF3B30', warning: '#F5A623', info: '#007AFF' };
  return (
    <span className="text-xs font-mono px-2 py-0.5 rounded" style={{ background: `${colors[severity] || '#6B7A90'}20`, color: colors[severity] || '#6B7A90' }}>
      {severity}
    </span>
  );
}

export default function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [devices, setDevices] = useState([]);
  const [events, setEvents] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const navigate = useNavigate();

  const fetchData = useCallback(async () => {
    try {
      const [sumRes, devRes, evtRes, alertRes] = await Promise.all([
        api.get('/dashboard/summary'),
        api.get('/dashboard/device-health?limit=60'),
        api.get('/dashboard/recent-events?limit=30'),
        api.get('/dashboard/recent-alerts?limit=15'),
      ]);
      setSummary(sumRes.data);
      setDevices(devRes.data.devices || []);
      setEvents(evtRes.data.events || []);
      setAlerts(alertRes.data.alerts || []);
    } catch (err) {
      console.error('Dashboard fetch error:', err);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const s = summary;

  return (
    <div data-testid="estate-dashboard" className="space-y-6">
      {/* Page Title */}
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-2xl font-bold tracking-tight" style={{ color: '#E8ECF1' }}>Estate Dashboard</h1>
        <span className="text-xs font-mono" style={{ color: '#6B7A90' }}>
          Auto-refresh: 15s
        </span>
      </div>

      {/* Summary Strip */}
      <div className="grid grid-cols-4 gap-4" data-testid="summary-strip">
        <SummaryCard
          testId="summary-devices"
          title="Total Devices"
          icon={Desktop}
          color="#00D4AA"
          data={{
            main: s?.devices?.total ?? '--',
            sub: `${s?.devices?.online ?? 0} online / ${s?.devices?.offline ?? 0} offline / ${s?.devices?.error ?? 0} error`
          }}
          onClick={() => navigate('/devices')}
        />
        <SummaryCard
          testId="summary-alerts"
          title="Active Alerts"
          icon={Warning}
          color="#FF3B30"
          data={{
            main: s?.alerts?.active ?? '--',
            sub: `${s?.alerts?.critical ?? 0} critical / ${s?.alerts?.warning ?? 0} warning`
          }}
          onClick={() => navigate('/alerts')}
        />
        <SummaryCard
          testId="summary-commands"
          title="Command Queue"
          icon={Queue}
          color="#F5A623"
          data={{
            main: s?.commands?.pending ?? '--',
            sub: 'pending & in-flight'
          }}
        />
        <SummaryCard
          testId="summary-events"
          title="Event Throughput"
          icon={Lightning}
          color="#007AFF"
          data={{
            main: s?.events?.total ?? '--',
            sub: 'total canonical events'
          }}
        />
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-12 gap-4" style={{ height: 'calc(100vh - 320px)' }}>
        {/* Device Health Map */}
        <div className="col-span-8 rounded border overflow-hidden flex flex-col" style={{ background: '#12151C', borderColor: '#272E3B' }}>
          <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: '#272E3B' }}>
            <h2 className="font-heading text-base font-semibold" style={{ color: '#E8ECF1' }}>Device Health Map</h2>
            <div className="flex items-center gap-4 text-xs" style={{ color: '#6B7A90' }}>
              <span className="flex items-center gap-1"><SealCheck size={14} style={{ color: '#00D4AA' }} /> Online</span>
              <span className="flex items-center gap-1"><WifiX size={14} style={{ color: '#FF3B30' }} /> Offline</span>
              <span className="flex items-center gap-1"><XCircle size={14} style={{ color: '#FF3B30' }} /> Error</span>
              <span className="flex items-center gap-1"><Wrench size={14} style={{ color: '#F5A623' }} /> Maint.</span>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-3">
            <div className="grid grid-cols-8 gap-2" data-testid="device-health-grid">
              {devices.map(d => {
                const colors = { online: '#00D4AA', offline: '#FF3B30', error: '#FF3B30', maintenance: '#F5A623' };
                const bgColors = { online: 'rgba(0,212,170,0.08)', offline: 'rgba(255,59,48,0.08)', error: 'rgba(255,59,48,0.12)', maintenance: 'rgba(245,166,35,0.08)' };
                return (
                  <button
                    key={d.id}
                    data-testid={`device-badge-${d.external_ref}`}
                    onClick={() => navigate(`/devices?selected=${d.id}`)}
                    className="rounded border p-2 text-center transition-all duration-150 hover:-translate-y-[1px]"
                    style={{ background: bgColors[d.status], borderColor: `${colors[d.status]}30` }}
                    title={`${d.external_ref} - ${d.manufacturer} ${d.model}`}
                  >
                    <div className="font-mono text-[10px] font-semibold truncate" style={{ color: colors[d.status] }}>{d.external_ref}</div>
                    <div className="text-[9px] truncate mt-0.5" style={{ color: '#6B7A90' }}>{d.protocol_family}</div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Live Event Feed */}
        <div className="col-span-4 rounded border overflow-hidden flex flex-col" style={{ background: '#12151C', borderColor: '#272E3B' }}>
          <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: '#272E3B' }}>
            <h2 className="font-heading text-base font-semibold" style={{ color: '#E8ECF1' }}>Live Event Feed</h2>
            <span className="w-2 h-2 rounded-full pulse-online" style={{ background: '#00D4AA' }} />
          </div>
          <div className="flex-1 overflow-y-auto" data-testid="live-event-feed">
            {events.map((evt, i) => (
              <div
                key={evt.id}
                className={`px-4 py-2 border-b text-xs transition-colors hover:bg-white/[0.02] ${i === 0 ? 'animate-slide-in' : ''}`}
                style={{ borderColor: '#272E3B20' }}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-mono" style={{ color: '#A3AEBE' }}>
                    {new Date(evt.occurred_at).toLocaleTimeString()}
                  </span>
                  <SeverityBadge severity={evt.severity} />
                </div>
                <div className="font-mono font-medium" style={{ color: '#E8ECF1' }}>{evt.event_type}</div>
                <div className="mt-0.5 truncate" style={{ color: '#6B7A90' }}>
                  {devices.find(d => d.id === evt.device_id)?.external_ref || evt.device_id?.slice(0, 8)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Alert Ticker */}
      {alerts.length > 0 && (
        <div className="rounded border overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="alert-ticker">
          <Marquee speed={40} gradient={false} pauseOnHover>
            {alerts.map(a => {
              const colors = { critical: '#FF3B30', warning: '#F5A623', info: '#007AFF' };
              return (
                <span
                  key={a.id}
                  className="inline-flex items-center gap-2 px-6 py-2 font-mono text-xs cursor-pointer"
                  onClick={() => navigate('/alerts')}
                  style={{ color: colors[a.severity] }}
                >
                  <span className="w-1.5 h-1.5 rounded-full" style={{ background: colors[a.severity] }} />
                  {a.message}
                </span>
              );
            })}
          </Marquee>
        </div>
      )}
    </div>
  );
}
