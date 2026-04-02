import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Bell, Check, X, Warning } from '@phosphor-icons/react';

export default function AlertConsolePage() {
  const [alerts, setAlerts] = useState([]);
  const [total, setTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');

  const fetchAlerts = async () => {
    const params = new URLSearchParams();
    if (statusFilter) params.set('status', statusFilter);
    if (severityFilter) params.set('severity', severityFilter);
    params.set('limit', '100');
    const { data } = await api.get(`/alerts?${params}`);
    setAlerts(data.alerts || []);
    setTotal(data.total || 0);
  };

  useEffect(() => { fetchAlerts(); }, [statusFilter, severityFilter]);

  const acknowledge = async (id) => {
    await api.post(`/alerts/${id}/acknowledge`);
    fetchAlerts();
  };

  const resolve = async (id) => {
    await api.post(`/alerts/${id}/resolve`);
    fetchAlerts();
  };

  const sevColors = { critical: '#FF3B30', warning: '#F5A623', info: '#007AFF' };
  const statusColors = { active: '#FF3B30', acknowledged: '#F5A623', resolved: '#00D4AA' };

  return (
    <div data-testid="alert-console" className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-2xl font-bold tracking-tight flex items-center gap-3" style={{ color: '#E8ECF1' }}>
          <Bell size={24} style={{ color: '#FF3B30' }} /> Alert Console
        </h1>
        <span className="text-xs font-mono" style={{ color: '#6B7A90' }}>{total} alerts</span>
      </div>

      <div className="flex gap-3">
        <select data-testid="alert-status-filter" value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="px-3 py-1.5 rounded text-xs outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}>
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="resolved">Resolved</option>
        </select>
        <select data-testid="alert-severity-filter" value={severityFilter} onChange={e => setSeverityFilter(e.target.value)} className="px-3 py-1.5 rounded text-xs outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}>
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="warning">Warning</option>
          <option value="info">Info</option>
        </select>
      </div>

      <div className="space-y-2">
        {alerts.map(a => (
          <div
            key={a.id}
            data-testid={`alert-row-${a.id}`}
            className="rounded border px-4 py-3 flex items-center gap-4 transition-colors"
            style={{
              background: '#12151C',
              borderColor: `${sevColors[a.severity]}30`,
              borderLeftWidth: 3,
              borderLeftColor: sevColors[a.severity],
            }}
          >
            <Warning size={18} style={{ color: sevColors[a.severity] }} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-medium" style={{ color: '#E8ECF1' }}>{a.device_ref}</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded" style={{ background: `${sevColors[a.severity]}20`, color: sevColors[a.severity] }}>{a.severity}</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded capitalize" style={{ background: `${statusColors[a.status]}20`, color: statusColors[a.status] }}>{a.status}</span>
              </div>
              <div className="text-sm mt-0.5" style={{ color: '#A3AEBE' }}>{a.message}</div>
              <div className="text-[10px] font-mono mt-1" style={{ color: '#6B7A90' }}>{new Date(a.created_at).toLocaleString()}</div>
            </div>
            <div className="flex gap-2 flex-shrink-0">
              {a.status === 'active' && (
                <button data-testid={`ack-alert-${a.id}`} onClick={() => acknowledge(a.id)} className="px-3 py-1.5 rounded text-xs font-medium" style={{ background: 'rgba(245,166,35,0.1)', color: '#F5A623' }}>
                  Acknowledge
                </button>
              )}
              {(a.status === 'active' || a.status === 'acknowledged') && (
                <button data-testid={`resolve-alert-${a.id}`} onClick={() => resolve(a.id)} className="px-3 py-1.5 rounded text-xs font-medium" style={{ background: 'rgba(0,212,170,0.1)', color: '#00D4AA' }}>
                  Resolve
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
