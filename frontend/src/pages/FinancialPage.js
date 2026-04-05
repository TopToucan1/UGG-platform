import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import { CurrencyDollar, ArrowUp, ArrowDown, Funnel, Receipt } from '@phosphor-icons/react';
import { AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import InfoTip from '@/components/InfoTip';

const COLORS = ['#00D4AA', '#007AFF', '#F5A623', '#FF3B30', '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16'];
const TYPE_COLORS = { wager: '#007AFF', payout: '#00D4AA', voucher_in: '#F5A623', voucher_out: '#8B5CF6', bill_in: '#06B6D4', jackpot: '#FF3B30', bonus: '#EC4899', handpay: '#FF6B35' };

function Tip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded border px-3 py-2 text-xs" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
      <div className="font-mono mb-1" style={{ color: '#E8ECF1' }}>{label}</div>
      {payload.map((p, i) => <div key={i} style={{ color: p.color }}>{p.name}: ${typeof p.value === 'number' ? p.value.toLocaleString() : p.value}</div>)}
    </div>
  );
}

function StatCard({ label, value, sub, color, icon: Icon, info }) {
  return (
    <div className="rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[11px] font-medium uppercase tracking-wider flex items-center" style={{ color: '#6B7A90' }}>{label}{info && <InfoTip label={label} description={info} />}</span>
        {Icon && <Icon size={18} style={{ color }} />}
      </div>
      <div className="font-mono text-xl font-bold" style={{ color: color || '#E8ECF1' }}>{value}</div>
      {sub && <div className="text-[11px] font-mono mt-1" style={{ color: '#6B7A90' }}>{sub}</div>}
    </div>
  );
}

export default function FinancialPage() {
  const [summary, setSummary] = useState(null);
  const [charts, setCharts] = useState(null);
  const [events, setEvents] = useState([]);
  const [total, setTotal] = useState(0);
  const [typeFilter, setTypeFilter] = useState('');
  const [types, setTypes] = useState([]);

  const fetchData = useCallback(async () => {
    try {
      const [sumRes, chartRes, typeRes] = await Promise.all([
        api.get('/financial/summary'),
        api.get('/financial/charts'),
        api.get('/financial/types'),
      ]);
      setSummary(sumRes.data);
      setCharts(chartRes.data);
      setTypes(typeRes.data.types || []);
    } catch (err) { console.error(err); }
  }, []);

  const fetchEvents = useCallback(async () => {
    const params = new URLSearchParams({ limit: '50' });
    if (typeFilter) params.set('event_type', typeFilter);
    const { data } = await api.get(`/financial?${params}`);
    setEvents(data.events || []);
    setTotal(data.total || 0);
  }, [typeFilter]);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => { fetchEvents(); }, [fetchEvents]);

  const s = summary;
  const fmt = (v) => v != null ? `$${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}` : '--';

  return (
    <div data-testid="financial-dashboard" className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-2xl font-bold tracking-tight flex items-center gap-3" style={{ color: '#E8ECF1' }}>
          <CurrencyDollar size={24} style={{ color: '#00D4AA' }} /> Financial Dashboard
          <InfoTip label="Financial Dashboard" description="Live view of money flowing through your fleet: coin-in, coin-out, jackpots, vouchers, and handpays. Use this to monitor daily revenue and spot unusual activity." />
        </h1>
        <span className="text-xs font-mono" style={{ color: '#6B7A90' }}>{total} transactions</span>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-6 gap-3" data-testid="financial-summary">
        <StatCard label="Coin In" value={fmt(s?.coin_in)} color="#007AFF" icon={ArrowDown} sub={`${s?.totals?.wager?.count || 0} wagers`} info="Total money wagered on machines (the 'handle'). This is the sum of every bet placed, not profit." />
        <StatCard label="Coin Out" value={fmt(s?.coin_out)} color="#FF3B30" icon={ArrowUp} sub="payouts + jackpots" info="Total money paid back to players (payouts, jackpots, handpays). Subtract this from coin-in to get house revenue." />
        <StatCard label="House Hold" value={fmt(s?.house_hold)} color={s?.house_hold >= 0 ? '#00D4AA' : '#FF3B30'} icon={CurrencyDollar} sub={`${s?.hold_percentage || 0}% hold`} info="Net revenue kept by the house (coin-in minus coin-out). Hold % is the share of wagers retained; healthy slots run 5-12%." />
        <StatCard label="Jackpots" value={fmt(s?.totals?.jackpot?.total)} color="#F5A623" sub={`${s?.totals?.jackpot?.count || 0} hits`} info="Total dollars paid out as jackpots and the number of hits in this period. Large spikes affect daily hold." />
        <StatCard label="Voucher In" value={fmt(s?.totals?.voucher_in?.total)} color="#8B5CF6" sub={`${s?.totals?.voucher_in?.count || 0} tickets`} info="TITO tickets redeemed at machines (players cashing prior credits back in). High volume = active session turnover." />
        <StatCard label="Handpays" value={fmt(s?.totals?.handpay?.total)} color="#FF6B35" sub={`${s?.totals?.handpay?.count || 0} events`} info="Wins too large for the machine to pay automatically — staff must hand-pay cash. Typically $1,200+ and triggers W-2G tax reporting." />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-12 gap-4">
        {/* Hourly Revenue */}
        <div className="col-span-7 rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="hourly-revenue-chart">
          <div className="text-[11px] uppercase tracking-wider mb-3 font-medium flex items-center" style={{ color: '#6B7A90' }}>Hourly Revenue (24h)<InfoTip description="Wagers vs payouts hour by hour for the last 24 hours. The gap between the lines is your gross revenue for that hour." /></div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={charts?.hourly_revenue || []}>
              <defs>
                <linearGradient id="wagerG" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#007AFF" stopOpacity={0.3}/><stop offset="95%" stopColor="#007AFF" stopOpacity={0}/></linearGradient>
                <linearGradient id="payoutG" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#00D4AA" stopOpacity={0.3}/><stop offset="95%" stopColor="#00D4AA" stopOpacity={0}/></linearGradient>
              </defs>
              <XAxis dataKey="hour" tick={{ fill: '#6B7A90', fontSize: 10 }} axisLine={false} tickLine={false} interval={3} />
              <YAxis tick={{ fill: '#6B7A90', fontSize: 10 }} axisLine={false} tickLine={false} width={50} tickFormatter={v => `$${(v/1000).toFixed(0)}k`} />
              <Tooltip content={<Tip />} />
              <Area type="monotone" dataKey="wagers" stroke="#007AFF" fill="url(#wagerG)" strokeWidth={2} name="Wagers" />
              <Area type="monotone" dataKey="payouts" stroke="#00D4AA" fill="url(#payoutG)" strokeWidth={2} name="Payouts" />
              <Legend wrapperStyle={{ fontSize: 11, color: '#6B7A90' }} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Revenue by Site */}
        <div className="col-span-2 rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="revenue-by-site">
          <div className="text-[11px] uppercase tracking-wider mb-3 font-medium flex items-center" style={{ color: '#6B7A90' }}>By Site<InfoTip description="Revenue share across your route locations. Helps you spot which sites carry the business and which are under-performing." /></div>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={charts?.by_site || []} cx="50%" cy="50%" innerRadius={40} outerRadius={65} dataKey="value" stroke="none">
                {(charts?.by_site || []).map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip content={<Tip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="space-y-1 mt-1">
            {(charts?.by_site || []).map((s, i) => (
              <div key={s.name} className="flex items-center justify-between text-[10px] font-mono">
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm" style={{ background: COLORS[i] }} /><span style={{ color: '#A3AEBE' }}>{s.name?.split(' ').pop()}</span></span>
                <span style={{ color: '#E8ECF1' }}>${(s.value / 1000).toFixed(1)}k</span>
              </div>
            ))}
          </div>
        </div>

        {/* Top Games */}
        <div className="col-span-3 rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="top-games-chart">
          <div className="text-[11px] uppercase tracking-wider mb-3 font-medium flex items-center" style={{ color: '#6B7A90' }}>Top Games by Wager Volume<InfoTip description="Which game titles are pulling the most coin-in. Use this to decide which games to keep, rotate, or replace." /></div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={(charts?.by_game || []).slice(0, 7)} layout="vertical" barSize={14}>
              <XAxis type="number" tick={{ fill: '#6B7A90', fontSize: 10 }} axisLine={false} tickLine={false} tickFormatter={v => `$${(v/1000).toFixed(0)}k`} />
              <YAxis type="category" dataKey="name" tick={{ fill: '#A3AEBE', fontSize: 10 }} axisLine={false} tickLine={false} width={100} />
              <Tooltip content={<Tip />} />
              <Bar dataKey="wagered" fill="#007AFF" radius={[0, 3, 3, 0]} name="Wagered" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Transaction Ledger */}
      <div className="rounded border overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="financial-ledger">
        <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: '#272E3B' }}>
          <h2 className="font-heading text-sm font-semibold flex items-center gap-2" style={{ color: '#E8ECF1' }}>
            <Receipt size={16} /> Transaction Ledger
            <InfoTip label="Transaction Ledger" description="The raw stream of every financial event on the fleet — wagers, payouts, voucher ins/outs, jackpots, and handpays. Use for reconciliation and spot audits." />
          </h2>
          <div className="flex items-center gap-2">
            <Funnel size={14} style={{ color: '#6B7A90' }} />
            <select data-testid="financial-type-filter" value={typeFilter} onChange={e => setTypeFilter(e.target.value)}
              className="px-2 py-1 rounded text-xs outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}>
              <option value="">All Types</option>
              {types.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
            <InfoTip description="Filter the ledger to a single event type (e.g. only jackpots or only handpays). Useful when you're chasing down a specific kind of transaction." />
          </div>
        </div>
        <div className="grid grid-cols-12 gap-2 px-4 py-2 text-[11px] uppercase tracking-wider font-medium border-b" style={{ color: '#6B7A90', borderColor: '#272E3B' }}>
          <div className="col-span-2 flex items-center">Time<InfoTip description="When the transaction occurred, in local time." /></div><div className="col-span-1 flex items-center">Type<InfoTip description="What kind of event it was: wager, payout, voucher in/out, bill in, jackpot, bonus, or handpay." /></div><div className="col-span-2 flex items-center">Amount<InfoTip description="Dollar value of the transaction. Green amounts are paid out to the player; white amounts are money in." /></div>
          <div className="col-span-2 flex items-center">Device<InfoTip description="The machine (asset/serial reference) where the transaction happened." /></div><div className="col-span-2 flex items-center">Player<InfoTip description="Carded player linked to the event, if any. Anonymous means no player card was inserted." /></div><div className="col-span-2 flex items-center">Game<InfoTip description="Game title played when the transaction occurred." /></div><div className="col-span-1 flex items-center">Denom<InfoTip description="Denomination — the credit value of a single coin on the machine (e.g. $0.01, $0.25, $1.00)." /></div>
        </div>
        <div className="max-h-64 overflow-y-auto">
          {events.map(e => (
            <div key={e.id} className="grid grid-cols-12 gap-2 px-4 py-2 border-b text-xs hover:bg-white/[0.02]" style={{ borderColor: '#272E3B10' }}>
              <div className="col-span-2 font-mono" style={{ color: '#6B7A90' }}>{new Date(e.occurred_at).toLocaleString()}</div>
              <div className="col-span-1">
                <span className="font-mono text-[10px] px-1.5 py-0.5 rounded" style={{ background: `${TYPE_COLORS[e.event_type] || '#6B7A90'}20`, color: TYPE_COLORS[e.event_type] || '#6B7A90' }}>{e.event_type}</span>
              </div>
              <div className="col-span-2 font-mono font-medium" style={{ color: ['payout', 'jackpot', 'handpay', 'bonus'].includes(e.event_type) ? '#00D4AA' : '#E8ECF1' }}>
                ${e.amount?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </div>
              <div className="col-span-2 font-mono" style={{ color: '#A3AEBE' }}>{e.device_ref}</div>
              <div className="col-span-2" style={{ color: e.player_name ? '#E8ECF1' : '#6B7A90' }}>{e.player_name || 'Anonymous'}</div>
              <div className="col-span-2 truncate" style={{ color: '#A3AEBE' }}>{e.game_title}</div>
              <div className="col-span-1 font-mono" style={{ color: '#6B7A90' }}>${e.denomination}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
