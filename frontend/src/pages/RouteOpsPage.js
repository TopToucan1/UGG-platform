import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import {
  MapPin, CurrencyDollar, Warning, ShieldCheck, WifiHigh,
  Receipt, Funnel, Check, CaretRight, ArrowUp, ArrowDown,
  Buildings, Lightning, Clock, Pulse, FileText, Users,
  Gauge, Scroll, LockKey
} from '@phosphor-icons/react';
import { AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import InfoTip from '@/components/InfoTip';

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

function KPI({ label, value, sub, color, icon: Icon, tip }) {
  return (
    <div className="rounded border p-3" style={{ background: '#12151C', borderColor: '#272E3B' }}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-[9px] uppercase tracking-widest font-medium flex items-center" style={{ color: '#6B7A90' }}>{label}{tip && <InfoTip description={tip} />}</span>
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
  const [statutory, setStatutory] = useState(null);
  const [rbacRoles, setRbacRoles] = useState(null);
  const [rbacUsers, setRbacUsers] = useState([]);
  const [perfMetrics, setPerfMetrics] = useState(null);
  const [nachaResult, setNachaResult] = useState(null);

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
      // Advanced modules
      const [statR, rbacR, rbacUR, perfR] = await Promise.all([
        api.get('/route/advanced/statutory/enrichment-status'),
        api.get('/route/advanced/rbac/roles'),
        api.get('/route/advanced/rbac/users').catch(() => ({ data: { users: [] } })),
        api.get('/route/advanced/performance/metrics'),
      ]);
      setStatutory(statR.data);
      setRbacRoles(rbacR.data.roles);
      setRbacUsers(rbacUR.data.users || []);
      setPerfMetrics(perfR.data);
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

  const enrichEvents = async () => {
    await api.post('/route/advanced/statutory/enrich-batch', { limit: 1000 });
    fetchData();
  };

  const generateNacha = async () => {
    const { data } = await api.post('/route/advanced/eft/generate-nacha', { sweep_type: 'WEEKLY' });
    setNachaResult(data);
    fetchData();
  };

  const d = dashboard;
  const tabs = [
    { id: 'overview', label: 'Overview', icon: Pulse, tip: 'Estate-wide snapshot: devices, revenue, integrity, exceptions.' },
    { id: 'nor', label: 'NOR Accounting', icon: CurrencyDollar, tip: 'Net Operating Revenue = Coin In minus Coin Out. The number states tax the player-owed earnings.' },
    { id: 'exceptions', label: 'Exceptions', icon: Warning, tip: 'Machine alerts needing attention: offline devices, zero play, door open, handpays pending, etc.' },
    { id: 'integrity', label: 'Integrity', icon: ShieldCheck, tip: 'Software signature checks that verify machine firmware has not been tampered with. State law requires these pass.' },
    { id: 'statutory', label: 'Statutory', icon: Scroll, tip: 'Statutory report = the monthly/quarterly filing required by state gaming law. Tracks that every event has the mandatory fields the state demands.' },
    { id: 'rbac', label: 'RBAC Portal', icon: LockKey, tip: 'Role-based access control. Four tiers: regulator, distributor, retailer, manufacturer — each seeing only data they are entitled to.' },
    { id: 'buffer', label: 'Offline Buffer', icon: WifiHigh, tip: 'Site controllers keep buffering meter and event data when the network drops. This tab shows which agents are caught up versus lagging.' },
    { id: 'eft', label: 'EFT/NACHA', icon: FileText, tip: 'Electronic Funds Transfer files used to sweep taxes/fees to the state. NACHA is the US bank-file format required for these transfers.' },
    { id: 'performance', label: 'Performance', icon: Gauge, tip: 'Query latency benchmarks, database sizes, and scale projections for the route platform.' },
  ];

  return (
    <div data-testid="route-operations" className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-2xl font-bold tracking-tight flex items-center gap-3" style={{ color: '#E8ECF1' }}>
          <MapPin size={24} style={{ color: '#00D4AA' }} /> Route Operations
          <InfoTip label="Route Operations" description="Central console for running slot machines placed in bars and taverns. Tracks revenue (NOR), exceptions (machine problems), software integrity checks, EFT tax sweeps, and the four-tier regulator/distributor/retailer/manufacturer portal." />
        </h1>
        <div className="flex items-center gap-3">
          <select data-testid="route-dist-filter" value={distFilter} onChange={e => setDistFilter(e.target.value)} className="px-3 py-1.5 rounded text-xs outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}>
            <option value="">All Distributors</option>
            {distributors.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
          <InfoTip description="Filter every tab below to a single distributor (the company that owns and services the machines at retailer sites)." />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b" style={{ borderColor: '#272E3B' }}>
        {tabs.map(t => (
          <button key={t.id} data-testid={`route-tab-${t.id}`} onClick={() => setActiveTab(t.id)}
            className="flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium uppercase tracking-wider transition-colors"
            style={{ color: activeTab === t.id ? '#00D4AA' : '#6B7A90', borderBottom: activeTab === t.id ? '2px solid #00D4AA' : '2px solid transparent' }}>
            <t.icon size={14} /> {t.label}{t.tip && <InfoTip description={t.tip} />}
          </button>
        ))}
      </div>

      {/* ═══ OVERVIEW TAB ═══ */}
      {activeTab === 'overview' && d && (
        <div className="space-y-4" data-testid="route-overview">
          <div className="grid grid-cols-8 gap-3">
            <KPI label="Devices" value={d.devices?.total} color="#00D4AA" icon={Lightning} sub={`${d.devices?.online} online`} tip="Total slot machines under management across every retailer site." />
            <KPI label="Active Exceptions" value={d.exceptions?.active} color="#FF3B30" icon={Warning} sub={`${d.exceptions?.critical} critical`} tip="Unresolved machine alerts right now. Critical means needs immediate operator action." />
            <KPI label="30d NOR" value={fmt(d.nor_30d?.total_nor)} color="#00D4AA" icon={CurrencyDollar} tip="Net Operating Revenue over the last 30 days. NOR = Coin In minus Coin Out (what the house kept before tax)." />
            <KPI label="30d Coin In" value={fmt(d.nor_30d?.total_coin_in)} color="#007AFF" icon={ArrowDown} tip="Total wagered by players across all machines in the last 30 days. Includes recycled winnings." />
            <KPI label="30d Tax" value={fmt(d.nor_30d?.total_tax)} color="#F5A623" icon={Receipt} tip="Taxes and fees the state is owed on the 30-day NOR. Swept to the state via EFT." />
            <KPI label="Distributors" value={d.distributors} color="#8B5CF6" icon={Buildings} tip="Licensed companies that own the machines and service them at retailer sites." />
            <KPI label="Integrity" value={`${d.integrity?.pass_rate}%`} color={d.integrity?.pass_rate >= 99 ? '#00D4AA' : '#FF3B30'} icon={ShieldCheck} sub={`${d.integrity?.total_checks} checks`} tip="Pass rate on software signature checks. State law usually requires 99%+ — any failure means the machine firmware may have been tampered with." />
            <KPI label="Agents" value={`${d.agents?.online}/${d.agents?.total}`} color="#00D4AA" icon={WifiHigh} sub="online" tip="Site controller agents currently talking to the central system. Offline agents buffer locally and catch up later." />
          </div>

          {/* NOR Trend + Exception Breakdown */}
          <div className="grid grid-cols-12 gap-4">
            <div className="col-span-8 rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="nor-trend-chart">
              <div className="text-[11px] uppercase tracking-wider mb-3 font-medium flex items-center" style={{ color: '#6B7A90' }}>Net Operating Revenue (30 Days)<InfoTip description="Daily NOR and Coin In trend for the last 30 days. NOR = what the house kept (Coin In minus Coin Out)." /></div>
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
              <div className="text-[11px] uppercase tracking-wider mb-3 font-medium flex items-center" style={{ color: '#6B7A90' }}>Exception Breakdown<InfoTip description="Active machine alerts grouped by type (offline, zero play, door open, handpay pending, etc.)." /></div>
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
                <span className="font-heading text-sm font-semibold flex items-center" style={{ color: '#E8ECF1' }}>NOR by Distributor (30 Days)<InfoTip description="30-day revenue, taxes, and device count grouped by the distributor (machine owner/service company)." /></span>
              </div>
              <div className="grid grid-cols-12 gap-2 px-4 py-2 text-[10px] uppercase tracking-wider font-medium border-b" style={{ color: '#6B7A90', borderColor: '#272E3B' }}>
                <div className="col-span-3 flex items-center">Distributor<InfoTip description="Licensed machine owner/service company." /></div><div className="col-span-2 flex items-center">Coin In<InfoTip description="Total dollars wagered by players across this distributor's machines." /></div><div className="col-span-2 flex items-center">Coin Out<InfoTip description="Total dollars paid out to players as winnings." /></div><div className="col-span-2 flex items-center">NOR<InfoTip description="Net Operating Revenue = Coin In minus Coin Out (house keep before tax)." /></div><div className="col-span-1 flex items-center">Tax<InfoTip description="State tax/fees owed on this NOR." /></div><div className="col-span-1 flex items-center">Devices<InfoTip description="Number of active machines for this distributor." /></div><div className="col-span-1 flex items-center">Hold%<InfoTip description="NOR as a percent of Coin In. Higher means the house kept a larger share of wagers." /></div>
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
            <div className="text-[11px] uppercase tracking-wider mb-3 font-medium flex items-center" style={{ color: '#6B7A90' }}>Daily NOR Trend<InfoTip description="Day-by-day NOR, Coin In, and tax accrual across the last 30 days for the selected scope." /></div>
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
            <InfoTip description="Filter the exception list to a single alert type." />
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
                    <Check size={14} /> Resolve<InfoTip description="Mark this alert as handled. Adds a resolution note and clears it from the active list." />
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
            <KPI label="Total Checks" value={intSummary?.total || 0} color="#E8ECF1" tip="Number of integrity checks performed — verifications that a machine's software signature matches the approved version on file." />
            <KPI label="Passed" value={intSummary?.passed || 0} color="#00D4AA" icon={ShieldCheck} tip="Checks where the machine's software signature matched the approved reference." />
            <KPI label="Failed" value={intSummary?.failed || 0} color="#FF3B30" icon={Warning} tip="Checks where the signature did NOT match — possible tampering. Machine may be auto-disabled and must be investigated." />
            <KPI label="Pass Rate" value={`${intSummary?.pass_rate || 0}%`} color={intSummary?.pass_rate >= 99 ? '#00D4AA' : '#FF3B30'} tip="Percentage of integrity checks that passed. State regulators typically require 99%+." />
            <KPI label="No Image" value={intSummary?.no_image || 0} color="#F5A623" tip="Checks that could not be completed because we don't have an approved reference signature on file for that firmware version." />
          </div>
          <div className="rounded border overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }}>
            <div className="grid grid-cols-12 gap-2 px-4 py-2 text-[10px] uppercase tracking-wider font-medium border-b" style={{ color: '#6B7A90', borderColor: '#272E3B' }}>
              <div className="col-span-2 flex items-center">Time<InfoTip description="When the check ran." /></div><div className="col-span-2 flex items-center">Device<InfoTip description="Which machine was checked." /></div><div className="col-span-1 flex items-center">Trigger<InfoTip description="What caused the check to run (scheduled, boot-up, manual, or post-incident)." /></div><div className="col-span-2 flex items-center">Software<InfoTip description="Firmware version reported by the machine." /></div><div className="col-span-1 flex items-center">Result<InfoTip description="PASS = signature matched the approved reference. FAIL = possible tampering." /></div><div className="col-span-2 flex items-center">Action<InfoTip description="What the system did automatically — e.g. DEVICE_DISABLED locks the machine until an operator clears it." /></div><div className="col-span-2 flex items-center">Signature<InfoTip description="SHA-256 fingerprint the machine reported for its software bundle." /></div>
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
            <KPI label="Agents Online" value={bufferStatus.summary?.online || 0} color="#00D4AA" icon={WifiHigh} tip="Site controller agents currently connected and syncing events live." />
            <KPI label="Degraded" value={bufferStatus.summary?.degraded || 0} color="#F5A623" tip="Agents reachable but falling behind — their local buffer is growing faster than it drains." />
            <KPI label="Offline" value={bufferStatus.summary?.offline || 0} color="#FF3B30" tip="Agents we can't reach right now. They keep recording meters and events locally until the link comes back." />
            <KPI label="Pending Events" value={(bufferStatus.summary?.total_pending_events || 0).toLocaleString()} color="#007AFF" tip="Events sitting on site-controller disks waiting to be uploaded to the central system." />
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
            <div className="flex gap-2">
              <button data-testid="generate-nacha-btn" onClick={generateNacha} className="flex items-center gap-2 px-4 py-2 rounded text-xs font-medium" style={{ background: '#007AFF', color: '#E8ECF1' }}>
                <FileText size={14} /> Generate NACHA-Compliant<InfoTip description="Produce a strictly NACHA-format bank file (the US standard for ACH transfers) ready to submit to the bank for state tax sweep." />
              </button>
              <button data-testid="generate-eft-btn" onClick={generateEft} className="flex items-center gap-2 px-4 py-2 rounded text-xs font-medium" style={{ background: '#00D4AA', color: '#0A0C10' }}>
                <FileText size={14} /> Quick Sweep<InfoTip description="Run an ad-hoc manual sweep that bundles current NOR-accrued taxes into an EFT file without waiting for the scheduled cadence." />
              </button>
            </div>
          </div>
          {nachaResult && (
            <div className="rounded border p-4 space-y-3" style={{ background: '#12151C', borderColor: nachaResult.nacha_compliant ? '#00D4AA40' : '#FF3B3040' }}>
              <div className="flex items-center gap-2">
                <span className="font-heading text-sm font-semibold" style={{ color: '#E8ECF1' }}>NACHA Validation</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded" style={{ background: nachaResult.nacha_compliant ? 'rgba(0,212,170,0.1)' : 'rgba(255,59,48,0.1)', color: nachaResult.nacha_compliant ? '#00D4AA' : '#FF3B30' }}>
                  {nachaResult.nacha_compliant ? 'COMPLIANT' : 'ERRORS FOUND'}
                </span>
              </div>
              {nachaResult.validation?.checks?.map((c, i) => (
                <div key={i} className="flex items-center gap-2 text-xs">
                  <span className="w-4 h-4 rounded-full flex items-center justify-center" style={{ background: c.passed ? 'rgba(0,212,170,0.15)' : 'rgba(255,59,48,0.15)' }}>
                    {c.passed ? <Check size={10} style={{ color: '#00D4AA' }} /> : <Warning size={10} style={{ color: '#FF3B30' }} />}
                  </span>
                  <span style={{ color: c.passed ? '#A3AEBE' : '#FF3B30' }}>{c.check}</span>
                </div>
              ))}
              {nachaResult.validation?.record_counts && (
                <div className="grid grid-cols-3 gap-2 mt-2">
                  {Object.entries(nachaResult.validation.record_counts).map(([k, v]) => (
                    <div key={k} className="text-[10px] font-mono px-2 py-1 rounded" style={{ background: '#1A1E2A' }}>
                      <span style={{ color: '#6B7A90' }}>{k}: </span><span style={{ color: '#E8ECF1' }}>{v}</span>
                    </div>
                  ))}
                </div>
              )}
              <div className="text-[10px] font-mono" style={{ color: '#6B7A90' }}>
                {nachaResult.filename} | {nachaResult.entry_count} entries | ${((nachaResult.total_amount_cents || 0) / 100).toLocaleString()} | {nachaResult.line_count} lines
              </div>
            </div>
          )}
          <div className="space-y-2">
            {eftFiles.map(f => (
              <div key={f.id} className="rounded border px-4 py-3 flex items-center gap-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
                <FileText size={18} style={{ color: f.status === 'TRANSMITTED' ? '#00D4AA' : '#F5A623' }} />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-medium" style={{ color: '#E8ECF1' }}>{f.filename}</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded" style={{ background: f.status === 'TRANSMITTED' ? 'rgba(0,212,170,0.1)' : 'rgba(245,166,35,0.1)', color: f.status === 'TRANSMITTED' ? '#00D4AA' : '#F5A623' }}>{f.status}</span>
                    {f.nacha_compliant !== undefined && (
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded" style={{ background: f.nacha_compliant ? 'rgba(0,212,170,0.1)' : 'rgba(255,59,48,0.1)', color: f.nacha_compliant ? '#00D4AA' : '#FF3B30' }}>
                        {f.nacha_compliant ? 'NACHA OK' : 'NACHA ERR'}
                      </span>
                    )}
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

      {/* ═══ STATUTORY TAB ═══ */}
      {activeTab === 'statutory' && statutory && (
        <div className="space-y-4" data-testid="route-statutory">
          <div className="flex items-center justify-between">
            <h3 className="font-heading text-lg font-semibold flex items-center" style={{ color: '#E8ECF1' }}>Statutory Reporting Fields (Module 4)<InfoTip description="Every gaming event sent to the state must carry certain mandatory fields (license, county, serial, software signature, etc). This tab shows how many events are missing them." /></h3>
            <button data-testid="enrich-events-btn" onClick={enrichEvents} className="flex items-center gap-2 px-4 py-2 rounded text-xs font-medium" style={{ background: '#00D4AA', color: '#0A0C10' }}>
              <Scroll size={14} /> Enrich Events<InfoTip description="Back-fill missing statutory fields on recent events (license, operator, site county, software signature, etc.) so they can be included in the next state report." />
            </button>
          </div>
          <div className="grid grid-cols-4 gap-3">
            <KPI label="Total Events" value={statutory.total_events?.toLocaleString()} color="#E8ECF1" tip="Every meter/event reported from machines in the reporting window." />
            <KPI label="Enriched" value={statutory.enriched_events?.toLocaleString()} color="#00D4AA" icon={Check} tip="Events that already have all mandatory statutory fields filled in and are safe to include in a state filing." />
            <KPI label="Missing" value={statutory.missing_enrichment?.toLocaleString()} color={statutory.missing_enrichment > 0 ? '#FF3B30' : '#00D4AA'} tip="Events missing one or more required fields. These must be fixed before the state report can be submitted." />
            <KPI label="Enrichment Rate" value={`${statutory.enrichment_rate}%`} color={statutory.enrichment_rate >= 95 ? '#00D4AA' : '#F5A623'} tip="Percentage of events that are ready for statutory filing. Should be 99%+ before cutoff." />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
              <div className="text-[11px] uppercase tracking-wider mb-3 font-medium flex items-center" style={{ color: '#6B7A90' }}>Required Statutory Fields<InfoTip description="The mandatory data points every gaming event must carry to be accepted in a state regulatory filing." /></div>
              <div className="space-y-1.5">
                {["distributor_id", "operator_id", "site_address", "site_city", "site_county", "software_version", "software_signature", "device_serial"].map(f => (
                  <div key={f} className="flex items-center gap-2 px-3 py-2 rounded text-xs font-mono" style={{ background: '#1A1E2A' }}>
                    <Check size={12} style={{ color: '#00D4AA' }} />
                    <span style={{ color: '#E8ECF1' }}>{f}</span>
                    <span className="ml-auto text-[10px]" style={{ color: '#6B7A90' }}>mandatory</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
              <div className="text-[11px] uppercase tracking-wider mb-3 font-medium flex items-center" style={{ color: '#6B7A90' }}>Events by County<InfoTip description="Event volume broken down by county where the machine operates — some states require per-county reporting." /></div>
              <div className="space-y-1.5">
                {(statutory.by_county || []).map((c, i) => (
                  <div key={c.county || i} className="flex items-center justify-between px-3 py-2 rounded text-xs" style={{ background: '#1A1E2A' }}>
                    <span style={{ color: '#E8ECF1' }}>{c.county || 'Not Enriched'}</span>
                    <span className="font-mono" style={{ color: '#00D4AA' }}>{c.count?.toLocaleString()}</span>
                  </div>
                ))}
                {(!statutory.by_county || statutory.by_county.length === 0) && (
                  <div className="text-xs text-center py-4" style={{ color: '#6B7A90' }}>Run enrichment to see county breakdown</div>
                )}
              </div>
            </div>
          </div>
          <div className="rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
            <div className="text-[11px] uppercase tracking-wider mb-2 font-medium flex items-center" style={{ color: '#6B7A90' }}>Enrichment Coverage<InfoTip description="Visual progress of how much of the event stream is ready for statutory filing." /></div>
            <div className="h-3 rounded-full overflow-hidden" style={{ background: '#272E3B' }}>
              <div className="h-full rounded-full transition-all duration-500" style={{ width: `${statutory.enrichment_rate || 0}%`, background: statutory.enrichment_rate >= 95 ? '#00D4AA' : statutory.enrichment_rate >= 50 ? '#F5A623' : '#FF3B30' }} />
            </div>
            <div className="flex justify-between text-[10px] font-mono mt-1" style={{ color: '#6B7A90' }}>
              <span>0%</span><span>{statutory.enrichment_rate}% enriched</span><span>100%</span>
            </div>
          </div>
        </div>
      )}

      {/* ═══ RBAC PORTAL TAB ═══ */}
      {activeTab === 'rbac' && (
        <div className="space-y-4" data-testid="route-rbac">
          <h3 className="font-heading text-lg font-semibold flex items-center" style={{ color: '#E8ECF1' }}>4-Tier RBAC Portal (Module 7)<InfoTip description="The four-tier access model: state regulator, distributor, retailer, manufacturer. Each tier sees only data they are licensed to access." /></h3>
          {/* Tier Cards */}
          <div className="grid grid-cols-4 gap-3">
            {rbacRoles && Object.entries(rbacRoles).map(([role, perms], i) => {
              const tierColors = ['#FFD700', '#00D4AA', '#007AFF', '#8B5CF6'];
              return (
                <div key={role} className="rounded border p-4" style={{ background: '#12151C', borderColor: `${tierColors[i]}30` }}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-bold px-2 py-0.5 rounded" style={{ background: `${tierColors[i]}20`, color: tierColors[i] }}>Tier {perms.tier}</span>
                    <span className="text-xs font-medium" style={{ color: '#E8ECF1' }}>{perms.label}</span>
                  </div>
                  <div className="text-[10px] mb-3" style={{ color: '#6B7A90' }}>{perms.description}</div>
                  <div className="space-y-1">
                    {['can_view_revenue', 'can_view_devices', 'can_view_integrity', 'can_view_eft', 'can_enable_disable_devices'].map(perm => (
                      <div key={perm} className="flex items-center gap-1.5 text-[9px] font-mono">
                        <span className="w-3 h-3 rounded-full flex items-center justify-center" style={{ background: perms[perm] ? 'rgba(0,212,170,0.15)' : 'rgba(255,59,48,0.1)' }}>
                          {perms[perm] ? <Check size={8} style={{ color: '#00D4AA' }} /> : <span style={{ color: '#FF3B30' }}>-</span>}
                        </span>
                        <span style={{ color: perms[perm] ? '#A3AEBE' : '#6B7A90' }}>{perm.replace(/can_|_/g, ' ').trim()}</span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
          {/* User List */}
          <div className="rounded border overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }}>
            <div className="px-4 py-2.5 border-b flex items-center gap-2" style={{ borderColor: '#272E3B' }}>
              <Users size={16} style={{ color: '#007AFF' }} />
              <span className="font-heading text-sm font-semibold flex items-center" style={{ color: '#E8ECF1' }}>Portal Users<InfoTip description="People provisioned to log into the route platform and what they are allowed to see." /></span>
            </div>
            <div className="grid grid-cols-12 gap-2 px-4 py-2 text-[10px] uppercase tracking-wider font-medium border-b" style={{ color: '#6B7A90', borderColor: '#272E3B' }}>
              <div className="col-span-3 flex items-center">Name<InfoTip description="User's display name." /></div><div className="col-span-3 flex items-center">Email<InfoTip description="Login identifier." /></div><div className="col-span-2 flex items-center">Role<InfoTip description="Job function (regulator, distributor admin, retailer viewer, etc.)." /></div><div className="col-span-1 flex items-center">Tier<InfoTip description="Which of the four tiers they sit in — determines broad permissions." /></div><div className="col-span-3 flex items-center">Scope<InfoTip description="Data boundary: the specific distributor, retailer, or region they can see." /></div>
            </div>
            {rbacUsers.map(u => {
              const tierColors = { state_regulator: '#FFD700', distributor_admin: '#00D4AA', retailer_viewer: '#007AFF', manufacturer_viewer: '#8B5CF6', admin: '#FF3B30', operator: '#A3AEBE', engineer: '#F5A623' };
              const perms = u.permissions || {};
              return (
                <div key={u.email} className="grid grid-cols-12 gap-2 px-4 py-2.5 border-b text-xs hover:bg-white/[0.02]" style={{ borderColor: '#272E3B10' }}>
                  <div className="col-span-3 font-medium" style={{ color: '#E8ECF1' }}>{u.name}</div>
                  <div className="col-span-3 font-mono" style={{ color: '#A3AEBE' }}>{u.email}</div>
                  <div className="col-span-2">
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded" style={{ background: `${tierColors[u.role] || '#6B7A90'}15`, color: tierColors[u.role] || '#6B7A90' }}>
                      {u.role?.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <div className="col-span-1 font-mono" style={{ color: tierColors[u.role] }}>{perms.tier || '-'}</div>
                  <div className="col-span-3 text-[10px] font-mono" style={{ color: '#6B7A90' }}>{perms.data_scope || 'full'}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ═══ PERFORMANCE TAB ═══ */}
      {activeTab === 'performance' && perfMetrics && (
        <div className="space-y-4" data-testid="route-performance">
          <div className="flex items-center justify-between">
            <h3 className="font-heading text-lg font-semibold flex items-center" style={{ color: '#E8ECF1' }}>Performance Metrics (Module 8)<InfoTip description="Query latency, database sizes, and capacity projections. Helps operators spot slowdowns before they affect reporting deadlines." /></h3>
            <span className="text-xs font-mono" style={{ color: '#00D4AA' }}>Metrics collected in {perfMetrics.total_metrics_time_ms}ms</span>
          </div>
          {/* Scale Projections */}
          <div className="grid grid-cols-4 gap-3">
            <KPI label="Current Devices" value={perfMetrics.scale_projections?.current_devices} color="#00D4AA" tip="How many machines the platform currently manages." />
            <KPI label="Year 1 Target" value={perfMetrics.scale_projections?.year1_target?.toLocaleString()} color="#007AFF" sub={`${perfMetrics.scale_projections?.year1_events_per_sec} evt/sec`} tip="Planned machine count and expected event throughput at the end of year 1." />
            <KPI label="Year 5 Target" value={perfMetrics.scale_projections?.year5_target?.toLocaleString()} color="#F5A623" sub={`${perfMetrics.scale_projections?.year5_events_per_sec} evt/sec`} tip="Planned machine count and event throughput at the end of year 5." />
            <KPI label="Year 5 Events/yr" value={`${perfMetrics.scale_projections?.year5_annual_events_billions}B`} color="#FF3B30" sub={`${perfMetrics.scale_projections?.year5_meter_rows_billions}B meter rows`} tip="Total gaming events and meter snapshots the system must ingest per year at year-5 scale." />
          </div>
          {/* Query Benchmarks */}
          <div className="rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
            <div className="text-[11px] uppercase tracking-wider mb-3 font-medium flex items-center" style={{ color: '#6B7A90' }}>Query Benchmarks<InfoTip description="How long each critical dashboard query took, versus the target SLA. Green = meeting target." /></div>
            <div className="space-y-2">
              {perfMetrics.benchmarks?.map((b, i) => {
                const target = b.query.includes('NOR') ? 2000 : b.query.includes('exception') ? 500 : 200;
                const ok = b.ms <= target;
                return (
                  <div key={i} className="flex items-center gap-3 px-3 py-2 rounded" style={{ background: '#1A1E2A' }}>
                    <span className="w-3 h-3 rounded-full" style={{ background: ok ? '#00D4AA' : '#FF3B30' }} />
                    <span className="text-xs flex-1" style={{ color: '#A3AEBE' }}>{b.query}</span>
                    <span className="font-mono text-xs" style={{ color: ok ? '#00D4AA' : '#FF3B30' }}>{b.ms}ms</span>
                    <span className="text-[10px] font-mono" style={{ color: '#6B7A90' }}>target: {target}ms</span>
                  </div>
                );
              })}
            </div>
          </div>
          {/* Database Stats */}
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
              <div className="text-[11px] uppercase tracking-wider mb-3 font-medium flex items-center" style={{ color: '#6B7A90' }}>Collection Sizes<InfoTip description="Row counts for each major database collection. Helps track growth pressure." /></div>
              <div className="space-y-1">
                {Object.entries(perfMetrics.db_stats || {}).sort((a, b) => b[1] - a[1]).map(([coll, count]) => (
                  <div key={coll} className="flex items-center justify-between px-2 py-1.5 rounded text-xs" style={{ background: '#1A1E2A' }}>
                    <span className="font-mono" style={{ color: '#A3AEBE' }}>{coll}</span>
                    <span className="font-mono font-bold" style={{ color: '#E8ECF1' }}>{count.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
              <div className="text-[11px] uppercase tracking-wider mb-3 font-medium flex items-center" style={{ color: '#6B7A90' }}>Performance Targets (Module 8 Spec)<InfoTip description="The service-level targets each query must meet to keep the console responsive." /></div>
              <div className="space-y-1.5">
                {Object.entries(perfMetrics.targets || {}).map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between px-2 py-1.5 rounded text-xs" style={{ background: '#1A1E2A' }}>
                    <span style={{ color: '#A3AEBE' }}>{k.replace(/_/g, ' ')}</span>
                    <span className="font-mono" style={{ color: '#00D4AA' }}>{v}ms</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
