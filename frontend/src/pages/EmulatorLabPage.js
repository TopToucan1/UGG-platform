import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import { Flask, Play, Stop, Check, X, Clock, Plugs, Terminal, Code, Hexagon, ArrowRight, ArrowLeft, Power } from '@phosphor-icons/react';

const STATE_C = { ONLINE: '#00D97E', SYNC: '#FFB800', OPENING: '#FFB800', CLOSING: '#FFB800', LOST: '#FF3B3B', CLOSED: '#4A6080' };
const PROTO_C = { SAS: '#00B4D8', G2S: '#00D97E', S2S: '#8B5CF6', VENDOR: '#FFB800', REST: '#FFB800', PROPRIETARY: '#FFB800' };

function SeverityDot({ severity }) {
  const c = { critical: '#FF3B3B', warning: '#FFB800', info: '#00B4D8' };
  return <span className="w-1.5 h-1.5 rounded-full inline-block" style={{ background: c[severity] || '#4A6080' }} />;
}

export default function EmulatorLabPage() {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState(null);
  const [runResult, setRunResult] = useState(null);
  const [running, setRunning] = useState(false);
  const [pastRuns, setPastRuns] = useState([]);
  // Adapter state
  const [adapters, setAdapters] = useState([]);
  const [traces, setTraces] = useState([]);
  const [traceTab, setTraceTab] = useState('g2s');
  const [traceChannels, setTraceChannels] = useState({ channels: [], protocols: [] });
  const [connectForm, setConnectForm] = useState({ protocol: 'SAS', device_id: '', config: {} });
  const [showConnect, setShowConnect] = useState(false);

  useEffect(() => {
    api.get('/emulator/scenarios').then(r => setScenarios(r.data.scenarios || []));
    api.get('/emulator/runs?limit=10').then(r => setPastRuns(r.data.runs || []));
    fetchAdapters();
  }, []);

  const fetchAdapters = async () => {
    const [aRes, tRes, cRes] = await Promise.all([
      api.get('/adapters'),
      api.get('/adapters/traces?limit=100'),
      api.get('/adapters/traces/channels'),
    ]);
    setAdapters(aRes.data.adapters || []);
    setTraces(tRes.data.traces || []);
    setTraceChannels(cRes.data);
  };

  // Poll adapter status every 5s
  useEffect(() => {
    const iv = setInterval(fetchAdapters, 5000);
    return () => clearInterval(iv);
  }, []);

  const runScenario = async () => {
    if (!selectedScenario || running) return;
    setRunning(true); setRunResult(null);
    try {
      const { data } = await api.post('/emulator/run', { scenario_id: selectedScenario.id });
      setRunResult(data); setPastRuns(prev => [data, ...prev].slice(0, 10));
    } catch (err) { console.error(err); }
    setRunning(false);
  };

  const connectAdapter = async () => {
    try {
      await api.post('/adapters/connect', { protocol: connectForm.protocol, device_id: connectForm.device_id || undefined, config: connectForm.config });
      fetchAdapters();
      setShowConnect(false);
    } catch (err) { console.error(err); }
  };

  const disconnectAdapter = async (id) => {
    await api.post(`/adapters/${encodeURIComponent(id)}/disconnect`);
    fetchAdapters();
  };

  // Filter traces by tab
  const filteredTraces = traces.filter(t => {
    if (traceTab === 'g2s') return t.channel === 'g2s';
    if (traceTab === 'soap') return t.channel === 'soap';
    if (traceTab === 'protocol') return t.channel === 'protocol';
    return true;
  });

  return (
    <div data-testid="emulator-lab" className="flex flex-col h-full -m-6">
      {/* Scenario Ribbon */}
      <div className="flex items-center gap-4 px-6 py-3 border-b flex-shrink-0" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
        <Flask size={20} style={{ color: '#00B4D8' }} />
        <select data-testid="scenario-selector" value={selectedScenario?.id || ''} onChange={e => setSelectedScenario(scenarios.find(s => s.id === e.target.value))}
          className="px-3 py-2 rounded text-sm outline-none min-w-64" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }}>
          <option value="">Select Scenario...</option>
          {scenarios.map(s => <option key={s.id} value={s.id}>{s.name} ({s.protocol})</option>)}
        </select>
        <button data-testid="run-scenario-btn" onClick={runScenario} disabled={!selectedScenario || running}
          className="flex items-center gap-2 px-4 py-2 rounded text-sm font-medium disabled:opacity-50" style={{ background: '#00D97E', color: '#070B14' }}>
          {running ? <Clock size={16} className="animate-spin" /> : <Play size={16} weight="fill" />} {running ? 'Running...' : 'Run'}
        </button>
        <button data-testid="connect-adapter-btn" onClick={() => setShowConnect(!showConnect)}
          className="ml-auto flex items-center gap-2 px-3 py-2 rounded text-xs font-medium" style={{ background: 'rgba(0,180,216,0.1)', color: '#00B4D8', border: '1px solid rgba(0,180,216,0.2)' }}>
          <Plugs size={14} /> Connect Adapter
        </button>
      </div>

      {/* Connect Adapter Form */}
      {showConnect && (
        <div className="px-6 py-3 border-b flex items-center gap-3" style={{ borderColor: '#1A2540', background: '#111827' }}>
          <select value={connectForm.protocol} onChange={e => setConnectForm(p => ({ ...p, protocol: e.target.value }))}
            className="px-3 py-2 rounded text-xs outline-none" style={{ background: '#1A2540', border: '1px solid #1F2E4A', color: '#F0F4FF' }}>
            <option value="SAS">SAS (Serial)</option><option value="G2S">G2S (SOAP)</option><option value="S2S">S2S (System)</option>
          </select>
          <input value={connectForm.device_id} onChange={e => setConnectForm(p => ({ ...p, device_id: e.target.value }))} placeholder="Device ID (auto)"
            className="px-3 py-2 rounded text-xs outline-none w-40" style={{ background: '#1A2540', border: '1px solid #1F2E4A', color: '#F0F4FF' }} />
          <button onClick={connectAdapter} className="px-4 py-2 rounded text-xs font-medium" style={{ background: '#00D97E', color: '#070B14' }}>
            <Power size={14} className="inline mr-1" /> Connect
          </button>
          <button onClick={() => setShowConnect(false)} className="text-xs" style={{ color: '#4A6080' }}>Cancel</button>
        </div>
      )}

      {/* Three-Pane Body */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left — Virtual Devices + Connected Adapters */}
        <div className="w-64 border-r flex-shrink-0 overflow-y-auto" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
          {/* Connected Adapters (Connector Status Panel) */}
          <div className="border-b" style={{ borderColor: '#1A2540' }}>
            <div className="px-4 py-2 text-[10px] uppercase tracking-wider font-medium flex items-center gap-2" style={{ color: '#4A6080' }}>
              <Plugs size={12} /> Connected Adapters ({adapters.length})
            </div>
            {adapters.map(a => (
              <div key={a.adapter_id} data-testid={`adapter-row-${a.adapter_id}`} className="px-4 py-2 border-b flex items-center gap-2" style={{ borderColor: '#1A254020' }}>
                <span className="w-2 h-2 rounded-full" style={{ background: STATE_C[a.state] || '#4A6080', boxShadow: a.state === 'ONLINE' ? `0 0 6px ${STATE_C.ONLINE}` : a.state === 'LOST' ? `0 0 6px ${STATE_C.LOST}` : 'none' }} />
                <span className="text-[10px] font-mono px-1 py-0.5 rounded" style={{ background: `${PROTO_C[a.protocol] || '#4A6080'}20`, color: PROTO_C[a.protocol] || '#4A6080' }}>{a.protocol}</span>
                <span className="text-[10px] font-mono flex-1 truncate" style={{ color: '#F0F4FF' }}>{a.device_id}</span>
                <button onClick={() => disconnectAdapter(a.adapter_id)} className="text-[9px]" style={{ color: '#FF3B3B' }}>
                  <X size={10} />
                </button>
              </div>
            ))}
            {adapters.length === 0 && <div className="px-4 py-3 text-[10px] text-center" style={{ color: '#4A6080' }}>No adapters connected</div>}
          </div>

          {/* Virtual Devices from scenario run */}
          <div className="px-4 py-2 text-[10px] uppercase tracking-wider font-medium" style={{ color: '#4A6080' }}>Virtual Devices</div>
          {runResult?.virtual_devices?.map(dev => (
            <div key={dev.id} className="px-4 py-2.5 border-b" style={{ borderColor: '#1A254020' }}>
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-medium" style={{ color: '#F0F4FF' }}>{dev.ref}</span>
                <span className="w-2 h-2 rounded-full" style={{ background: dev.status === 'running' ? '#00D97E' : '#4A6080', boxShadow: dev.status === 'running' ? '0 0 6px rgba(0,217,126,0.4)' : 'none' }} />
              </div>
              <div className="text-[10px] font-mono mt-0.5" style={{ color: '#4A6080' }}>{dev.protocol} | {dev.id.slice(0, 12)}</div>
            </div>
          )) || <div className="px-4 py-3 text-[10px] text-center" style={{ color: '#4A6080' }}>Run a scenario</div>}
        </div>

        {/* Center — Trace Stream */}
        <div className="flex-1 flex flex-col overflow-hidden" style={{ background: '#070B14' }}>
          <div className="flex items-center border-b" style={{ borderColor: '#1A2540', background: '#0C1322' }}>
            <div className="px-4 py-2 text-[10px] uppercase tracking-wider font-medium" style={{ color: '#4A6080' }}>Trace Stream</div>
            {/* 3-tab Protocol Trace selector */}
            <div className="flex ml-auto">
              {[
                { id: 'g2s', label: 'G2S Messages', icon: Terminal },
                { id: 'soap', label: 'SOAP Transport', icon: Code },
                { id: 'protocol', label: 'Protocol Trace', icon: Flask },
              ].map(tab => (
                <button key={tab.id} data-testid={`trace-tab-${tab.id}`} onClick={() => setTraceTab(tab.id)}
                  className="flex items-center gap-1 px-3 py-2 text-[10px] font-medium uppercase tracking-wider transition-colors"
                  style={{ color: traceTab === tab.id ? '#00B4D8' : '#4A6080', borderBottom: traceTab === tab.id ? '2px solid #00B4D8' : '2px solid transparent' }}>
                  <tab.icon size={12} /> {tab.label}
                </button>
              ))}
            </div>
          </div>
          <div className="flex-1 overflow-y-auto" data-testid="trace-stream">
            {/* Scenario traces */}
            {runResult?.trace_events?.map((evt, i) => (
              <div key={evt.id} className="px-4 py-1.5 border-b text-xs font-mono flex items-center gap-3 hover:bg-white/[0.02]" style={{ borderColor: '#1A254010' }}>
                <span style={{ color: '#4A6080' }}>{new Date(evt.timestamp).toLocaleTimeString()}</span>
                <SeverityDot severity={evt.severity} />
                <span style={{ color: '#F0F4FF' }}>{evt.event_type}</span>
                <span className="ml-auto" style={{ color: '#4A6080' }}>{evt.device_ref}</span>
              </div>
            ))}
            {/* Adapter traces with hex/xml */}
            {filteredTraces.map((t, i) => (
              <div key={t.id || i} className="px-4 py-1.5 border-b text-[11px] font-mono hover:bg-white/[0.02]" style={{ borderColor: '#1A254010' }}>
                <div className="flex items-center gap-2">
                  <span style={{ color: '#4A6080' }}>{t.timestamp ? new Date(t.timestamp).toLocaleTimeString() : ''}</span>
                  {t.direction === 'out' ? <ArrowRight size={10} style={{ color: '#00B4D8' }} /> : <ArrowLeft size={10} style={{ color: '#00D97E' }} />}
                  <span className="text-[9px] px-1 rounded" style={{ background: `${PROTO_C[t.protocol] || '#4A6080'}20`, color: PROTO_C[t.protocol] || '#4A6080' }}>{t.protocol}</span>
                  {t.command && <span style={{ color: '#F0F4FF' }}>{t.command}</span>}
                  {t.class && <span style={{ color: '#8BA3CC' }}>{t.class}</span>}
                  {t.annotation && <span style={{ color: '#8BA3CC' }}>{t.annotation}</span>}
                </div>
                {/* Raw hex for SAS Protocol Trace */}
                {traceTab === 'protocol' && t.hex && (
                  <div className="mt-1 px-2 py-1 rounded text-[10px]" style={{ background: '#111827' }}>
                    <span style={{ color: '#00B4D8' }}>HEX: </span>
                    <span style={{ color: '#00D97E' }}>{t.hex.match(/.{1,2}/g)?.join(' ') || t.hex}</span>
                    <span style={{ color: '#4A6080' }}> | ASCII: </span>
                    <span style={{ color: '#FFB800' }}>{t.hex.match(/.{1,2}/g)?.map(h => { const c = parseInt(h, 16); return c >= 32 && c < 127 ? String.fromCharCode(c) : '.'; }).join('') || ''}</span>
                  </div>
                )}
                {/* Raw XML for SOAP/G2S */}
                {(traceTab === 'soap' || traceTab === 'g2s') && t.xml && (
                  <div className="mt-1 px-2 py-1 rounded text-[10px] overflow-x-auto" style={{ background: '#111827' }}>
                    <span style={{ color: '#00D97E' }}>{t.xml}</span>
                  </div>
                )}
              </div>
            ))}
            {filteredTraces.length === 0 && !runResult && (
              <div className="flex items-center justify-center h-full text-xs" style={{ color: '#4A6080' }}>
                <div className="text-center">
                  <Flask size={32} className="mx-auto mb-2" />
                  Connect an adapter or run a scenario to see trace data
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right — Assertions / Adapter Details */}
        <div className="w-80 border-l flex-shrink-0 overflow-y-auto" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
          <div className="px-4 py-2 text-[10px] uppercase tracking-wider font-medium" style={{ color: '#4A6080' }}>Assertions</div>
          {runResult?.assertions?.map(a => (
            <div key={a.id} className="px-4 py-3 border-b" style={{ borderColor: '#1A254020' }}>
              <div className="flex items-start gap-2">
                {a.passed ? <Check size={16} className="flex-shrink-0 mt-0.5" style={{ color: '#00D97E' }} /> : <X size={16} className="flex-shrink-0 mt-0.5" style={{ color: '#FF3B3B' }} />}
                <div>
                  <div className="text-xs" style={{ color: '#F0F4FF' }}>{a.description}</div>
                  <div className="text-[10px] font-mono mt-0.5" style={{ color: '#4A6080' }}>Expected: {String(a.expected)} | Actual: {String(a.actual)}</div>
                </div>
              </div>
            </div>
          )) || <div className="px-4 py-3 text-[10px] text-center" style={{ color: '#4A6080' }}>Run a scenario to see assertions</div>}

          {/* Adapter Status Detail */}
          {adapters.length > 0 && (
            <>
              <div className="px-4 py-2 text-[10px] uppercase tracking-wider font-medium border-t" style={{ color: '#4A6080', borderColor: '#1A2540' }}>Adapter Details</div>
              {adapters.map(a => (
                <div key={a.adapter_id} className="px-4 py-2 border-b text-[10px] font-mono" style={{ borderColor: '#1A254020' }}>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="px-1 py-0.5 rounded" style={{ background: `${PROTO_C[a.protocol]}20`, color: PROTO_C[a.protocol] }}>{a.protocol}</span>
                    <span style={{ color: '#F0F4FF' }}>{a.device_id}</span>
                  </div>
                  <div className="space-y-0.5" style={{ color: '#4A6080' }}>
                    <div>State: <span style={{ color: STATE_C[a.state] }}>{a.state}</span></div>
                    {a.poll_count !== undefined && <div>Polls: {a.poll_count} | Errors: {a.error_count}</div>}
                    {a.message_count !== undefined && <div>Messages: {a.message_count}</div>}
                    {a.schema_version && <div>Schema: {a.schema_version}</div>}
                    {a.edge_id && <div>Edge: {a.edge_id} | Devices: {a.managed_devices}</div>}
                    {a.last_event_at && <div>Last: {new Date(a.last_event_at).toLocaleTimeString()}</div>}
                  </div>
                </div>
              ))}
            </>
          )}

          {/* Past Runs */}
          {pastRuns.length > 0 && (
            <>
              <div className="px-4 py-2 text-[10px] uppercase tracking-wider font-medium border-t" style={{ color: '#4A6080', borderColor: '#1A2540' }}>Recent Runs</div>
              {pastRuns.map(r => (
                <div key={r.id} className="px-4 py-2 border-b text-xs" style={{ borderColor: '#1A254020' }}>
                  <div className="flex items-center justify-between">
                    <span style={{ color: '#F0F4FF' }}>{r.scenario_name}</span>
                    <span className="font-mono" style={{ color: r.assertions_passed === r.assertions_total ? '#00D97E' : '#FF3B3B' }}>{r.assertions_passed}/{r.assertions_total}</span>
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
