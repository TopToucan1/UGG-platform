import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Users, Play, Stop, Gauge, Lightning, ArrowsClockwise } from '@phosphor-icons/react';

const STATUS_C = { 'Engine Stopped': '#4A6080', 'Engine Loading': '#FFB800', 'Engine Starting': '#FFB800', 'Engine Running': '#00D97E', 'Scripts Starting': '#00B4D8', 'Scripts Running': '#00B4D8', 'Scripts Stopping': '#FFB800', 'Engine Stopping': '#FFB800' };

export default function FleetDashboardPage() {
  const [runners, setRunners] = useState([]);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [name, setName] = useState('');
  const [targetUrl, setTargetUrl] = useState('');
  const [maxEgms, setMaxEgms] = useState(50);

  useEffect(() => { api.get('/fleet/runners').then(r => setRunners(r.data.runners || [])).catch(() => {}); }, []);

  const createFleet = async () => {
    const { data } = await api.post('/fleet/create', { name: name || 'Fleet Run', target_host_url: targetUrl, max_egms: maxEgms });
    setRunners(prev => [data, ...prev]);
    setSelected(data);
  };

  const controlEngine = async (id, action) => {
    const { data } = await api.post(`/fleet/${id}/engine`, { action });
    refreshDetail(id);
  };

  const controlScripts = async (id, action) => {
    const { data } = await api.post(`/fleet/${id}/scripts`, { action });
    refreshDetail(id);
  };

  const resetMetrics = async (id) => {
    await api.post(`/fleet/${id}/metrics`, { reset: true });
    refreshDetail(id);
  };

  const refreshDetail = async (id) => {
    const { data } = await api.get(`/fleet/${id}/engine`);
    setDetail(data);
  };

  const selectRunner = (r) => {
    setSelected(r);
    refreshDetail(r.id);
  };

  return (
    <div data-testid="fleet-dashboard" className="space-y-4">
      <h1 className="font-heading text-2xl font-bold flex items-center gap-3" style={{ color: '#F0F4FF' }}>
        <Users size={24} style={{ color: '#EC4899' }} /> Fleet Simulator
      </h1>

      {/* Create Fleet */}
      <div className="rounded-lg border p-4" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
        <div className="grid grid-cols-4 gap-3">
          <div><label className="block text-[9px] uppercase tracking-wider mb-1" style={{ color: '#4A6080' }}>Fleet Name</label><input value={name} onChange={e => setName(e.target.value)} placeholder="Load Test Alpha" className="w-full px-3 py-2 rounded text-xs outline-none" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} /></div>
          <div><label className="block text-[9px] uppercase tracking-wider mb-1" style={{ color: '#4A6080' }}>Target Host</label><input value={targetUrl} onChange={e => setTargetUrl(e.target.value)} placeholder="https://cms.casino.com" className="w-full px-3 py-2 rounded text-xs outline-none font-mono" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} /></div>
          <div><label className="block text-[9px] uppercase tracking-wider mb-1" style={{ color: '#4A6080' }}>Max EGMs (max 200)</label><input type="number" min={1} max={200} value={maxEgms} onChange={e => setMaxEgms(+e.target.value)} className="w-full px-3 py-2 rounded text-xs outline-none font-mono" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} /></div>
          <div className="flex items-end"><button data-testid="create-fleet-btn" onClick={createFleet} className="w-full py-2 rounded text-xs font-semibold" style={{ background: '#EC4899', color: '#F0F4FF' }}>Create Fleet</button></div>
        </div>
      </div>

      {/* Fleet List + Detail */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-4 space-y-2" data-testid="fleet-list">
          {runners.map(r => (
            <button key={r.id} onClick={() => selectRunner(r)} className="w-full text-left rounded-lg border p-3 transition-colors" style={{ background: selected?.id === r.id ? 'rgba(236,72,153,0.05)' : '#0C1322', borderColor: selected?.id === r.id ? '#EC489940' : '#1A2540' }}>
              <div className="flex items-center gap-2 mb-1">
                <span className="w-2.5 h-2.5 rounded-full" style={{ background: STATUS_C[r.status] || '#4A6080' }} />
                <span className="text-xs font-semibold" style={{ color: '#F0F4FF' }}>{r.name}</span>
              </div>
              <div className="text-[10px] font-mono" style={{ color: '#4A6080' }}>{r.max_egms} slots | {r.status}</div>
            </button>
          ))}
        </div>

        {detail && (
          <div className="col-span-8 rounded-lg border p-5 space-y-4" style={{ background: '#0C1322', borderColor: '#1A2540' }} data-testid="fleet-detail">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-heading text-lg font-semibold" style={{ color: '#F0F4FF' }}>{selected?.name}</div>
                <div className="text-xs font-mono mt-0.5" style={{ color: STATUS_C[detail.status] }}>{detail.status}</div>
              </div>
              <div className="flex gap-2">
                {detail.status === 'Engine Stopped' && <button onClick={() => controlEngine(selected.id, 'start')} className="flex items-center gap-1 px-4 py-2 rounded text-xs font-semibold" style={{ background: '#00D97E', color: '#070B14' }}><Play size={14} /> Start Engine</button>}
                {detail.status === 'Engine Running' && <button onClick={() => controlScripts(selected.id, 'start')} className="flex items-center gap-1 px-4 py-2 rounded text-xs font-semibold" style={{ background: '#00B4D8', color: '#070B14' }}><Lightning size={14} /> Start Scripts</button>}
                {detail.status === 'Scripts Running' && <button onClick={() => controlScripts(selected.id, 'stop')} className="flex items-center gap-1 px-4 py-2 rounded text-xs font-semibold" style={{ background: '#FFB800', color: '#070B14' }}><Stop size={14} /> Stop Scripts</button>}
                {detail.status !== 'Engine Stopped' && <button onClick={() => controlEngine(selected.id, 'stop')} className="flex items-center gap-1 px-3 py-2 rounded text-xs" style={{ background: 'rgba(255,59,59,0.1)', color: '#FF3B3B' }}><Stop size={14} /> Stop</button>}
                <button onClick={() => resetMetrics(selected.id)} className="flex items-center gap-1 px-3 py-2 rounded text-xs" style={{ background: '#1A2540', color: '#4A6080' }}><ArrowsClockwise size={14} /> Reset</button>
              </div>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-4 gap-3">
              {[
                { label: 'EGMs Connected', value: detail.metrics?.egms_connected || 0, color: '#00D97E' },
                { label: 'EGMs Running', value: detail.metrics?.egms_running || 0, color: '#00B4D8' },
                { label: 'Msgs Sent', value: (detail.metrics?.messages_sent || 0).toLocaleString(), color: '#F0F4FF' },
                { label: 'Avg Response', value: `${detail.metrics?.avg_response_ms || 0}ms`, color: '#FFB800' },
              ].map(m => (
                <div key={m.label} className="rounded p-3" style={{ background: '#111827', border: '1px solid #1A2540' }}>
                  <div className="text-[9px] uppercase tracking-wider" style={{ color: '#4A6080' }}>{m.label}</div>
                  <div className="font-mono text-xl font-bold" style={{ color: m.color }}>{m.value}</div>
                </div>
              ))}
            </div>

            {/* Slot Summary */}
            <div className="flex items-center gap-4 text-xs font-mono">
              <span style={{ color: '#4A6080' }}>Slots: {detail.slot_count}</span>
              <span style={{ color: '#4A6080' }}>Idle: {detail.slots_summary?.idle}</span>
              <span style={{ color: '#00D97E' }}>Connected: {detail.slots_summary?.connected}</span>
              <span style={{ color: '#00B4D8' }}>Running: {detail.slots_summary?.running}</span>
              <span style={{ color: '#4A6080' }}>Errors: {detail.metrics?.errors_total || 0}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
