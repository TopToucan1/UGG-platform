import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import {
  MapPin, CurrencyDollar, Warning, ShieldCheck, WifiHigh,
  Receipt, Funnel, Check, CaretRight, ArrowUp, ArrowDown,
  Buildings, Lightning, Clock, Pulse, FileText
} from '@phosphor-icons/react';
import { AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const COLORS = ['#00D4AA', '#007AFF', '#F5A623', '#FF3B30', '#8B5CF6', '#EC4899', '#06B6D4'];
const EXC_COLORS = { CRITICAL: '#FF3B30', WARNING: '#F5A623', INFO: '#007AFF' };
const CONN_COLORS = { ONLINE: '#00D4AA', DEGRADED: '#F5A623', OFFLINE: '#FF3B30', AUTO_DISABLED: '#FF3B30' };

function Tip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded border px-3 py-2 text-xs" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
      <div className="font-mono mb-1" style={{ color: '#E8ECF1' }}>{label}</div>
      {payload.map((p, i) => <div key={i} style={{ color: p.color }}>{p.name}: {typeof p.value === 'number' ? `$${p.value.toLocaleString()}` : p.value}</div>)}
    </div>
  );
}

function KPI({ label, value, sub, color, icon: Icon }) {
  return (
    <div className="rounded border p-3" style={{ background: '#12151C', borderColor: '#272E3B' }}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-[9px] uppercase tracking-widest font-medium" style={{ color: '#6B7A90' }}>{label}</span>
        {Icon && <Icon size={16} style={{ color }} />}
      </div>
      <div className="font-mono text-xl font-bold" style={{ color: color || '#E8ECF1' }}>{value}</div>
      {sub && <div className="text-[10px] font-mono mt-0.5" style={{ color: '#6B7A90' }}>{sub}</div>}
    </div>
  );
}

const fmt = (v) => v != null ? `$${Number(v).toLocaleString()}` : '--';

export default function RouteOpsPage() {
  const [activeTab, setActiveTab] = useState('overview');
  const [dashboard, setDashboard] = useState(null);
  const [norSummary, setNorSummary] = useState(null);
  const [norTrend, setNorTrend] = useState([]);
  const [exceptions, setExceptions] = useState([]);
  const [excSummary, setExcSummary] = useState(null);
  const [integrity, setIntegrity] = useState([]);
  const [intSummary, setIntSummary] = useState(null);
  const [bufferStatus, setBufferStatus] = useState(null);
  const [eftFiles, setEftFiles] = useState([]);
  const [distributors, setDistributors] = useState([]);
  const [distFilter, setDistFilter] = useState('');
  const [excTypeFilter, setExcTypeFilter] = useState('');

  const fetchData = useCallback(async () => {
    try {
      const [dashR, norR, trendR, excR, excSumR, intR, intSumR, bufR, eftR, distR] = await Promise.all([
        api.get('/route/dashboard'),
        api.get(`/route/nor/summary?days=30${distFilter ? `&distributor_id=${distFilter}` : ''}`),
        api.get(`/route/nor/daily-trend?days=30${distFilter ? `&distributor_id=${distFilter}` : ''}`),
        api.get(`/route/exceptions?limit=50${distFilter ? `&distributor_id=${distFilter}` : ''}${excTypeFilter ? `&exc_type=${excTypeFilter}` : ''}`),
        api.get(`/route/exceptions/summary${distFilter ? `?distributor_id=${distFilter}` : ''}`),
        api.get('/route/integrity?limit=50'),
        api.get('/route/integrity/summary'),
        api.get('/route/buffer-status'),
        api.get('/route/eft'),
        api.get('/route/distributors'),
      ]);
      setDashboard(dashR.data);
      setNorSummary(norR.data);
      setNorTrend(trendR.data.trend || []);
      setExceptions(excR.data.exceptions || []);
      setExcSummary(excSumR.data);
      setIntegrity(intR.data.checks || []);
      setIntSummary(intSumR.data);
      setBufferStatus(bufR.data);
      setEftFiles(eftR.data.files || []);
      setDistributors(distR.data.distributors || []);
    } catch (err) { console.error(err); }
  }, [distFilter, excTypeFilter]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const resolveException = async (id) => {
    await api.post(`/route/exceptions/${id}/resolve`, { note: 'Resolved from Route Operations console' });
    fetchData();
  };

  const generateEft = async () => {
    await api.post('/route/eft/generate', { sweep_type: 'MANUAL' });
    fetchData();
  };

  const d = dashboard;
  const tabs = [
    { id: 'overview', label: 'Overview', icon: Pulse },
    { id: 'nor', label: 'NOR Accounting', icon: CurrencyDollar },
    { id: 'exceptions', label: 'Exceptions', icon: Warning },
    { id: 'integrity', label: 'Integrity', icon: ShieldCheck },
    { id: 'buffer', label: 'Offline Buffer', icon: WifiHigh },
    { id: 'eft', label: 'EFT Files', icon: FileText },
  ];

  return (
    <div data-testid="route-operations" className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-2xl font-bold tracking-tight flex items-center gap-3" style={{ color: '#E8ECF1' }}>
          <MapPin size={24} style={{ color: '#00D4AA' }} /> Route Operations
        </h1>
        <div className="flex items-center gap-3">
          <select data-testid="route-dist-filter" value={distFilter} onChange={e => setDistFilter(e.target.value)} className="px-3 py-1.5 rounded text-xs outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}>
            <option value="">All Distributors</option>
            {distributors.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b" style={{ borderColor: '#272E3B' }}>
        {tabs.map(t => (
          <button key={t.id} data-testid={`route-tab-${t.id}`} onClick={() => setActiveTab(t.id)}
            className="flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium uppercase tracking-wider transition-colors"
            style={{ color: activeTab === t.id ? '#00D4AA' : '#6B7A90', borderBottom: activeTab === t.id ? '2px solid #00D4AA' : '2px solid transparent' }}>
            <t.icon size={14} /> {t.label}
          </button>
        ))}
      </div>

      {/* ═══ OVERVIEW TAB ═══ */}
      {activeTab === 'overview' && d && (
        <div className="space-y-4" data-testid="route-overview">
          <div className="grid grid-cols-8 gap-3">
            <KPI label="Devices" value={d.devices?.total} color="#00D4AA" icon={Lightning} sub={`${d.devices?.online} online`} />
            <KPI label="Active Exceptions" value={d.exceptions?.active} color="#FF3B30" icon={Warning} sub={`${d.exceptions?.critical} critical`} />
            <KPI label="30d NOR" value={fmt(d.nor_30d?.total_nor)} color="#00D4AA" icon={CurrencyDollar} />
            <KPI label="30d Coin In" value={fmt(d.nor_30d?.total_coin_in)} color="#007AFF" icon={ArrowDown} />
            <KPI label="30d Tax" value={fmt(d.nor_30d?.total_tax)} color="#F5A623" icon={Receipt} />
            <KPI label="Distributors" value={d.distributors} color="#8B5CF6" icon={Buildings} />
            <KPI label="Integrity" value={`${d.integrity?.pass_rate}%`} color={d.integrity?.pass_rate >= 99 ? '#00D4AA' : '#FF3B30'} icon={ShieldCheck} sub={`${d.integrity?.total_checks} checks`} />
            <KPI label="Agents" value={`${d.agents?.online}/${d.agents?.total}`} color="#00D4AA" icon={WifiHigh} sub="online" />
          </div>

          {/* NOR Trend + Exception Breakdown */}
          <div className="grid grid-cols-12 gap-4">
            <div className="col-span-8 rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="nor-trend-chart">
              <div className="text-[11px] uppercase tracking-wider mb-3 font-medium" style={{ color: '#6B7A90' }}>Net Operating Revenue (30 Days)</div>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={norTrend}>
                  <defs>
                    <linearGradient id="norG" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#00D4AA" stopOpacity={0.3}/><stop offset="95%" stopColor="#00D4AA" stopOpacity={0}/></linearGradient>
                    <linearGradient id="coinG" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#007AFF" stopOpacity={0.2}/><stop offset="95%" stopColor="#007AFF" stopOpacity={0}/></linearGradient>
                  </defs>
                  <XAxis dataKey="date" tick={{ fill: '#6B7A90', fontSize: 9 }} axisLine={false} tickLine={false} interval={4} />
                  <YAxis tick={{ fill: '#6B7A90', fontSize: 9 }} axisLine={false} tickLine={false} width={50} tickFormatter={v => `$${(v/1000).toFixed(0)}k`} />
                  <Tooltip content={<Tip />} />
                  <Area type="monotone" dataKey="coin_in" stroke="#007AFF" fill="url(#coinG)" strokeWidth={1.5} name="Coin In" />
                  <Area type="monotone" dataKey="nor" stroke="#00D4AA" fill="url(#norG)" strokeWidth={2} name="NOR" />
                  <Legend wrapperStyle={{ fontSize: 10, color: '#6B7A90' }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="col-span-4 rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="exc-breakdown">
              <div className="text-[11px] uppercase tracking-wider mb-3 font-medium" style={{ color: '#6B7A90' }}>Exception Breakdown</div>
              <div className="space-y-1.5">
                {Object.entries(excSummary?.by_type || {}).map(([type, count], i) => (
                  <div key={type} className="flex items-center justify-between px-2 py-1.5 rounded" style={{ background: '#1A1E2A' }}>
                    <span className="text-[10px] font-mono" style={{ color: '#A3AEBE' }}>{type.replace(/_/g, ' ')}</span>
                    <span className="font-mono text-xs font-bold" style={{ color: COLORS[i % COLORS.length] }}>{count}</span>
                  </div>
                ))}
              </div>
              <div className="mt-3 pt-3 border-t" style={{ borderColor: '#272E3B' }}>
                <div className="flex justify-between text-xs">
                  <span style={{ color: '#6B7A90' }}>Oldest unresolved</span>
                  <span className="font-mono" style={{ color: '#F5A623' }}>{Math.round((excSummary?.oldest_unresolved_minutes || 0) / 60)}h {(excSummary?.oldest_unresolved_minutes || 0) % 60}m</span>
                </div>
              </div>
            </div>
          </div>

          {/* Distributor NOR Table */}
          {norSummary?.by_distributor?.length > 0 && (
            <div className="rounded border overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }}>
              <div className="px-4 py-2.5 border-b" style={{ borderColor: '#272E3B' }}>
                <span className="font-heading text-sm font-semibold" style={{ color: '#E8ECF1' }}>NOR by Distributor (30 Days)</span>
              </div>
              <div className="grid grid-cols-12 gap-2 px-4 py-2 text-[10px] uppercase tracking-wider font-medium border-b" style={{ color: '#6B7A90', borderColor: '#272E3B' }}>
                <div className="col-span-3">Distributor</div><div className="col-span-2">Coin In</div><div className="col-span-2">Coin Out</div><div className="col-span-2">NOR</div><div className="col-span-1">Tax</div><div className="col-span-1">Devices</div><div className="col-span-1">Hold%</div>
              </div>
              {norSummary.by_distributor.map(d => (
                <div key={d.distributor_id} className="grid grid-cols-12 gap-2 px-4 py-2 border-b text-xs hover:bg-white/[0.02]" style={{ borderColor: '#272E3B10' }}>
                  <div className="col-span-3 font-medium" style={{ color: '#E8ECF1' }}>{d.distributor_name}</div>
                  <div className="col-span-2 font-mono" style={{ color: '#007AFF' }}>{fmt(d.total_coin_in)}</div>
                  <div className="col-span-2 font-mono" style={{ color: '#FF3B30' }}>{fmt(d.total_coin_out)}</div>
                  <div className="col-span-2 font-mono font-bold" style={{ color: '#00D4AA' }}>{fmt(d.total_nor)}</div>
                  <div className="col-span-1 font-mono" style={{ color: '#F5A623' }}>{fmt(d.total_tax)}</div>
                  <div className="col-span-1 font-mono" style={{ color: '#6B7A90' }}>{d.device_count}</div>
                  <div className="col-span-1 font-mono" style={{ color: '#E8ECF1' }}>{d.total_coin_in > 0 ? (d.total_nor / d.total_coin_in * 100).toFixed(1) : 0}%</div>
                </div>
              ))}
              {norSummary.grand_total && (
                <div className="grid grid-cols-12 gap-2 px-4 py-2 text-xs font-bold" style={{ background: '#1A1E2A' }}>
                  <div className="col-span-3" style={{ color: '#E8ECF1' }}>GRAND TOTAL</div>
                  <div className="col-span-2 font-mono" style={{ color: '#007AFF' }}>{fmt(norSummary.grand_total.total_coin_in)}</div>
                  <div className="col-span-2" />
                  <div className="col-span-2 font-mono" style={{ color: '#00D4AA' }}>{fmt(norSummary.grand_total.total_nor)}</div>
                  <div className="col-span-1 font-mono" style={{ color: '#F5A623' }}>{fmt(norSummary.grand_total.total_tax)}</div>
                  <div className="col-span-1 font-mono" style={{ color: '#6B7A90' }}>{norSummary.grand_total.total_devices}</div>
                  <div className="col-span-1" />
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ═══ NOR TAB ═══ */}
      {activeTab === 'nor' && (
        <div className="space-y-4" data-testid="route-nor">
          <div className="rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
            <div className="text-[11px] uppercase tracking-wider mb-3 font-medium" style={{ color: '#6B7A90' }}>Daily NOR Trend</div>
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={norTrend}>
                <defs>
                  <linearGradient id="norG2" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#00D4AA" stopOpacity={0.35}/><stop offset="95%" stopColor="#00D4AA" stopOpacity={0}/></linearGradient>
                </defs>
                <XAxis dataKey="date" tick={{ fill: '#6B7A90', fontSize: 10 }} axisLine={false} tickLine={false} interval={3} />
                <YAxis tick={{ fill: '#6B7A90', fontSize: 10 }} axisLine={false} tickLine={false} width={60} tickFormatter={v => `$${(v/1000).toFixed(0)}k`} />
                <Tooltip content={<Tip />} />
                <Area type="monotone" dataKey="coin_in" stroke="#007AFF" fill="none" strokeWidth={1} strokeDasharray="4 4" name="Coin In" />
                <Area type="monotone" dataKey="nor" stroke="#00D4AA" fill="url(#norG2)" strokeWidth={2} name="NOR" />
                <Area type="monotone" dataKey="tax" stroke="#F5A623" fill="none" strokeWidth={1} strokeDasharray="2 2" name="Tax" />
                <Legend wrapperStyle={{ fontSize: 10 }} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* ═══ EXCEPTIONS TAB ═══ */}
      {activeTab === 'exceptions' && (
        <div className="space-y-4" data-testid="route-exceptions">
          <div className="flex items-center gap-3">
            <Funnel size={14} style={{ color: '#6B7A90' }} />
            <select data-testid="exc-type-filter" value={excTypeFilter} onChange={e => setExcTypeFilter(e.target.value)} className="px-3 py-1.5 rounded text-xs outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}>
              <option value="">All Types</option>
              {["DEVICE_OFFLINE", "SITE_CONTROLLER_OFFLINE", "INTEGRITY_VIOLATION", "ZERO_PLAY_TODAY", "LOW_PLAY_ALERT", "DOOR_OPEN", "HANDPAY_PENDING", "NSF_ALERT"].map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
            </select>
            <span className="text-xs font-mono" style={{ color: '#FF3B30' }}>{excSummary?.total_active || 0} active ({excSummary?.critical_count || 0} critical)</span>
          </div>
          <div className="space-y-2">
            {exceptions.map(exc => (
              <div key={exc.id} data-testid={`route-exc-${exc.id}`} className="rounded border px-4 py-3 flex items-center gap-4"
                style={{ background: '#12151C', borderColor: `${EXC_COLORS[exc.severity]}30`, borderLeftWidth: 3, borderLeftColor: EXC_COLORS[exc.severity] }}>
                <Warning size={16} style={{ color: EXC_COLORS[exc.severity] }} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="font-mono text-[10px] px-1.5 py-0.5 rounded" style={{ background: `${EXC_COLORS[exc.severity]}15`, color: EXC_COLORS[exc.severity] }}>{exc.severity}</span>
                    <span className="font-mono text-[10px] px-1.5 py-0.5 rounded" style={{ background: '#1A1E2A', color: '#A3AEBE' }}>{exc.type.replace(/_/g, ' ')}</span>
                    <span className="font-mono text-xs" style={{ color: '#E8ECF1' }}>{exc.device_ref}</span>
                  </div>
                  <div className="text-xs" style={{ color: '#A3AEBE' }}>{exc.detail}</div>
                  <div className="text-[10px] font-mono mt-0.5" style={{ color: '#6B7A90' }}>{exc.site_name} | {new Date(exc.raised_at).toLocaleString()}</div>
                </div>
                {exc.is_active && (
                  <button data-testid={`resolve-exc-${exc.id}`} onClick={() => resolveException(exc.id)} className="flex items-center gap-1 px-3 py-1.5 rounded text-xs font-medium flex-shrink-0" style={{ background: 'rgba(0,212,170,0.1)', color: '#00D4AA' }}>
                    <Check size={14} /> Resolve
                  </button>
                )}
                {!exc.is_active && <span className="text-[10px] font-mono" style={{ color: '#00D4AA' }}>Resolved</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ═══ INTEGRITY TAB ═══ */}
      {activeTab === 'integrity' && (
        <div className="space-y-4" data-testid="route-integrity">
          <div className="grid grid-cols-5 gap-3">
            <KPI label="Total Checks" value={intSummary?.total || 0} color="#E8ECF1" />
            <KPI label="Passed" value={intSummary?.passed || 0} color="#00D4AA" icon={ShieldCheck} />
            <KPI label="Failed" value={intSummary?.failed || 0} color="#FF3B30" icon={Warning} />
            <KPI label="Pass Rate" value={`${intSummary?.pass_rate || 0}%`} color={intSummary?.pass_rate >= 99 ? '#00D4AA' : '#FF3B30'} />
            <KPI label="No Image" value={intSummary?.no_image || 0} color="#F5A623" />
          </div>
          <div className="rounded border overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }}>
            <div className="grid grid-cols-12 gap-2 px-4 py-2 text-[10px] uppercase tracking-wider font-medium border-b" style={{ color: '#6B7A90', borderColor: '#272E3B' }}>
              <div className="col-span-2">Time</div><div className="col-span-2">Device</div><div className="col-span-1">Trigger</div><div className="col-span-2">Software</div><div className="col-span-1">Result</div><div className="col-span-2">Action</div><div className="col-span-2">Signature</div>
            </div>
            <div className="max-h-96 overflow-y-auto">
              {integrity.map(c => (
                <div key={c.id} className="grid grid-cols-12 gap-2 px-4 py-2 border-b text-xs hover:bg-white/[0.02]" style={{ borderColor: '#272E3B10' }}>
                  <div className="col-span-2 font-mono" style={{ color: '#6B7A90' }}>{new Date(c.check_time).toLocaleString()}</div>
                  <div className="col-span-2 font-mono" style={{ color: '#E8ECF1' }}>{c.device_ref}</div>
                  <div className="col-span-1 font-mono text-[10px]" style={{ color: '#A3AEBE' }}>{c.trigger}</div>
                  <div className="col-span-2 font-mono" style={{ color: '#6B7A90' }}>{c.software_version}</div>
                  <div className="col-span-1"><span className="font-mono text-[10px] px-1.5 py-0.5 rounded" style={{ background: c.result === 'PASS' ? 'rgba(0,212,170,0.1)' : 'rgba(255,59,48,0.1)', color: c.result === 'PASS' ? '#00D4AA' : '#FF3B30' }}>{c.result}</span></div>
                  <div className="col-span-2 font-mono text-[10px]" style={{ color: c.action_taken === 'DEVICE_DISABLED' ? '#FF3B30' : '#6B7A90' }}>{c.action_taken}</div>
                  <div className="col-span-2 font-mono text-[10px] truncate" style={{ color: '#6B7A90' }}>{c.reported_signature?.slice(0, 16)}...</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ═══ BUFFER TAB ═══ */}
      {activeTab === 'buffer' && bufferStatus && (
        <div className="space-y-4" data-testid="route-buffer">
          <div className="grid grid-cols-4 gap-3">
            <KPI label="Agents Online" value={bufferStatus.summary?.online || 0} color="#00D4AA" icon={WifiHigh} />
            <KPI label="Degraded" value={bufferStatus.summary?.degraded || 0} color="#F5A623" />
            <KPI label="Offline" value={bufferStatus.summary?.offline || 0} color="#FF3B30" />
            <KPI label="Pending Events" value={(bufferStatus.summary?.total_pending_events || 0).toLocaleString()} color="#007AFF" />
          </div>
          <div className="space-y-2">
            {bufferStatus.agents?.map(a => (
              <div key={a.id} className="rounded border px-4 py-3 flex items-center gap-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
                <span className={`w-3 h-3 rounded-full ${a.connectivity_state === 'ONLINE' ? 'pulse-online' : ''}`} style={{ background: CONN_COLORS[a.connectivity_state] || '#6B7A90' }} />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-medium" style={{ color: '#E8ECF1' }}>{a.agent_name}</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded" style={{ background: `${CONN_COLORS[a.connectivity_state]}15`, color: CONN_COLORS[a.connectivity_state] }}>{a.connectivity_state}</span>
                  </div>
                  <div className="text-[10px] font-mono mt-0.5" style={{ color: '#6B7A90' }}>
                    Pending: {a.pending_events?.toLocaleString()} | Buffered: {a.total_buffered?.toLocaleString()} | Last sync: {a.last_sync_at ? new Date(a.last_sync_at).toLocaleString() : 'Never'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ═══ EFT TAB ═══ */}
      {activeTab === 'eft' && (
        <div className="space-y-4" data-testid="route-eft">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono" style={{ color: '#6B7A90' }}>{eftFiles.length} EFT files</span>
            <button data-testid="generate-eft-btn" onClick={generateEft} className="flex items-center gap-2 px-4 py-2 rounded text-xs font-medium" style={{ background: '#00D4AA', color: '#0A0C10' }}>
              <FileText size={14} /> Generate Manual Sweep
            </button>
          </div>
          <div className="space-y-2">
            {eftFiles.map(f => (
              <div key={f.id} className="rounded border px-4 py-3 flex items-center gap-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
                <FileText size={18} style={{ color: f.status === 'TRANSMITTED' ? '#00D4AA' : '#F5A623' }} />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-medium" style={{ color: '#E8ECF1' }}>{f.filename}</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded" style={{ background: f.status === 'TRANSMITTED' ? 'rgba(0,212,170,0.1)' : 'rgba(245,166,35,0.1)', color: f.status === 'TRANSMITTED' ? '#00D4AA' : '#F5A623' }}>{f.status}</span>
                  </div>
                  <div className="text-[10px] font-mono mt-0.5" style={{ color: '#6B7A90' }}>
                    {f.period_start} to {f.period_end} | {f.sweep_type} | {f.entry_count} entries | ${(f.total_amount_cents / 100).toLocaleString()}
                  </div>
                </div>
                <span className="text-[10px] font-mono" style={{ color: '#6B7A90' }}>{new Date(f.generated_at).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
