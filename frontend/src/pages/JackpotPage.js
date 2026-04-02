import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import { Trophy, CurrencyDollar, Lightning, Funnel, ArrowUp } from '@phosphor-icons/react';
import { BarChart, Bar, AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const COLORS = ['#FFD700', '#00D4AA', '#007AFF', '#F5A623', '#FF3B30', '#8B5CF6', '#EC4899', '#06B6D4'];
const STATUS_COLORS = { active: '#00D4AA', hit_pending: '#F5A623', suspended: '#FF3B30' };
const TYPE_COLORS = { standalone: '#007AFF', linked: '#00D4AA', wide_area: '#8B5CF6' };

function Tip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded border px-3 py-2 text-xs" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
      <div className="font-mono mb-1" style={{ color: '#E8ECF1' }}>{label}</div>
      {payload.map((p, i) => <div key={i} style={{ color: p.color }}>{p.name}: {typeof p.value === 'number' ? `$${p.value.toLocaleString()}` : p.value}</div>)}
    </div>
  );
}

function fmt(v) { return v != null ? `$${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}` : '--'; }

export default function JackpotPage() {
  const [jackpots, setJackpots] = useState([]);
  const [summary, setSummary] = useState(null);
  const [charts, setCharts] = useState(null);
  const [history, setHistory] = useState([]);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');

  const fetchData = useCallback(async () => {
    const [jpRes, sumRes, chartRes, histRes] = await Promise.all([
      api.get(`/jackpots${statusFilter ? `?status=${statusFilter}` : ''}`),
      api.get('/jackpots/summary'),
      api.get('/jackpots/charts'),
      api.get('/jackpots/history?limit=30'),
    ]);
    setJackpots(jpRes.data.jackpots || []);
    setSummary(sumRes.data);
    setCharts(chartRes.data);
    setHistory(histRes.data.hits || []);
  }, [statusFilter]);

  useEffect(() => { fetchData(); const iv = setInterval(fetchData, 30000); return () => clearInterval(iv); }, [fetchData]);

  const selectJP = async (jp) => {
    setSelected(jp);
    const { data } = await api.get(`/jackpots/${jp.id}`);
    setDetail(data);
  };

  const sm = summary;

  return (
    <div data-testid="jackpot-monitor" className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-2xl font-bold tracking-tight flex items-center gap-3" style={{ color: '#E8ECF1' }}>
          <Trophy size={24} style={{ color: '#FFD700' }} /> Progressive Jackpots
        </h1>
        <div className="flex items-center gap-3">
          <Funnel size={14} style={{ color: '#6B7A90' }} />
          <select data-testid="jp-status-filter" value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="px-3 py-1.5 rounded text-xs outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}>
            <option value="">All</option><option value="active">Active</option><option value="hit_pending">Hit Pending</option><option value="suspended">Suspended</option>
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-5 gap-3" data-testid="jackpot-summary">
        <div className="rounded border p-3" style={{ background: '#12151C', borderColor: '#272E3B' }}>
          <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: '#6B7A90' }}>Total Liability</div>
          <div className="font-mono text-lg font-bold" style={{ color: '#FFD700' }}>{fmt(sm?.total_current_liability)}</div>
          <div className="text-[10px] font-mono" style={{ color: '#6B7A90' }}>{sm?.total_jackpots || 0} jackpots</div>
        </div>
        <div className="rounded border p-3" style={{ background: '#12151C', borderColor: '#272E3B' }}>
          <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: '#6B7A90' }}>Total Paid Out</div>
          <div className="font-mono text-lg font-bold" style={{ color: '#00D4AA' }}>{fmt(sm?.total_paid_out)}</div>
          <div className="text-[10px] font-mono" style={{ color: '#6B7A90' }}>{sm?.total_hits || 0} total hits</div>
        </div>
        <div className="rounded border p-3" style={{ background: '#12151C', borderColor: '#272E3B' }}>
          <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: '#6B7A90' }}>Active</div>
          <div className="font-mono text-lg font-bold" style={{ color: '#00D4AA' }}>{sm?.active || 0}</div>
        </div>
        <div className="rounded border p-3" style={{ background: '#12151C', borderColor: '#272E3B' }}>
          <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: '#6B7A90' }}>Hit Pending</div>
          <div className="font-mono text-lg font-bold" style={{ color: '#F5A623' }}>{sm?.hit_pending || 0}</div>
        </div>
        <div className="rounded border p-3" style={{ background: '#12151C', borderColor: '#272E3B' }}>
          <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: '#6B7A90' }}>Linked Devices</div>
          <div className="font-mono text-lg font-bold" style={{ color: '#007AFF' }}>{sm?.total_linked_devices || 0}</div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-8 rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="jp-top-chart">
          <div className="text-[11px] uppercase tracking-wider mb-3 font-medium" style={{ color: '#6B7A90' }}>Top Jackpots by Current Amount</div>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={charts?.top_jackpots || []} barSize={24}>
              <XAxis dataKey="name" tick={{ fill: '#6B7A90', fontSize: 9 }} axisLine={false} tickLine={false} interval={0} angle={-20} textAnchor="end" height={50} />
              <YAxis tick={{ fill: '#6B7A90', fontSize: 10 }} axisLine={false} tickLine={false} width={60} tickFormatter={v => `$${(v/1000).toFixed(0)}k`} />
              <Tooltip content={<Tip />} />
              <Bar dataKey="current_amount" name="Current" radius={[3, 3, 0, 0]}>
                {(charts?.top_jackpots || []).map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="col-span-4 rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="jp-hits-chart">
          <div className="text-[11px] uppercase tracking-wider mb-3 font-medium" style={{ color: '#6B7A90' }}>Daily Hits (30d)</div>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={(charts?.daily_hits || []).slice(-14)}>
              <defs><linearGradient id="hitG" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#FFD700" stopOpacity={0.3}/><stop offset="95%" stopColor="#FFD700" stopOpacity={0}/></linearGradient></defs>
              <XAxis dataKey="date" tick={{ fill: '#6B7A90', fontSize: 9 }} axisLine={false} tickLine={false} interval={2} />
              <YAxis tick={{ fill: '#6B7A90', fontSize: 9 }} axisLine={false} tickLine={false} width={20} />
              <Tooltip content={<Tip />} />
              <Area type="monotone" dataKey="hits" stroke="#FFD700" fill="url(#hitG)" strokeWidth={2} name="Hits" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Jackpot List + History */}
      <div className="grid grid-cols-12 gap-4" style={{ height: 'calc(100vh - 500px)' }}>
        {/* Jackpot Cards */}
        <div className="col-span-7 overflow-y-auto space-y-2" data-testid="jackpot-list">
          {jackpots.map(jp => {
            const pct = ((jp.current_amount - jp.base_amount) / (jp.ceiling_amount - jp.base_amount) * 100);
            return (
              <button key={jp.id} data-testid={`jp-card-${jp.id}`} onClick={() => selectJP(jp)}
                className="w-full text-left rounded border p-4 transition-all duration-150 hover:-translate-y-[1px]"
                style={{ background: selected?.id === jp.id ? 'rgba(255,215,0,0.04)' : '#12151C', borderColor: selected?.id === jp.id ? '#FFD70040' : '#272E3B' }}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Trophy size={16} style={{ color: '#FFD700' }} />
                    <span className="font-heading text-sm font-semibold" style={{ color: '#E8ECF1' }}>{jp.name}</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded capitalize" style={{ background: `${TYPE_COLORS[jp.type]}20`, color: TYPE_COLORS[jp.type] }}>{jp.type}</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded capitalize" style={{ background: `${STATUS_COLORS[jp.status]}20`, color: STATUS_COLORS[jp.status] }}>{jp.status}</span>
                  </div>
                  <span className="text-xs" style={{ color: '#6B7A90' }}>{jp.site_name}</span>
                </div>
                <div className="font-mono text-xl font-bold mb-2" style={{ color: '#FFD700' }}>{fmt(jp.current_amount)}</div>
                {/* Progress bar: base to ceiling */}
                <div className="h-2 rounded-full overflow-hidden mb-2" style={{ background: '#272E3B' }}>
                  <div className="h-full rounded-full transition-all" style={{ width: `${Math.min(pct, 100)}%`, background: pct > 80 ? '#FF3B30' : pct > 50 ? '#F5A623' : '#00D4AA' }} />
                </div>
                <div className="flex justify-between text-[10px] font-mono">
                  <span style={{ color: '#6B7A90' }}>Base: {fmt(jp.base_amount)}</span>
                  <span style={{ color: '#6B7A90' }}>{jp.linked_device_count} devices | {jp.contribution_rate}% rate</span>
                  <span style={{ color: '#6B7A90' }}>Ceiling: {fmt(jp.ceiling_amount)}</span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Hit History */}
        <div className="col-span-5 rounded border flex flex-col overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }}>
          <div className="px-4 py-2.5 border-b flex items-center gap-2" style={{ borderColor: '#272E3B' }}>
            <Lightning size={16} style={{ color: '#FFD700' }} />
            <span className="font-heading text-sm font-semibold" style={{ color: '#E8ECF1' }}>
              {selected ? `Hits — ${selected.name}` : 'Recent Hits'}
            </span>
          </div>
          <div className="flex-1 overflow-y-auto" data-testid="hit-history">
            {(detail?.recent_hits || history).map(h => (
              <div key={h.id} className="px-4 py-2.5 border-b hover:bg-white/[0.02]" style={{ borderColor: '#272E3B10' }}>
                <div className="flex items-center justify-between">
                  <span className="font-heading text-sm font-semibold" style={{ color: '#FFD700' }}>{fmt(h.hit_amount)}</span>
                  <span className="text-[10px] font-mono" style={{ color: '#6B7A90' }}>{new Date(h.hit_at).toLocaleString()}</span>
                </div>
                <div className="flex items-center gap-3 text-[10px] font-mono mt-1">
                  <span style={{ color: '#A3AEBE' }}>{h.jackpot_name}</span>
                  {h.device_ref && <span style={{ color: '#6B7A90' }}>{h.device_ref}</span>}
                  {h.player_id && <span style={{ color: '#007AFF' }}>{h.player_id}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
