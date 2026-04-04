import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { ShieldCheck, Play, Stop, ArrowRight, ArrowLeft, Funnel, Warning } from '@phosphor-icons/react';

export default function ProxyControlPage() {
  const [instances, setInstances] = useState([]);
  const [targetHost, setTargetHost] = useState('cms.casino.com');
  const [listenPort, setListenPort] = useState(8443);
  const [filters, setFilters] = useState([]);
  const [interceptResult, setInterceptResult] = useState(null);
  const [newFilter, setNewFilter] = useState({ id: '', commandName: '', action: 'DROP', direction: 'EGM_TO_HOST' });

  useEffect(() => { api.get('/proxy/instances').then(r => setInstances(r.data.instances || [])).catch(() => {}); }, []);

  const startProxy = async () => {
    const { data } = await api.post('/proxy/start', { listen_port: listenPort, target_host: targetHost, disruptive_filters: filters });
    setInstances(prev => [...prev, data]);
  };

  const stopProxy = async (id) => {
    await api.post(`/proxy/${id}/stop`);
    setInstances(prev => prev.filter(p => p.id !== id));
  };

  const addFilter = () => {
    if (newFilter.id) setFilters(prev => [...prev, { ...newFilter, type: 'AUTOMATIC' }]);
    setNewFilter({ id: '', commandName: '', action: 'DROP', direction: 'EGM_TO_HOST' });
  };

  const testIntercept = async (proxyId) => {
    const { data } = await api.post(`/proxy/${proxyId}/intercept`, { direction: 'EGM_TO_HOST', command_class: 'G2S_cabinet', command_name: 'getDeviceStatus', xml: '<g2s:getDeviceStatus deviceId="G2S_EGM001"/>' });
    setInterceptResult(data);
  };

  return (
    <div data-testid="proxy-control" className="space-y-4">
      <h1 className="font-heading text-2xl font-bold flex items-center gap-3" style={{ color: '#F0F4FF' }}>
        <ShieldCheck size={24} style={{ color: '#8B5CF6' }} /> Proxy Mode — Transparent MITM
      </h1>

      {/* Config */}
      <div className="rounded-lg border p-4 space-y-3" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
        <div className="grid grid-cols-3 gap-3">
          <div><label className="block text-[9px] uppercase tracking-wider mb-1" style={{ color: '#4A6080' }}>Target Host</label><input value={targetHost} onChange={e => setTargetHost(e.target.value)} className="w-full px-3 py-2 rounded text-xs font-mono outline-none" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} /></div>
          <div><label className="block text-[9px] uppercase tracking-wider mb-1" style={{ color: '#4A6080' }}>Listen Port</label><input type="number" value={listenPort} onChange={e => setListenPort(+e.target.value)} className="w-full px-3 py-2 rounded text-xs font-mono outline-none" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} /></div>
          <div className="flex items-end"><button data-testid="start-proxy-btn" onClick={startProxy} className="w-full py-2 rounded text-xs font-semibold" style={{ background: '#8B5CF6', color: '#F0F4FF' }}><Play size={14} className="inline mr-1" /> Start Proxy</button></div>
        </div>

        {/* Filters */}
        <div className="text-[10px] uppercase tracking-wider font-medium" style={{ color: '#4A6080' }}>Disruptive Filters</div>
        <div className="flex gap-2">
          <input value={newFilter.id} onChange={e => setNewFilter(p => ({ ...p, id: e.target.value }))} placeholder="Filter ID" className="px-2 py-1.5 rounded text-xs font-mono outline-none" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} />
          <input value={newFilter.commandName} onChange={e => setNewFilter(p => ({ ...p, commandName: e.target.value }))} placeholder="Command name" className="px-2 py-1.5 rounded text-xs font-mono outline-none" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} />
          <select value={newFilter.action} onChange={e => setNewFilter(p => ({ ...p, action: e.target.value }))} className="px-2 py-1.5 rounded text-xs outline-none" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }}>
            {['DROP', 'DELAY', 'CORRUPT', 'DUPLICATE'].map(a => <option key={a}>{a}</option>)}
          </select>
          <button onClick={addFilter} className="px-3 py-1.5 rounded text-xs" style={{ background: '#1A2540', color: '#F0F4FF' }}>Add</button>
        </div>
        {filters.map((f, i) => (
          <div key={i} className="flex items-center gap-2 px-3 py-1.5 rounded text-[10px] font-mono" style={{ background: '#111827' }}>
            <Funnel size={12} style={{ color: '#8B5CF6' }} /> <span style={{ color: '#F0F4FF' }}>{f.id}</span>
            <span style={{ color: '#FFB800' }}>{f.commandName || '*'}</span> <ArrowRight size={10} style={{ color: '#4A6080' }} />
            <span style={{ color: f.action === 'DROP' ? '#FF3B3B' : '#FFB800' }}>{f.action}</span>
          </div>
        ))}
      </div>

      {/* Active Instances */}
      {instances.map(p => (
        <div key={p.id} className="rounded-lg border p-4" style={{ background: '#0C1322', borderColor: p.status === 'RUNNING' ? '#8B5CF630' : '#1A2540' }}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <span className={`w-3 h-3 rounded-full ${p.status === 'RUNNING' ? 'pulse-online' : ''}`} style={{ background: p.status === 'RUNNING' ? '#00D97E' : '#4A6080' }} />
              <span className="font-mono text-sm font-semibold" style={{ color: '#F0F4FF' }}>{p.id}</span>
              <span className="text-[10px] font-mono" style={{ color: '#4A6080' }}>:{p.listen_port} → {p.target_host}:{p.target_port}</span>
            </div>
            <div className="flex gap-2">
              <button onClick={() => testIntercept(p.id)} className="px-3 py-1 rounded text-[10px] font-mono" style={{ background: '#1A2540', color: '#00B4D8' }}>Test Intercept</button>
              <button onClick={() => stopProxy(p.id)} className="px-3 py-1 rounded text-[10px] font-mono" style={{ background: 'rgba(255,59,59,0.1)', color: '#FF3B3B' }}><Stop size={10} className="inline mr-1" /> Stop</button>
            </div>
          </div>
          <div className="grid grid-cols-4 gap-3 text-xs font-mono">
            <div style={{ color: '#4A6080' }}>Captured: <span style={{ color: '#F0F4FF' }}>{p.messages_captured}</span></div>
            <div style={{ color: '#4A6080' }}>Forwarded: <span style={{ color: '#00D97E' }}>{p.messages_forwarded}</span></div>
            <div style={{ color: '#4A6080' }}>Dropped: <span style={{ color: '#FF3B3B' }}>{p.messages_dropped}</span></div>
            <div style={{ color: '#4A6080' }}>Schema Violations: <span style={{ color: '#FFB800' }}>{p.schema_violations}</span></div>
          </div>
        </div>
      ))}

      {interceptResult && (
        <div className="rounded-lg border p-3 text-xs font-mono" style={{ background: '#111827', borderColor: '#1A2540' }}>
          <span style={{ color: '#4A6080' }}>Intercept: </span>
          <span style={{ color: interceptResult.action === 'FORWARD' ? '#00D97E' : '#FF3B3B' }}>{interceptResult.action}</span>
          <span style={{ color: '#4A6080' }}> | Schema: </span><span style={{ color: interceptResult.schema_valid ? '#00D97E' : '#FF3B3B' }}>{interceptResult.schema_valid ? 'Valid' : 'Invalid'}</span>
          <span style={{ color: '#4A6080' }}> | Channels: PROTO={interceptResult.channels?.protocol_trace} SOAP={interceptResult.channels?.soap} G2S={interceptResult.channels?.g2s}</span>
        </div>
      )}
    </div>
  );
}
