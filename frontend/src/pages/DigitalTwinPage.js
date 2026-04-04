import { useState, useEffect, useCallback, useRef } from 'react';
import api, { API_URL } from '@/lib/api';
import {
  Cpu, Pulse, ShieldCheck, WifiHigh, CurrencyDollar,
  Lightning, GameController, Warning, ArrowRight, X,
  Heartbeat, CircleNotch, Check, Gauge, Funnel
} from '@phosphor-icons/react';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const HEALTH_C = (h) => h >= 90 ? '#00D97E' : h >= 70 ? '#FFB800' : '#FF3B3B';
const STATE_C = { ONLINE: '#00D97E', OFFLINE: '#4A6080', CLOSED: '#4A6080', SYNC: '#FFB800', LOST: '#FF3B3B', OPENING: '#FFB800', ERROR: '#FF3B3B', MAINTENANCE: '#8B5CF6', UNKNOWN: '#4A6080' };
const COMMS_C = { ONLINE: '#00D97E', SYNC: '#FFB800', CLOSED: '#4A6080', LOST: '#FF3B3B', OPENING: '#FFB800' };
const COLORS = ['#00D97E', '#00B4D8', '#FFB800', '#FF3B3B', '#8B5CF6', '#EC4899', '#06B6D4'];

function Tip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded px-3 py-2 text-xs" style={{ background: '#1A2540', border: '1px solid #1F2E4A' }}>
      <div className="font-mono mb-1" style={{ color: '#F0F4FF' }}>{label}</div>
      {payload.map((p, i) => <div key={i} style={{ color: p.color || '#8BA3CC' }}>{p.name}: {p.value}</div>)}
    </div>
  );
}

function KPI({ label, value, sub, color, icon: Icon }) {
  return (
    <div className="rounded-lg p-4" style={{ background: '#111827', border: '1px solid #1A2540' }}>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[9px] uppercase tracking-widest font-medium" style={{ color: '#4A6080' }}>{label}</span>
        {Icon && <Icon size={16} style={{ color }} />}
      </div>
      <div className="font-mono text-2xl font-black" style={{ color: color || '#F0F4FF' }}>{value}</div>
      {sub && <div className="text-[10px] font-mono mt-1" style={{ color: '#4A6080' }}>{sub}</div>}
    </div>
  );
}

function HealthBar({ score, width = '100%' }) {
  return (
    <div className="h-1.5 rounded-full overflow-hidden" style={{ background: '#1A2540', width }}>
      <div className="h-full rounded-full transition-all duration-500" style={{ width: `${score}%`, background: HEALTH_C(score) }} />
    </div>
  );
}

export default function DigitalTwinPage() {
  const [summary, setSummary] = useState(null);
  const [twins, setTwins] = useState([]);
  const [gateway, setGateway] = useState(null);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [sortBy, setSortBy] = useState('health_score');
  const [wsConnected, setWsConnected] = useState(false);
  const [liveUpdates, setLiveUpdates] = useState(0);
  const wsRef = useRef(null);

  const fetchData = useCallback(async () => {
    try {
      const [sumR, twinR, gwR] = await Promise.all([
        api.get('/digital-twin/fleet/summary'),
        api.get(`/digital-twin/fleet?limit=85&sort_by=${sortBy}${statusFilter ? `&status=${statusFilter}` : ''}`),
        api.get('/digital-twin/gateway'),
      ]);
      setSummary(sumR.data);
      setTwins(twinR.data.twins || []);
      setGateway(gwR.data);
    } catch (err) { console.error(err); }
  }, [sortBy, statusFilter]);

  useEffect(() => { fetchData(); const iv = setInterval(fetchData, 10000); return () => clearInterval(iv); }, [fetchData]);

  // WebSocket for live twin updates
  useEffect(() => {
    const wsUrl = API_URL.replace('https://', 'wss://').replace('http://', 'ws://');
    let ws, reconnect;
    const connect = () => {
      ws = new WebSocket(`${wsUrl}/api/events/ws`);
      wsRef.current = ws;
      ws.onopen = () => setWsConnected(true);
      ws.onmessage = () => setLiveUpdates(p => p + 1);
      ws.onclose = () => { setWsConnected(false); reconnect = setTimeout(connect, 3000); };
      ws.onerror = () => ws.close();
    };
    connect();
    return () => { if (reconnect) clearTimeout(reconnect); if (ws) ws.close(); };
  }, []);

  const selectTwin = async (t) => {
    setSelected(t);
    try {
      const { data } = await api.get(`/digital-twin/device/${t.device_id}`);
      setDetail(data);
    } catch {}
  };

  const s = summary;
  const gw = gateway?.gateway;
  const fmt = (v) => v != null ? `$${Number(v).toLocaleString()}` : '--';

  return (
    <div data-testid="digital-twin-dashboard" className="flex gap-0 h-full -m-6">
      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden" style={{ background: '#070B14' }}>
        {/* Header */}
        <div className="px-6 pt-5 pb-3 flex-shrink-0">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Cpu size={26} style={{ color: '#00B4D8' }} />
              <div>
                <h1 className="font-heading text-2xl font-bold tracking-tight" style={{ color: '#F0F4FF' }}>Digital Twin</h1>
                <span className="text-xs" style={{ color: '#4A6080' }}>Real-time device state projections — Gateway Core Pipeline</span>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5 text-xs font-mono" style={{ color: wsConnected ? '#00D97E' : '#FF3B3B' }}>
                <Pulse size={14} className={wsConnected ? 'animate-pulse' : ''} />
                {wsConnected ? `Live (${liveUpdates})` : 'Reconnecting'}
              </span>
              {gw && (
                <span className="flex items-center gap-1.5 text-[10px] font-mono px-2 py-1 rounded" style={{ background: gw.pipeline?.running ? 'rgba(0,217,126,0.1)' : 'rgba(255,59,59,0.1)', color: gw.pipeline?.running ? '#00D97E' : '#FF3B3B' }}>
                  <CircleNotch size={10} className={gw.pipeline?.running ? 'animate-spin' : ''} />
                  Pipeline: {gw.pipeline?.processed || 0} processed
                </span>
              )}
            </div>
          </div>

          {/* KPI Strip */}
          {s && (
            <div className="grid grid-cols-7 gap-3" data-testid="twin-kpi-strip">
              <KPI label="Fleet" value={s.total_devices} color="#00B4D8" icon={Cpu} sub={`${s.online} online`} />
              <KPI label="Avg Health" value={`${s.avg_health}%`} color={HEALTH_C(s.avg_health)} icon={Heartbeat} />
              <KPI label="Coin In" value={fmt(s.total_coin_in)} color="#00D97E" icon={CurrencyDollar} />
              <KPI label="Credits" value={s.total_credits?.toLocaleString()} color="#FFB800" icon={Lightning} />
              <KPI label="Games" value={s.total_games?.toLocaleString()} color="#00B4D8" icon={GameController} />
              <KPI label="Integrity" value={`${s.integrity_rate}%`} color={s.integrity_rate >= 98 ? '#00D97E' : '#FF3B3B'} icon={ShieldCheck} />
              <KPI label="Comms Lost" value={s.comms_lost} color={s.comms_lost > 0 ? '#FF3B3B' : '#00D97E'} icon={WifiHigh} />
            </div>
          )}
        </div>

        {/* Charts + Pipeline */}
        <div className="px-6 pb-3 flex-shrink-0">
          <div className="grid grid-cols-12 gap-3">
            {/* Health Distribution */}
            <div className="col-span-3 rounded-lg p-3" style={{ background: '#111827', border: '1px solid #1A2540' }} data-testid="health-distribution">
              <div className="text-[9px] uppercase tracking-widest mb-2 font-medium" style={{ color: '#4A6080' }}>Health Distribution</div>
              <ResponsiveContainer width="100%" height={90}>
                <PieChart>
                  <Pie data={s?.health_distribution || []} cx="50%" cy="50%" innerRadius={25} outerRadius={38} dataKey="count" stroke="none">
                    {(s?.health_distribution || []).map((d, i) => <Cell key={i} fill={d.color} />)}
                  </Pie>
                  <Tooltip content={<Tip />} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-1 mt-1">
                {(s?.health_distribution || []).map(d => (
                  <div key={d.label} className="flex items-center justify-between text-[10px] font-mono">
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{ background: d.color }} /><span style={{ color: '#8BA3CC' }}>{d.label}</span></span>
                    <span style={{ color: '#F0F4FF' }}>{d.count}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Comms State */}
            <div className="col-span-3 rounded-lg p-3" style={{ background: '#111827', border: '1px solid #1A2540' }} data-testid="comms-distribution">
              <div className="text-[9px] uppercase tracking-widest mb-2 font-medium" style={{ color: '#4A6080' }}>Comms State</div>
              <ResponsiveContainer width="100%" height={90}>
                <BarChart data={s?.comms_distribution || []} barSize={18}>
                  <XAxis dataKey="state" tick={{ fill: '#4A6080', fontSize: 9 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#4A6080', fontSize: 9 }} axisLine={false} tickLine={false} width={25} />
                  <Tooltip content={<Tip />} />
                  <Bar dataKey="count" name="Devices" radius={[3, 3, 0, 0]}>
                    {(s?.comms_distribution || []).map((d, i) => <Cell key={i} fill={COMMS_C[d.state] || '#4A6080'} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Protocol Mix */}
            <div className="col-span-3 rounded-lg p-3" style={{ background: '#111827', border: '1px solid #1A2540' }} data-testid="protocol-distribution">
              <div className="text-[9px] uppercase tracking-widest mb-2 font-medium" style={{ color: '#4A6080' }}>Protocol Mix</div>
              <div className="space-y-2 mt-1">
                {(s?.protocol_distribution || []).map((p, i) => (
                  <div key={p.protocol} className="flex items-center gap-2">
                    <span className="text-[10px] font-mono w-12 uppercase" style={{ color: COLORS[i % COLORS.length] }}>{p.protocol}</span>
                    <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: '#1A2540' }}>
                      <div className="h-full rounded-full" style={{ width: `${(p.count / (s?.total_devices || 1)) * 100}%`, background: COLORS[i % COLORS.length] }} />
                    </div>
                    <span className="text-[10px] font-mono w-8 text-right" style={{ color: '#F0F4FF' }}>{p.count}</span>
                    <span className="text-[9px] font-mono" style={{ color: HEALTH_C(p.avg_health) }}>{p.avg_health}%</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Pipeline Status */}
            <div className="col-span-3 rounded-lg p-3" style={{ background: '#111827', border: '1px solid #1A2540' }} data-testid="pipeline-status">
              <div className="text-[9px] uppercase tracking-widest mb-2 font-medium" style={{ color: '#4A6080' }}>Gateway Pipeline</div>
              <div className="space-y-1">
                {(gateway?.pipeline_stages || []).map((stage, i) => (
                  <div key={stage.name} className="flex items-center gap-2 px-2 py-1 rounded text-[9px]" style={{ background: '#0C1322' }}>
                    <span className="w-4 text-center font-mono font-bold" style={{ color: '#00B4D8' }}>{i + 1}</span>
                    <span className="font-mono font-semibold w-16" style={{ color: '#F0F4FF' }}>{stage.name}</span>
                    <span style={{ color: '#4A6080' }}>{stage.description}</span>
                  </div>
                ))}
              </div>
              {gw?.pipeline && (
                <div className="mt-2 pt-2 border-t flex justify-between text-[9px] font-mono" style={{ borderColor: '#1A2540' }}>
                  <span style={{ color: '#4A6080' }}>Queue: {gw.pipeline.queue_size}/{gw.pipeline.queue_max}</span>
                  <span style={{ color: gw.pipeline.errors > 0 ? '#FF3B3B' : '#00D97E' }}>Err: {gw.pipeline.errors}</span>
                  <span style={{ color: '#00B4D8' }}>Adapters: {gw.adapter_count || 0}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Device Twin Fleet Table */}
        <div className="flex-1 px-6 pb-6 overflow-hidden flex flex-col">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] uppercase tracking-widest font-medium" style={{ color: '#4A6080' }}>Device Fleet Twins ({twins.length})</span>
            <div className="flex items-center gap-2">
              <Funnel size={12} style={{ color: '#4A6080' }} />
              <select data-testid="twin-status-filter" value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="px-2 py-1 rounded text-[10px] outline-none" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }}>
                <option value="">All States</option>
                {['ONLINE', 'OFFLINE', 'ERROR', 'MAINTENANCE'].map(s => <option key={s} value={s}>{s}</option>)}
              </select>
              <select data-testid="twin-sort" value={sortBy} onChange={e => setSortBy(e.target.value)} className="px-2 py-1 rounded text-[10px] outline-none" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }}>
                <option value="health_score">Health (low first)</option>
                <option value="coin_in_today">Coin In (high first)</option>
                <option value="device_ref">Device ID</option>
              </select>
            </div>
          </div>

          <div className="rounded-lg border overflow-hidden flex-1 flex flex-col" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
            <div className="grid grid-cols-12 gap-1 px-4 py-2 text-[9px] uppercase tracking-widest font-medium border-b" style={{ color: '#4A6080', borderColor: '#1A2540' }}>
              <div className="col-span-1">Health</div><div className="col-span-2">Device</div><div className="col-span-1">Protocol</div>
              <div className="col-span-1">State</div><div className="col-span-1">Comms</div><div className="col-span-1">Integrity</div>
              <div className="col-span-1">Coin In</div><div className="col-span-1">Credits</div><div className="col-span-1">Games</div>
              <div className="col-span-2">Last Event</div>
            </div>
            <div className="flex-1 overflow-y-auto" data-testid="twin-fleet-table">
              {twins.map(t => (
                <button key={t.device_id} data-testid={`twin-row-${t.device_id}`} onClick={() => selectTwin(t)}
                  className="w-full grid grid-cols-12 gap-1 px-4 py-2 border-b text-[11px] text-left hover:bg-white/[0.02] transition-colors"
                  style={{ borderColor: '#1A254010', background: selected?.device_id === t.device_id ? 'rgba(0,180,216,0.04)' : 'transparent' }}>
                  <div className="col-span-1 flex items-center gap-1.5">
                    <span className="font-mono font-bold" style={{ color: HEALTH_C(t.health_score) }}>{t.health_score}</span>
                    <HealthBar score={t.health_score} width={30} />
                  </div>
                  <div className="col-span-2 font-mono font-medium" style={{ color: '#F0F4FF' }}>{t.device_ref || t.device_id?.slice(0, 12)}</div>
                  <div className="col-span-1 font-mono text-[10px] uppercase" style={{ color: '#8BA3CC' }}>{t.protocol}</div>
                  <div className="col-span-1"><span className="inline-flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full" style={{ background: STATE_C[t.operational_state] || '#4A6080' }} /><span className="text-[10px] font-mono" style={{ color: STATE_C[t.operational_state] }}>{t.operational_state}</span></span></div>
                  <div className="col-span-1"><span className="text-[10px] font-mono" style={{ color: COMMS_C[t.comms_state] || '#4A6080' }}>{t.comms_state}</span></div>
                  <div className="col-span-1"><span className="text-[10px] font-mono" style={{ color: t.software_integrity === 'PASS' ? '#00D97E' : t.software_integrity === 'FAIL' ? '#FF3B3B' : '#4A6080' }}>{t.software_integrity}</span></div>
                  <div className="col-span-1 font-mono" style={{ color: '#00D97E' }}>${(t.coin_in_today || 0).toLocaleString()}</div>
                  <div className="col-span-1 font-mono" style={{ color: '#FFB800' }}>{(t.current_credits || 0).toLocaleString()}</div>
                  <div className="col-span-1 font-mono" style={{ color: '#8BA3CC' }}>{(t.games_played_today || 0).toLocaleString()}</div>
                  <div className="col-span-2 font-mono text-[10px]" style={{ color: '#4A6080' }}>{t.last_event_at ? new Date(t.last_event_at).toLocaleTimeString() : '--'}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Right — Device Twin Detail */}
      {selected && (
        <div className="w-[420px] border-l flex-shrink-0 overflow-y-auto" style={{ background: '#0C1322', borderColor: '#1A2540' }} data-testid="twin-detail-panel">
          <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: '#1A2540' }}>
            <div>
              <h3 className="font-heading text-base font-semibold flex items-center gap-2" style={{ color: '#F0F4FF' }}>
                <Cpu size={18} style={{ color: '#00B4D8' }} /> {selected.device_ref || selected.device_id}
              </h3>
              <span className="text-xs" style={{ color: '#4A6080' }}>{selected.manufacturer} {selected.model}</span>
            </div>
            <button onClick={() => { setSelected(null); setDetail(null); }} style={{ color: '#4A6080' }}><X size={18} /></button>
          </div>

          <div className="p-4 space-y-4">
            {/* Health Score Gauge */}
            <div className="flex items-center gap-4">
              <div className="relative w-20 h-20">
                <svg width={80} height={80} viewBox="0 0 80 80">
                  <circle cx="40" cy="40" r="32" fill="none" stroke="#1A2540" strokeWidth="6" />
                  <circle cx="40" cy="40" r="32" fill="none" stroke={HEALTH_C(selected.health_score)} strokeWidth="6"
                    strokeDasharray={2 * Math.PI * 32} strokeDashoffset={2 * Math.PI * 32 * (1 - selected.health_score / 100)}
                    strokeLinecap="round" transform="rotate(-90 40 40)" style={{ transition: 'stroke-dashoffset 0.8s ease' }} />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="font-mono text-lg font-black" style={{ color: HEALTH_C(selected.health_score) }}>{selected.health_score}</span>
                </div>
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full" style={{ background: STATE_C[selected.operational_state] }} /><span className="text-xs font-mono" style={{ color: '#F0F4FF' }}>{selected.operational_state}</span></div>
                <div className="flex items-center gap-2"><WifiHigh size={12} style={{ color: COMMS_C[selected.comms_state] }} /><span className="text-xs font-mono" style={{ color: COMMS_C[selected.comms_state] }}>{selected.comms_state}</span></div>
                <div className="flex items-center gap-2"><ShieldCheck size={12} style={{ color: selected.software_integrity === 'PASS' ? '#00D97E' : '#FF3B3B' }} /><span className="text-xs font-mono" style={{ color: selected.software_integrity === 'PASS' ? '#00D97E' : '#FF3B3B' }}>{selected.software_integrity}</span></div>
              </div>
            </div>

            {/* Live Meters */}
            <div className="grid grid-cols-2 gap-2">
              {[
                { label: 'Coin In Today', value: `$${(selected.coin_in_today || 0).toLocaleString()}`, color: '#00D97E' },
                { label: 'Coin Out Today', value: `$${(selected.coin_out_today || 0).toLocaleString()}`, color: '#FF3B3B' },
                { label: 'Current Credits', value: (selected.current_credits || 0).toLocaleString(), color: '#FFB800' },
                { label: 'Games Today', value: (selected.games_played_today || 0).toLocaleString(), color: '#00B4D8' },
              ].map(m => (
                <div key={m.label} className="rounded p-2.5" style={{ background: '#111827', border: '1px solid #1A2540' }}>
                  <div className="text-[8px] uppercase tracking-widest" style={{ color: '#4A6080' }}>{m.label}</div>
                  <div className="font-mono text-sm font-bold" style={{ color: m.color }}>{m.value}</div>
                </div>
              ))}
            </div>

            {/* Timestamps */}
            <div className="rounded p-3 space-y-1.5 text-[10px] font-mono" style={{ background: '#111827', border: '1px solid #1A2540' }}>
              <div className="flex justify-between"><span style={{ color: '#4A6080' }}>Last Event</span><span style={{ color: '#F0F4FF' }}>{selected.last_event_at ? new Date(selected.last_event_at).toLocaleString() : '--'}</span></div>
              <div className="flex justify-between"><span style={{ color: '#4A6080' }}>Last Meter</span><span style={{ color: '#F0F4FF' }}>{selected.last_meter_at ? new Date(selected.last_meter_at).toLocaleString() : '--'}</span></div>
              <div className="flex justify-between"><span style={{ color: '#4A6080' }}>Last Integrity</span><span style={{ color: '#F0F4FF' }}>{selected.last_integrity_at ? new Date(selected.last_integrity_at).toLocaleString() : '--'}</span></div>
              <div className="flex justify-between"><span style={{ color: '#4A6080' }}>Updated</span><span style={{ color: '#00B4D8' }}>{selected.updated_at ? new Date(selected.updated_at).toLocaleString() : '--'}</span></div>
            </div>

            {/* Recent Events */}
            {detail?.recent_events?.length > 0 && (
              <div>
                <div className="text-[9px] uppercase tracking-widest mb-2 font-medium" style={{ color: '#4A6080' }}>Recent Events</div>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {detail.recent_events.map(e => (
                    <div key={e.id} className="flex items-center gap-2 px-2 py-1.5 rounded text-[10px] font-mono" style={{ background: '#111827' }}>
                      <span style={{ color: '#4A6080' }}>{new Date(e.occurred_at).toLocaleTimeString()}</span>
                      <span style={{ color: '#F0F4FF' }}>{e.event_type}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
