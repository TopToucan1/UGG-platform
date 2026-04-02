import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import { UserCircle, Users, Clock, GameController, Trophy, CurrencyDollar, Funnel, X, Star } from '@phosphor-icons/react';
import { BarChart, Bar, AreaChart, Area, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const TIER_COLORS = { Diamond: '#B9F2FF', Platinum: '#C0C0C0', Gold: '#FFD700', Silver: '#A8A8A8', Bronze: '#CD7F32' };
const COLORS = ['#00D4AA', '#007AFF', '#F5A623', '#FF3B30', '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16', '#FF6B35', '#10B981'];

function Tip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded border px-3 py-2 text-xs" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
      <div className="font-mono mb-1" style={{ color: '#E8ECF1' }}>{label}</div>
      {payload.map((p, i) => <div key={i} style={{ color: p.color }}>{p.name}: {p.value}</div>)}
    </div>
  );
}

function StatCard({ label, value, sub, color }) {
  return (
    <div className="rounded border p-3" style={{ background: '#12151C', borderColor: '#272E3B' }}>
      <div className="text-[10px] font-medium uppercase tracking-wider mb-1" style={{ color: '#6B7A90' }}>{label}</div>
      <div className="font-mono text-lg font-bold" style={{ color: color || '#E8ECF1' }}>{value}</div>
      {sub && <div className="text-[10px] font-mono mt-0.5" style={{ color: '#6B7A90' }}>{sub}</div>}
    </div>
  );
}

function TierBadge({ tier }) {
  return (
    <span className="inline-flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded" style={{ background: `${TIER_COLORS[tier] || '#6B7A90'}20`, color: TIER_COLORS[tier] || '#6B7A90' }}>
      <Star size={10} weight="fill" /> {tier}
    </span>
  );
}

export default function PlayerSessionsPage() {
  const [summary, setSummary] = useState(null);
  const [charts, setCharts] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [total, setTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [sumRes, chartRes] = await Promise.all([
        api.get('/players/summary'),
        api.get('/players/charts'),
      ]);
      setSummary(sumRes.data);
      setCharts(chartRes.data);
    } catch (err) { console.error(err); }
  }, []);

  const fetchSessions = useCallback(async () => {
    const params = new URLSearchParams({ limit: '60' });
    if (statusFilter) params.set('status', statusFilter);
    const { data } = await api.get(`/players/sessions?${params}`);
    setSessions(data.sessions || []);
    setTotal(data.total || 0);
  }, [statusFilter]);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => { fetchSessions(); }, [fetchSessions]);

  const selectSession = async (s) => {
    setSelected(s);
    try {
      const { data } = await api.get(`/players/sessions/${s.id}`);
      setDetail(data);
    } catch (err) { console.error(err); }
  };

  const sm = summary;
  const fmt = (v) => v != null ? `$${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}` : '--';

  return (
    <div data-testid="player-sessions" className="flex gap-0 h-full -m-6">
      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden" style={{ background: '#0A0C10' }}>
        {/* Header */}
        <div className="px-6 pt-6 pb-4 flex-shrink-0">
          <div className="flex items-center justify-between mb-4">
            <h1 className="font-heading text-2xl font-bold tracking-tight flex items-center gap-3" style={{ color: '#E8ECF1' }}>
              <Users size={24} style={{ color: '#007AFF' }} /> Player Sessions
            </h1>
            <span className="text-xs font-mono" style={{ color: '#6B7A90' }}>{total} sessions | {sm?.unique_players || 0} players | {sm?.active_sessions || 0} active now</span>
          </div>

          {/* Summary Strip */}
          <div className="grid grid-cols-7 gap-3" data-testid="player-summary">
            <StatCard label="Active" value={sm?.active_sessions ?? '--'} color="#00D4AA" sub="right now" />
            <StatCard label="Total Sessions" value={sm?.total_sessions ?? '--'} color="#E8ECF1" />
            <StatCard label="Unique Players" value={sm?.unique_players ?? '--'} color="#007AFF" />
            <StatCard label="Total Wagered" value={fmt(sm?.total_wagered)} color="#F5A623" />
            <StatCard label="Total Won" value={fmt(sm?.total_won)} color="#00D4AA" />
            <StatCard label="Avg Duration" value={`${sm?.avg_duration_minutes || 0} min`} color="#8B5CF6" />
            <StatCard label="Loyalty Pts" value={sm?.total_loyalty_points?.toLocaleString() || '--'} color="#EC4899" />
          </div>
        </div>

        {/* Charts */}
        <div className="px-6 pb-4 flex-shrink-0">
          <div className="grid grid-cols-12 gap-3">
            {/* Sessions Timeline */}
            <div className="col-span-4 rounded border p-3" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="sessions-timeline">
              <div className="text-[10px] uppercase tracking-wider mb-2 font-medium" style={{ color: '#6B7A90' }}>Sessions (24h)</div>
              <ResponsiveContainer width="100%" height={100}>
                <AreaChart data={charts?.sessions_timeline || []}>
                  <defs><linearGradient id="sessG" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#007AFF" stopOpacity={0.3}/><stop offset="95%" stopColor="#007AFF" stopOpacity={0}/></linearGradient></defs>
                  <XAxis dataKey="time" tick={{ fill: '#6B7A90', fontSize: 9 }} axisLine={false} tickLine={false} interval={2} />
                  <YAxis tick={{ fill: '#6B7A90', fontSize: 9 }} axisLine={false} tickLine={false} width={20} />
                  <Tooltip content={<Tip />} />
                  <Area type="monotone" dataKey="sessions" stroke="#007AFF" fill="url(#sessG)" strokeWidth={2} name="Sessions" />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Duration Distribution */}
            <div className="col-span-4 rounded border p-3" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="duration-chart">
              <div className="text-[10px] uppercase tracking-wider mb-2 font-medium" style={{ color: '#6B7A90' }}>Session Duration</div>
              <ResponsiveContainer width="100%" height={100}>
                <BarChart data={charts?.duration_distribution || []} barSize={16}>
                  <XAxis dataKey="name" tick={{ fill: '#6B7A90', fontSize: 9 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#6B7A90', fontSize: 9 }} axisLine={false} tickLine={false} width={20} />
                  <Tooltip content={<Tip />} />
                  <Bar dataKey="value" name="Sessions" radius={[3, 3, 0, 0]}>
                    {(charts?.duration_distribution || []).map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Game Popularity */}
            <div className="col-span-4 rounded border p-3" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="game-popularity">
              <div className="text-[10px] uppercase tracking-wider mb-2 font-medium" style={{ color: '#6B7A90' }}>Game Popularity</div>
              <ResponsiveContainer width="100%" height={100}>
                <PieChart>
                  <Pie data={(charts?.game_popularity || []).slice(0, 6)} cx="50%" cy="50%" innerRadius={25} outerRadius={42} dataKey="value" stroke="none">
                    {(charts?.game_popularity || []).slice(0, 6).map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip content={<Tip />} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Player Leaderboard + Session List */}
        <div className="flex-1 flex overflow-hidden px-6 pb-6 gap-4">
          {/* Leaderboard */}
          <div className="w-80 rounded border flex flex-col overflow-hidden flex-shrink-0" style={{ background: '#12151C', borderColor: '#272E3B' }}>
            <div className="px-4 py-2.5 border-b flex items-center gap-2" style={{ borderColor: '#272E3B' }}>
              <Trophy size={16} style={{ color: '#FFD700' }} />
              <span className="font-heading text-sm font-semibold" style={{ color: '#E8ECF1' }}>Top Players</span>
            </div>
            <div className="flex-1 overflow-y-auto" data-testid="player-leaderboard">
              {(charts?.leaderboard || []).map((p, i) => (
                <div key={p.player_id} className="px-4 py-2 border-b text-xs hover:bg-white/[0.02]" style={{ borderColor: '#272E3B10' }}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[10px] w-5 text-right" style={{ color: i < 3 ? '#FFD700' : '#6B7A90' }}>#{i + 1}</span>
                      <span className="font-medium" style={{ color: '#E8ECF1' }}>{p.name}</span>
                      <TierBadge tier={p.tier} />
                    </div>
                  </div>
                  <div className="flex items-center gap-3 mt-1 ml-7 font-mono text-[10px]">
                    <span style={{ color: '#007AFF' }}>${(p.total_wagered / 1000).toFixed(1)}k bet</span>
                    <span style={{ color: p.net >= 0 ? '#00D4AA' : '#FF3B30' }}>{p.net >= 0 ? '+' : ''}{fmt(p.net)}</span>
                    <span style={{ color: '#6B7A90' }}>{p.sessions}s {p.games}g</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Session List */}
          <div className="flex-1 rounded border flex flex-col overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }}>
            <div className="px-4 py-2.5 border-b flex items-center justify-between" style={{ borderColor: '#272E3B' }}>
              <span className="font-heading text-sm font-semibold" style={{ color: '#E8ECF1' }}>Sessions</span>
              <div className="flex items-center gap-2">
                <Funnel size={14} style={{ color: '#6B7A90' }} />
                <select data-testid="session-status-filter" value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="px-2 py-1 rounded text-xs outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}>
                  <option value="">All</option>
                  <option value="active">Active</option>
                  <option value="completed">Completed</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-12 gap-1 px-4 py-1.5 text-[10px] uppercase tracking-wider font-medium border-b" style={{ color: '#6B7A90', borderColor: '#272E3B' }}>
              <div className="col-span-1">Status</div><div className="col-span-2">Player</div><div className="col-span-1">Tier</div>
              <div className="col-span-2">Device</div><div className="col-span-1">Duration</div><div className="col-span-1">Games</div>
              <div className="col-span-2">Wagered</div><div className="col-span-2">Net</div>
            </div>
            <div className="flex-1 overflow-y-auto" data-testid="session-list">
              {sessions.map(s => (
                <button key={s.id} data-testid={`session-row-${s.id}`} onClick={() => selectSession(s)}
                  className="w-full grid grid-cols-12 gap-1 px-4 py-2 border-b text-xs text-left hover:bg-white/[0.02] transition-colors"
                  style={{ borderColor: '#272E3B10', background: selected?.id === s.id ? 'rgba(0,212,170,0.04)' : 'transparent' }}>
                  <div className="col-span-1">
                    <span className="w-2 h-2 rounded-full inline-block" style={{ background: s.status === 'active' ? '#00D4AA' : '#6B7A90' }} />
                  </div>
                  <div className="col-span-2 font-medium truncate" style={{ color: '#E8ECF1' }}>{s.player_name}</div>
                  <div className="col-span-1"><TierBadge tier={s.player_tier} /></div>
                  <div className="col-span-2 font-mono" style={{ color: '#A3AEBE' }}>{s.device_ref}</div>
                  <div className="col-span-1 font-mono" style={{ color: '#6B7A90' }}>{s.duration_minutes}m</div>
                  <div className="col-span-1 font-mono" style={{ color: '#6B7A90' }}>{s.games_played}</div>
                  <div className="col-span-2 font-mono" style={{ color: '#F5A623' }}>${s.total_wagered?.toLocaleString()}</div>
                  <div className="col-span-2 font-mono" style={{ color: s.net_result >= 0 ? '#00D4AA' : '#FF3B30' }}>
                    {s.net_result >= 0 ? '+' : ''}${s.net_result?.toLocaleString()}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Detail Drawer */}
      {selected && (
        <div className="w-[400px] border-l overflow-y-auto flex-shrink-0" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="session-detail-drawer">
          <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: '#272E3B' }}>
            <div>
              <h3 className="font-heading text-base font-semibold flex items-center gap-2" style={{ color: '#E8ECF1' }}>
                <UserCircle size={20} /> {selected.player_name}
              </h3>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="font-mono text-xs" style={{ color: '#6B7A90' }}>{selected.player_id}</span>
                <TierBadge tier={selected.player_tier} />
                <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${selected.status === 'active' ? '' : ''}`} style={{
                  background: selected.status === 'active' ? 'rgba(0,212,170,0.1)' : 'rgba(107,122,144,0.1)',
                  color: selected.status === 'active' ? '#00D4AA' : '#6B7A90'
                }}>{selected.status}</span>
              </div>
            </div>
            <button onClick={() => { setSelected(null); setDetail(null); }} style={{ color: '#6B7A90' }}><X size={18} /></button>
          </div>

          <div className="p-4 space-y-4">
            {/* Session Info */}
            <div className="grid grid-cols-2 gap-2">
              <div className="rounded border p-2.5" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
                <div className="text-[9px] uppercase tracking-wider" style={{ color: '#6B7A90' }}>Device</div>
                <div className="font-mono text-xs" style={{ color: '#E8ECF1' }}>{selected.device_ref}</div>
              </div>
              <div className="rounded border p-2.5" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
                <div className="text-[9px] uppercase tracking-wider" style={{ color: '#6B7A90' }}>Duration</div>
                <div className="font-mono text-xs" style={{ color: '#E8ECF1' }}>{selected.duration_minutes} min</div>
              </div>
              <div className="rounded border p-2.5" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
                <div className="text-[9px] uppercase tracking-wider" style={{ color: '#6B7A90' }}>Card In</div>
                <div className="font-mono text-[10px]" style={{ color: '#E8ECF1' }}>{new Date(selected.card_in_at).toLocaleString()}</div>
              </div>
              <div className="rounded border p-2.5" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
                <div className="text-[9px] uppercase tracking-wider" style={{ color: '#6B7A90' }}>Card Out</div>
                <div className="font-mono text-[10px]" style={{ color: '#E8ECF1' }}>{selected.card_out_at ? new Date(selected.card_out_at).toLocaleString() : 'Still Active'}</div>
              </div>
            </div>

            {/* Financial Summary */}
            <div>
              <div className="text-[10px] uppercase tracking-wider mb-2 font-medium" style={{ color: '#6B7A90' }}>Session Financials</div>
              <div className="rounded border p-3 space-y-2 font-mono text-xs" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Games Played</span><span style={{ color: '#E8ECF1' }}>{selected.games_played}</span></div>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Total Wagered</span><span style={{ color: '#F5A623' }}>${selected.total_wagered?.toLocaleString()}</span></div>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Total Won</span><span style={{ color: '#00D4AA' }}>${selected.total_won?.toLocaleString()}</span></div>
                <div className="flex justify-between border-t pt-2" style={{ borderColor: '#272E3B' }}>
                  <span style={{ color: '#E8ECF1' }}>Net Result</span>
                  <span className="font-bold" style={{ color: selected.net_result >= 0 ? '#00D4AA' : '#FF3B30' }}>
                    {selected.net_result >= 0 ? '+' : ''}${selected.net_result?.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Denomination</span><span style={{ color: '#E8ECF1' }}>${selected.denomination}</span></div>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Loyalty Points</span><span style={{ color: '#EC4899' }}>{selected.loyalty_points_earned}</span></div>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Vouchers Used</span><span style={{ color: '#E8ECF1' }}>{selected.vouchers_used}</span></div>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Bonuses Triggered</span><span style={{ color: '#E8ECF1' }}>{selected.bonuses_triggered}</span></div>
              </div>
            </div>

            {/* Games Played */}
            <div>
              <div className="text-[10px] uppercase tracking-wider mb-2 font-medium" style={{ color: '#6B7A90' }}>Games Played</div>
              <div className="flex flex-wrap gap-1.5">
                {selected.game_titles?.map(g => (
                  <span key={g} className="text-[10px] font-mono px-2 py-1 rounded" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#A3AEBE' }}>
                    <GameController size={10} className="inline mr-1" />{g}
                  </span>
                ))}
              </div>
            </div>

            {/* Related Financial Events */}
            {detail?.financial_events?.length > 0 && (
              <div>
                <div className="text-[10px] uppercase tracking-wider mb-2 font-medium" style={{ color: '#6B7A90' }}>Related Transactions ({detail.financial_events.length})</div>
                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {detail.financial_events.slice(0, 20).map(fe => (
                    <div key={fe.id} className="flex items-center justify-between px-2 py-1.5 rounded text-[10px] font-mono" style={{ background: '#1A1E2A' }}>
                      <span style={{ color: '#6B7A90' }}>{new Date(fe.occurred_at).toLocaleTimeString()}</span>
                      <span style={{ color: '#A3AEBE' }}>{fe.event_type}</span>
                      <span style={{ color: ['payout', 'jackpot'].includes(fe.event_type) ? '#00D4AA' : '#E8ECF1' }}>${fe.amount?.toLocaleString()}</span>
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
