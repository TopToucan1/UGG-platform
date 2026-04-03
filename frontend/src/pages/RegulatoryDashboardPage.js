import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import {
  Scales, ShieldCheck, Warning, CurrencyDollar, Buildings, Desktop,
  Check, X, CaretRight, Receipt, WifiHigh, FileText, Gauge, MapPin,
  SealCheck, Pulse
} from '@phosphor-icons/react';
import { AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const COLORS = ['#00D4AA', '#007AFF', '#F5A623', '#FF3B30', '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16'];
const SEV = { CRITICAL: '#FF3B30', WARNING: '#F5A623', INFO: '#007AFF' };

function Tip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded border px-3 py-2 text-xs" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
      <div className="font-mono mb-1" style={{ color: '#E8ECF1' }}>{label}</div>
      {payload.map((p, i) => <div key={i} style={{ color: p.color }}>{p.name}: {typeof p.value === 'number' ? (p.name.includes('$') || p.name.includes('NOR') || p.name.includes('Tax') || p.name.includes('Coin') ? `$${p.value.toLocaleString()}` : p.value.toLocaleString()) : p.value}</div>)}
    </div>
  );
}

function ScoreGauge({ score, size = 100 }) {
  const color = score >= 90 ? '#00D4AA' : score >= 70 ? '#F5A623' : '#FF3B30';
  const circumference = 2 * Math.PI * 38;
  const offset = circumference - (score / 100) * circumference;
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="38" fill="none" stroke="#272E3B" strokeWidth="8" />
        <circle cx="50" cy="50" r="38" fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={circumference} strokeDashoffset={offset}
          strokeLinecap="round" transform="rotate(-90 50 50)"
          style={{ transition: 'stroke-dashoffset 1s ease' }} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-mono text-xl font-black" style={{ color }}>{score}</span>
        <span className="text-[8px] uppercase tracking-widest" style={{ color: '#6B7A90' }}>score</span>
      </div>
    </div>
  );
}

function KPI({ label, value, sub, color, icon: Icon, large }) {
  return (
    <div className="rounded border p-3" style={{ background: '#12151C', borderColor: '#272E3B' }}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-[9px] uppercase tracking-widest font-medium" style={{ color: '#6B7A90' }}>{label}</span>
        {Icon && <Icon size={14} style={{ color }} />}
      </div>
      <div className={`font-mono ${large ? 'text-2xl' : 'text-lg'} font-bold`} style={{ color: color || '#E8ECF1' }}>{value}</div>
      {sub && <div className="text-[10px] font-mono mt-0.5" style={{ color: '#6B7A90' }}>{sub}</div>}
    </div>
  );
}

const fmt = (v) => v != null ? `$${Number(v).toLocaleString()}` : '--';

export default function RegulatoryDashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDist, setSelectedDist] = useState(null);
  const [distDetail, setDistDetail] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const { data: d } = await api.get('/route/advanced/regulatory/dashboard');
      setData(d);
      setError(null);
    } catch (err) {
      setError(err.response?.status === 403 ? 'Access denied — requires State Regulator or Admin role' : err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); const iv = setInterval(fetchData, 60000); return () => clearInterval(iv); }, [fetchData]);

  const selectDistributor = async (dist) => {
    setSelectedDist(dist);
    try {
      const { data: d } = await api.get(`/route/advanced/regulatory/distributor/${dist.distributor_id}`);
      setDistDetail(d);
    } catch {}
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: '#00D4AA', borderTopColor: 'transparent' }} /></div>;
  if (error) return <div className="rounded border p-8 text-center" style={{ background: '#12151C', borderColor: '#FF3B3040' }}><Scales size={40} className="mx-auto mb-3" style={{ color: '#FF3B30' }} /><div className="text-sm" style={{ color: '#FF3B30' }}>{error}</div></div>;
  if (!data) return null;

  const d = data;
  const sc = d.overall_compliance_score;

  return (
    <div data-testid="regulatory-dashboard" className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Scales size={26} style={{ color: '#FFD700' }} />
          <div>
            <h1 className="font-heading text-2xl font-bold tracking-tight" style={{ color: '#E8ECF1' }}>Regulatory Compliance Dashboard</h1>
            <span className="text-xs" style={{ color: '#6B7A90' }}>State-Level Estate Overview — All Distributors</span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <ScoreGauge score={sc} size={64} />
          <div>
            <div className="text-[9px] uppercase tracking-widest" style={{ color: '#6B7A90' }}>Overall Compliance</div>
            <div className="font-mono text-lg font-bold" style={{ color: sc >= 90 ? '#00D4AA' : sc >= 70 ? '#F5A623' : '#FF3B30' }}>{sc}/100</div>
          </div>
        </div>
      </div>

      {/* KPI Strip */}
      <div className="grid grid-cols-8 gap-2" data-testid="reg-kpi-strip">
        <KPI label="Devices" value={d.estate?.devices} color="#00D4AA" icon={Desktop} sub={`${d.estate?.online} online`} />
        <KPI label="Distributors" value={d.estate?.distributors} color="#8B5CF6" icon={Buildings} />
        <KPI label="Retailers" value={d.estate?.retailers} color="#007AFF" icon={MapPin} />
        <KPI label="30d NOR" value={fmt(d.revenue?.grand_nor)} color="#00D4AA" icon={CurrencyDollar} />
        <KPI label="30d Tax" value={fmt(d.revenue?.grand_tax)} color="#F5A623" icon={Receipt} />
        <KPI label="Integrity" value={`${d.integrity_compliance?.pass_rate}%`} color={d.integrity_compliance?.pass_rate >= 99 ? '#00D4AA' : '#FF3B30'} icon={ShieldCheck} />
        <KPI label="Statutory" value={`${d.statutory_compliance?.rate}%`} color={d.statutory_compliance?.rate >= 99 ? '#00D4AA' : '#F5A623'} icon={SealCheck} />
        <KPI label="Exceptions" value={d.exceptions?.total_active} color="#FF3B30" icon={Warning} sub={`${d.exceptions?.critical} critical`} />
      </div>

      {/* Row 2: Revenue Trend + Compliance Breakdown */}
      <div className="grid grid-cols-12 gap-4">
        {/* Revenue Trend */}
        <div className="col-span-8 rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="reg-revenue-chart">
          <div className="text-[11px] uppercase tracking-wider mb-3 font-medium" style={{ color: '#6B7A90' }}>State Revenue & Tax Collection (30 Days)</div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={d.revenue?.daily_trend || []}>
              <defs>
                <linearGradient id="regNorG" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#00D4AA" stopOpacity={0.3}/><stop offset="95%" stopColor="#00D4AA" stopOpacity={0}/></linearGradient>
                <linearGradient id="regTaxG" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#F5A623" stopOpacity={0.3}/><stop offset="95%" stopColor="#F5A623" stopOpacity={0}/></linearGradient>
              </defs>
              <XAxis dataKey="date" tick={{ fill: '#6B7A90', fontSize: 9 }} axisLine={false} tickLine={false} interval={4} />
              <YAxis tick={{ fill: '#6B7A90', fontSize: 9 }} axisLine={false} tickLine={false} width={50} tickFormatter={v => `$${(v/1000).toFixed(0)}k`} />
              <Tooltip content={<Tip />} />
              <Area type="monotone" dataKey="coin_in" stroke="#007AFF" fill="none" strokeWidth={1} strokeDasharray="3 3" name="Coin In" />
              <Area type="monotone" dataKey="nor" stroke="#00D4AA" fill="url(#regNorG)" strokeWidth={2} name="NOR" />
              <Area type="monotone" dataKey="tax" stroke="#F5A623" fill="url(#regTaxG)" strokeWidth={1.5} name="Tax" />
              <Legend wrapperStyle={{ fontSize: 10 }} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Right: Compliance Gauges */}
        <div className="col-span-4 space-y-3">
          {/* Statutory Enrichment */}
          <div className="rounded border p-3" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="reg-statutory-gauge">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] uppercase tracking-wider font-medium" style={{ color: '#6B7A90' }}>Statutory Field Coverage</span>
              <span className="font-mono text-sm font-bold" style={{ color: d.statutory_compliance?.rate >= 99 ? '#00D4AA' : '#F5A623' }}>{d.statutory_compliance?.rate}%</span>
            </div>
            <div className="h-2 rounded-full overflow-hidden" style={{ background: '#272E3B' }}>
              <div className="h-full rounded-full transition-all" style={{ width: `${d.statutory_compliance?.rate || 0}%`, background: d.statutory_compliance?.rate >= 99 ? '#00D4AA' : d.statutory_compliance?.rate >= 90 ? '#F5A623' : '#FF3B30' }} />
            </div>
            <div className="text-[9px] font-mono mt-1" style={{ color: '#6B7A90' }}>{d.statutory_compliance?.enriched?.toLocaleString()} / {d.statutory_compliance?.total_events?.toLocaleString()} events</div>
          </div>
          {/* Integrity */}
          <div className="rounded border p-3" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="reg-integrity-gauge">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] uppercase tracking-wider font-medium" style={{ color: '#6B7A90' }}>Software Integrity</span>
              <span className="font-mono text-sm font-bold" style={{ color: d.integrity_compliance?.pass_rate >= 99 ? '#00D4AA' : '#FF3B30' }}>{d.integrity_compliance?.pass_rate}%</span>
            </div>
            <div className="h-2 rounded-full overflow-hidden" style={{ background: '#272E3B' }}>
              <div className="h-full rounded-full" style={{ width: `${d.integrity_compliance?.pass_rate || 0}%`, background: d.integrity_compliance?.pass_rate >= 99 ? '#00D4AA' : '#FF3B30' }} />
            </div>
            <div className="text-[9px] font-mono mt-1" style={{ color: '#6B7A90' }}>{d.integrity_compliance?.passed} pass / {d.integrity_compliance?.failed} fail of {d.integrity_compliance?.total_checks}</div>
          </div>
          {/* EFT */}
          <div className="rounded border p-3" style={{ background: '#12151C', borderColor: '#272E3B' }}>
            <div className="text-[10px] uppercase tracking-wider font-medium mb-2" style={{ color: '#6B7A90' }}>EFT Sweep Status</div>
            <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
              <div><span style={{ color: '#6B7A90' }}>Files: </span><span style={{ color: '#E8ECF1' }}>{d.eft_compliance?.total_files}</span></div>
              <div><span style={{ color: '#6B7A90' }}>Transmitted: </span><span style={{ color: '#00D4AA' }}>{d.eft_compliance?.transmitted}</span></div>
              <div><span style={{ color: '#6B7A90' }}>NACHA OK: </span><span style={{ color: '#00D4AA' }}>{d.eft_compliance?.nacha_compliant}</span></div>
              <div><span style={{ color: '#6B7A90' }}>Total Swept: </span><span style={{ color: '#E8ECF1' }}>${((d.eft_compliance?.total_swept_cents || 0) / 100).toLocaleString()}</span></div>
            </div>
          </div>
          {/* Buffer Risk */}
          <div className="rounded border p-3" style={{ background: '#12151C', borderColor: d.buffer_risk?.agents_offline > 0 ? '#FF3B3030' : '#272E3B' }}>
            <div className="text-[10px] uppercase tracking-wider font-medium mb-2" style={{ color: '#6B7A90' }}>Agent Connectivity</div>
            <div className="flex items-center gap-3 text-[10px] font-mono">
              <span style={{ color: '#00D4AA' }}>{d.buffer_risk?.agents_online} online</span>
              <span style={{ color: d.buffer_risk?.agents_offline > 0 ? '#FF3B30' : '#6B7A90' }}>{d.buffer_risk?.agents_offline} offline</span>
              <span style={{ color: d.buffer_risk?.pending_events > 0 ? '#F5A623' : '#6B7A90' }}>{d.buffer_risk?.pending_events?.toLocaleString()} pending</span>
            </div>
          </div>
        </div>
      </div>

      {/* Row 3: Distributor Compliance Table + Exception & County Breakdown */}
      <div className="grid grid-cols-12 gap-4">
        {/* Distributor Compliance Table */}
        <div className="col-span-8 rounded border overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="reg-distributor-table">
          <div className="px-4 py-2.5 border-b flex items-center gap-2" style={{ borderColor: '#272E3B' }}>
            <Buildings size={16} style={{ color: '#8B5CF6' }} />
            <span className="font-heading text-sm font-semibold" style={{ color: '#E8ECF1' }}>Distributor Compliance Matrix</span>
          </div>
          <div className="grid grid-cols-12 gap-1 px-4 py-2 text-[9px] uppercase tracking-wider font-medium border-b" style={{ color: '#6B7A90', borderColor: '#272E3B' }}>
            <div className="col-span-2">Distributor</div><div className="col-span-1">License</div><div className="col-span-1">Devices</div>
            <div className="col-span-1">NOR</div><div className="col-span-1">Tax</div><div className="col-span-1">Hold%</div>
            <div className="col-span-1">Integrity</div><div className="col-span-1">Exceptions</div><div className="col-span-2">Score</div><div className="col-span-1"></div>
          </div>
          {d.distributor_compliance?.map((dc, i) => (
            <button key={dc.distributor_id} data-testid={`reg-dist-row-${dc.distributor_id}`}
              onClick={() => selectDistributor(dc)}
              className="w-full grid grid-cols-12 gap-1 px-4 py-2.5 border-b text-xs text-left hover:bg-white/[0.02] transition-colors"
              style={{ borderColor: '#272E3B10', background: selectedDist?.distributor_id === dc.distributor_id ? 'rgba(0,212,170,0.04)' : 'transparent' }}>
              <div className="col-span-2 font-medium" style={{ color: '#E8ECF1' }}>{dc.distributor_name}</div>
              <div className="col-span-1 font-mono text-[10px]" style={{ color: '#6B7A90' }}>{dc.state_license}</div>
              <div className="col-span-1 font-mono" style={{ color: '#A3AEBE' }}>{dc.device_count}</div>
              <div className="col-span-1 font-mono" style={{ color: '#00D4AA' }}>${(dc.nor / 1000).toFixed(0)}k</div>
              <div className="col-span-1 font-mono" style={{ color: '#F5A623' }}>${(dc.tax_collected / 1000).toFixed(0)}k</div>
              <div className="col-span-1 font-mono" style={{ color: '#E8ECF1' }}>{dc.hold_pct}%</div>
              <div className="col-span-1">
                <span className="text-[10px] font-mono px-1 py-0.5 rounded" style={{ background: dc.integrity_pass_rate >= 99 ? 'rgba(0,212,170,0.1)' : 'rgba(255,59,48,0.1)', color: dc.integrity_pass_rate >= 99 ? '#00D4AA' : '#FF3B30' }}>
                  {dc.integrity_pass_rate}%
                </span>
              </div>
              <div className="col-span-1 font-mono" style={{ color: dc.active_exceptions > 0 ? '#FF3B30' : '#00D4AA' }}>{dc.active_exceptions}</div>
              <div className="col-span-2">
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: '#272E3B' }}>
                    <div className="h-full rounded-full" style={{ width: `${dc.compliance_score}%`, background: dc.compliance_score >= 90 ? '#00D4AA' : dc.compliance_score >= 70 ? '#F5A623' : '#FF3B30' }} />
                  </div>
                  <span className="font-mono text-[10px] w-8 text-right" style={{ color: dc.compliance_score >= 90 ? '#00D4AA' : dc.compliance_score >= 70 ? '#F5A623' : '#FF3B30' }}>{dc.compliance_score}</span>
                </div>
              </div>
              <div className="col-span-1 flex justify-end"><CaretRight size={12} style={{ color: '#6B7A90' }} /></div>
            </button>
          ))}
        </div>

        {/* Right: County + Exception breakdown */}
        <div className="col-span-4 space-y-3">
          {/* Events by County */}
          <div className="rounded border p-3" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="reg-county-breakdown">
            <div className="text-[10px] uppercase tracking-wider font-medium mb-2" style={{ color: '#6B7A90' }}>Events by County</div>
            <div className="space-y-1">
              {d.statutory_compliance?.by_county?.map((c, i) => (
                <div key={c.county} className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
                  <span className="text-xs flex-1" style={{ color: '#A3AEBE' }}>{c.county}</span>
                  <span className="font-mono text-xs" style={{ color: '#E8ECF1' }}>{c.events?.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>
          {/* Exception Types */}
          <div className="rounded border p-3" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="reg-exc-types">
            <div className="text-[10px] uppercase tracking-wider font-medium mb-2" style={{ color: '#6B7A90' }}>Active Exceptions by Type</div>
            <div className="space-y-1">
              {d.exceptions?.by_type?.map((e, i) => (
                <div key={e.type} className="flex items-center justify-between px-2 py-1 rounded text-[10px]" style={{ background: '#1A1E2A' }}>
                  <span className="font-mono" style={{ color: '#A3AEBE' }}>{e.type.replace(/_/g, ' ')}</span>
                  <span className="font-mono font-bold" style={{ color: COLORS[i % COLORS.length] }}>{e.count}</span>
                </div>
              ))}
            </div>
          </div>
          {/* Integrity by Trigger */}
          <div className="rounded border p-3" style={{ background: '#12151C', borderColor: '#272E3B' }}>
            <div className="text-[10px] uppercase tracking-wider font-medium mb-2" style={{ color: '#6B7A90' }}>Integrity by Trigger</div>
            <div className="space-y-1">
              {d.integrity_compliance?.by_trigger?.map(t => (
                <div key={t.trigger} className="flex items-center justify-between px-2 py-1 rounded text-[10px] font-mono" style={{ background: '#1A1E2A' }}>
                  <span style={{ color: '#A3AEBE' }}>{t.trigger}</span>
                  <span><span style={{ color: '#00D4AA' }}>{t.passed}</span> / <span style={{ color: t.failed > 0 ? '#FF3B30' : '#6B7A90' }}>{t.failed}</span></span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Row 4: Failed Integrity Checks (if any) */}
      {d.integrity_compliance?.failed_checks?.length > 0 && (
        <div className="rounded border overflow-hidden" style={{ background: '#12151C', borderColor: '#FF3B3030' }} data-testid="reg-failed-integrity">
          <div className="px-4 py-2.5 border-b flex items-center gap-2" style={{ borderColor: '#272E3B', background: 'rgba(255,59,48,0.03)' }}>
            <Warning size={16} style={{ color: '#FF3B30' }} />
            <span className="font-heading text-sm font-semibold" style={{ color: '#FF3B30' }}>Integrity Violations Requiring Investigation</span>
          </div>
          <div className="grid grid-cols-12 gap-2 px-4 py-2 text-[9px] uppercase tracking-wider font-medium border-b" style={{ color: '#6B7A90', borderColor: '#272E3B' }}>
            <div className="col-span-2">Time</div><div className="col-span-2">Device</div><div className="col-span-1">Trigger</div><div className="col-span-2">Software</div><div className="col-span-2">Expected Sig</div><div className="col-span-2">Reported Sig</div><div className="col-span-1">Action</div>
          </div>
          {d.integrity_compliance.failed_checks.map(c => (
            <div key={c.id} className="grid grid-cols-12 gap-2 px-4 py-2 border-b text-xs" style={{ borderColor: '#272E3B10', background: 'rgba(255,59,48,0.02)' }}>
              <div className="col-span-2 font-mono" style={{ color: '#6B7A90' }}>{new Date(c.check_time).toLocaleString()}</div>
              <div className="col-span-2 font-mono font-medium" style={{ color: '#E8ECF1' }}>{c.device_ref}</div>
              <div className="col-span-1 font-mono text-[10px]" style={{ color: '#A3AEBE' }}>{c.trigger}</div>
              <div className="col-span-2 font-mono text-[10px]" style={{ color: '#6B7A90' }}>{c.software_version}</div>
              <div className="col-span-2 font-mono text-[10px] truncate" style={{ color: '#00D4AA' }}>{c.expected_signature?.slice(0, 16)}...</div>
              <div className="col-span-2 font-mono text-[10px] truncate" style={{ color: '#FF3B30' }}>{c.reported_signature?.slice(0, 16)}...</div>
              <div className="col-span-1 text-[10px] font-mono" style={{ color: '#FF3B30' }}>{c.action_taken}</div>
            </div>
          ))}
        </div>
      )}

      {/* Distributor Detail Drawer */}
      {selectedDist && distDetail && (
        <div className="rounded border p-4 space-y-3" style={{ background: '#12151C', borderColor: '#8B5CF630' }} data-testid="reg-dist-detail">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-heading text-base font-semibold" style={{ color: '#E8ECF1' }}>{selectedDist.distributor_name}</h3>
              <span className="text-xs font-mono" style={{ color: '#6B7A90' }}>License: {selectedDist.state_license} | {distDetail.device_count} devices | {distDetail.retailer_count} retailers</span>
            </div>
            <button onClick={() => { setSelectedDist(null); setDistDetail(null); }} className="text-xs px-3 py-1 rounded" style={{ color: '#6B7A90', border: '1px solid #272E3B' }}>Close</button>
          </div>
          {/* Mini NOR Trend */}
          <div>
            <div className="text-[10px] uppercase tracking-wider mb-2" style={{ color: '#6B7A90' }}>30-Day Revenue Trend</div>
            <ResponsiveContainer width="100%" height={120}>
              <AreaChart data={distDetail.nor_trend || []}>
                <XAxis dataKey="date" tick={{ fill: '#6B7A90', fontSize: 8 }} axisLine={false} tickLine={false} interval={5} />
                <YAxis tick={{ fill: '#6B7A90', fontSize: 8 }} axisLine={false} tickLine={false} width={40} tickFormatter={v => `$${(v/1000).toFixed(0)}k`} />
                <Area type="monotone" dataKey="nor" stroke="#00D4AA" fill="rgba(0,212,170,0.1)" strokeWidth={1.5} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          {/* Active Exceptions for this distributor */}
          {distDetail.active_exceptions?.length > 0 && (
            <div>
              <div className="text-[10px] uppercase tracking-wider mb-2" style={{ color: '#FF3B30' }}>{distDetail.active_exceptions.length} Active Exceptions</div>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {distDetail.active_exceptions.map(e => (
                  <div key={e.id} className="flex items-center gap-2 px-2 py-1.5 rounded text-[10px] font-mono" style={{ background: '#1A1E2A' }}>
                    <span className="w-1.5 h-1.5 rounded-full" style={{ background: SEV[e.severity] }} />
                    <span style={{ color: '#A3AEBE' }}>{e.type.replace(/_/g, ' ')}</span>
                    <span style={{ color: '#E8ECF1' }}>{e.device_ref}</span>
                    <span className="ml-auto" style={{ color: '#6B7A90' }}>{e.site_name}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="text-[9px] font-mono text-right" style={{ color: '#6B7A90' }}>
        Report generated: {new Date(d.generated_at).toLocaleString()} UTC
      </div>
    </div>
  );
}
