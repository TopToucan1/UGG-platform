import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import { Crown, Users, CurrencyDollar, Lightning, Gauge, Warning, Trophy, PaperPlaneTilt, Sparkle, Star, CaretRight, Check, GearSix, Plus, Pencil, Trash } from '@phosphor-icons/react';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import InfoTip from '@/components/InfoTip';

const TAB_INFO = {
  overview: 'Fleet-wide snapshot of player segments, tiers, and recent bonus activity.',
  players: 'Drill into individual player churn scores and trigger manual POC awards.',
  rules: 'Create, edit, and toggle automated bonus rules that award POC when conditions are met.',
  rtp: 'Find players whose return-to-player is running below target and compensate them.',
  roi: 'Measure how much coin-in every $1 of POC has generated — the business case for bonusing.',
  config: 'Budgets, time multipliers, and engine settings for the automated reward system.',
};

const SEG_C = { elite_churner: '#FFD700', high_churner: '#00D97E', mid_churner: '#00B4D8', developing: '#8B5CF6', casual: '#4A6080', low_value: '#2A3550' };
const TIER_C = { bronze: '#CD7F32', silver: '#C0C0C0', gold: '#FFD700', platinum: '#B9F2FF', diamond: '#E0E7FF' };

function Tip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return <div className="rounded px-3 py-2 text-xs" style={{ background: '#1A2540', border: '1px solid #1F2E4A' }}>
    <div className="font-mono" style={{ color: '#F0F4FF' }}>{label}</div>
    {payload.map((p, i) => <div key={i} style={{ color: p.color }}>{p.name}: {p.value}</div>)}
  </div>;
}

export default function PIRSPage() {
  const [dashboard, setDashboard] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [players, setPlayers] = useState([]);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [rules, setRules] = useState([]);
  const [roi, setRoi] = useState(null);
  const [pocAmount, setPocAmount] = useState(10);
  const [config, setConfig] = useState(null);
  const [rtpPlayers, setRtpPlayers] = useState([]);
  const [engineStatus, setEngineStatus] = useState(null);
  const [showNewRule, setShowNewRule] = useState(false);
  const [editRule, setEditRule] = useState(null);
  const [newRule, setNewRule] = useState({ name: '', trigger: 'coin_in_milestone', poc_fixed: 10, condition_churn_min: 50, max_per_day: 1, cooldown_min: 60, condition_time_window: 'always', message_template: 'You earned ${amount} in bonus credits!' });
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);

  const fetchData = useCallback(async () => {
    const [dRes, pRes, rRes, roiRes, cRes, eRes] = await Promise.all([
      api.get('/pirs/dashboard'), api.get('/pirs/leaderboard'),
      api.get('/pirs/rules'), api.get('/pirs/analytics/roi'),
      api.get('/pirs/config'), api.get('/pirs/engine/status'),
    ]);
    setDashboard(dRes.data); setPlayers(pRes.data.leaderboard || []);
    setRules(rRes.data.rules || []); setRoi(roiRes.data);
    setConfig(cRes.data); setEngineStatus(eRes.data);
  }, []);
  useEffect(() => { fetchData(); }, [fetchData]);

  const fetchRtpPlayers = async () => {
    const { data } = await api.get('/pirs/rtp/below-threshold?threshold=0.70&min_dollars_played=50');
    setRtpPlayers(data.players_below_rtp || []);
  };

  const updateConfig = async (updates) => {
    await api.post('/pirs/config', updates);
    const { data } = await api.get('/pirs/config');
    setConfig(data);
  };

  const createRule = async () => {
    await api.post('/pirs/rules/create', newRule);
    setShowNewRule(false); setNewRule({ name: '', trigger: 'coin_in_milestone', poc_fixed: 10, condition_churn_min: 50, max_per_day: 1, cooldown_min: 60, condition_time_window: 'always', message_template: 'You earned ${amount} in bonus credits!' });
    fetchData();
  };

  const updateRule = async (ruleId, updates) => {
    await api.put(`/pirs/rules/${ruleId}`, updates);
    setEditRule(null); fetchData();
  };

  const deleteRule = async (ruleId) => {
    await api.delete(`/pirs/rules/${ruleId}`);
    fetchData();
  };

  const runEngine = async () => {
    await api.post('/pirs/engine/run');
    fetchData();
  };

  const sendWalletPoc = async (playerId, amount) => {
    await api.post('/pirs/wallet/credit', { player_id: playerId, amount, reason: 'operator_manual' });
    fetchData();
  };

  const compensateRtp = async (playerId, autoCalc = true) => {
    await api.post('/pirs/wallet/compensate-rtp', { player_id: playerId, auto_calculate: autoCalc });
    fetchRtpPlayers();
  };

  const selectPlayer = async (p) => { setSelected(p); const { data } = await api.get(`/pirs/players/${p.player_id}`); setDetail(data); };
  const awardPoc = async () => { if (!selected) return; await api.post('/pirs/poc/award', { player_id: selected.player_id, amount: pocAmount, trigger_type: 'campaign_manual' }); fetchData(); selectPlayer(selected); };
  const toggleRule = async (id) => { await api.post(`/pirs/rules/${id}/toggle`); const { data } = await api.get('/pirs/rules'); setRules(data.rules || []); };

  const d = dashboard;
  const fmt = v => v != null ? `$${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}` : '--';
  const tabs = [{ id: 'overview', label: 'Fleet Overview' }, { id: 'players', label: 'Player Intel' }, { id: 'rules', label: 'Bonus Rules' }, { id: 'rtp', label: 'RTP Compensation' }, { id: 'roi', label: 'Business Impact' }, { id: 'config', label: 'Settings' }];

  return (
    <div data-testid="pirs-dashboard" className="flex gap-0 h-full -m-6">
      <div className="flex-1 flex flex-col overflow-hidden" style={{ background: '#070B14' }}>
        <div className="px-6 pt-5 pb-3">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Crown size={26} weight="fill" style={{ color: '#FFD700' }} />
              <div><h1 className="font-heading text-2xl font-bold flex items-center" style={{ color: '#F0F4FF' }}>PIRS — Player Intelligence<InfoTip label="PIRS" description="Player Incentive & Rewards System. Scores every carded player for churn risk, then awards POC (player on card) bonuses automatically or manually to keep them playing." /></h1>
              <span className="text-xs" style={{ color: '#4A6080' }}>AI-Driven Churn Scoring & POC Bonusing</span></div>
            </div>
            <div className="flex gap-1 items-center">{tabs.map(t => (
              <span key={t.id} className="flex items-center">
                <button onClick={() => setActiveTab(t.id)} className="px-3 py-1.5 rounded text-[10px] font-medium uppercase tracking-wider"
                  style={{ background: activeTab === t.id ? 'rgba(255,215,0,0.12)' : 'transparent', color: activeTab === t.id ? '#FFD700' : '#4A6080' }}>{t.label}</button>
                <InfoTip label={t.label} description={TAB_INFO[t.id]} />
              </span>
            ))}</div>
          </div>
          {/* KPI Strip */}
          {d && (
            <div className="grid grid-cols-7 gap-2">
              {[
                { label: 'Players', value: d.total_players, color: '#F0F4FF', icon: Users, info: 'Total distinct carded players tracked by the system.' },
                { label: 'Active Now', value: d.active_now, color: '#00D97E', icon: Lightning, info: 'Players currently carded in on any machine across the fleet.' },
                { label: 'Avg Score', value: d.avg_churn_score, color: '#FFD700', icon: Gauge, info: 'Average churn score (0-100). Higher means more players are at risk of drifting away.' },
                { label: 'Lifetime Coin-In', value: fmt(d.total_lifetime_coin_in), color: '#00B4D8', icon: CurrencyDollar, info: 'Every dollar wagered by carded players, ever. The top-line measure of player value.' },
                { label: 'POC Today', value: fmt(d.poc_today), color: '#00D97E', icon: Crown, info: 'Dollar value of POC (player-on-card bonus credits) awarded today across all rules.' },
                { label: 'Awards Today', value: d.poc_today_count || 0, color: '#8B5CF6', icon: Star, info: 'Number of individual POC awards sent today, manual or automated.' },
                { label: 'Lapse Risk', value: d.at_risk_players, color: d.at_risk_players > 5 ? '#FF3B3B' : '#FFB800', icon: Warning, info: 'Players predicted to stop visiting soon. Consider sending them a POC bonus to win them back.' },
              ].map(k => (
                <div key={k.label} className="rounded-lg p-3" style={{ background: '#111827', border: '1px solid #1A2540' }}>
                  <div className="flex items-center justify-between mb-1"><span className="text-[9px] uppercase tracking-widest flex items-center" style={{ color: '#4A6080' }}>{k.label}<InfoTip label={k.label} description={k.info} /></span><k.icon size={14} style={{ color: k.color }} /></div>
                  <div className="font-mono text-lg font-bold" style={{ color: k.color }}>{k.value}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="flex-1 px-6 pb-6 overflow-y-auto">
          {/* FLEET OVERVIEW */}
          {activeTab === 'overview' && d && (
            <div className="grid grid-cols-12 gap-4">
              <div className="col-span-5 rounded-lg border p-4" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
                <div className="text-[10px] uppercase tracking-wider mb-3 font-medium flex items-center" style={{ color: '#4A6080' }}>Churn Score Distribution<InfoTip description="How your players break down across churn-risk segments (elite through low-value). Shifts toward 'churner' segments mean you need to step up retention." /></div>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={d.score_distribution || []} barSize={30}>
                    <XAxis dataKey="label" tick={{ fill: '#4A6080', fontSize: 9 }} axisLine={false} tickLine={false} angle={-15} textAnchor="end" height={50} />
                    <YAxis tick={{ fill: '#4A6080', fontSize: 9 }} axisLine={false} tickLine={false} width={30} />
                    <Tooltip content={<Tip />} />
                    <Bar dataKey="count" name="Players" radius={[4, 4, 0, 0]}>
                      {(d.score_distribution || []).map((s, i) => <Cell key={i} fill={SEG_C[s.segment] || '#4A6080'} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="col-span-3 rounded-lg border p-4" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
                <div className="text-[10px] uppercase tracking-wider mb-3 font-medium flex items-center" style={{ color: '#4A6080' }}>Tiers<InfoTip description="Loyalty tiers and the POC multiplier players in each tier receive. Higher tiers earn more per bonus trigger." /></div>
                {(d.tiers || []).map(t => (
                  <div key={t.id} className="flex items-center gap-2 px-2 py-1.5 rounded mb-1" style={{ background: '#111827' }}>
                    <Trophy size={12} weight="fill" style={{ color: TIER_C[t.id] || '#4A6080' }} />
                    <span className="text-xs font-medium flex-1" style={{ color: '#F0F4FF' }}>{t.name}</span>
                    <span className="text-[9px] font-mono" style={{ color: '#4A6080' }}>{t.poc_multiplier}x POC</span>
                  </div>
                ))}
              </div>
              <div className="col-span-4 rounded-lg border p-4" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
                <div className="text-[10px] uppercase tracking-wider mb-3 font-medium flex items-center" style={{ color: '#FFD700' }}>Live Bonus Feed<InfoTip description="Real-time stream of POC awards being sent to players. Useful to verify the engine is actually firing rules." /></div>
                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {(d.recent_awards || []).map(a => (
                    <div key={a.id} className="flex items-center gap-2 px-2 py-1.5 rounded text-[10px]" style={{ background: '#111827' }}>
                      <Crown size={10} weight="fill" style={{ color: '#FFD700' }} />
                      <span style={{ color: '#F0F4FF' }}>{a.player_name}</span>
                      <span className="font-mono" style={{ color: '#00D97E' }}>${a.poc_amount}</span>
                      <span style={{ color: '#4A6080' }}>{a.trigger_type?.replace(/_/g, ' ')}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* PLAYER INTELLIGENCE */}
          {activeTab === 'players' && (
            <div className="grid grid-cols-12 gap-4">
              <div className="col-span-5 rounded-lg border overflow-hidden" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
                <div className="px-4 py-2 text-[10px] uppercase tracking-wider font-medium flex items-center" style={{ color: '#FFD700' }}>Top Players by Churn Score<InfoTip description="Players ranked by churn score — the highest scores are your most loyal, highest-value players. Click any row to open their profile." /></div>
                {players.map((p, i) => (
                  <button key={p.player_id} onClick={() => selectPlayer(p)} className="w-full text-left px-4 py-2 border-b flex items-center gap-2 hover:bg-white/[0.02]"
                    style={{ borderColor: '#1A254010', background: selected?.player_id === p.player_id ? 'rgba(255,215,0,0.04)' : 'transparent' }}>
                    <span className="font-mono text-[10px] w-5 text-right" style={{ color: i < 3 ? '#FFD700' : '#4A6080' }}>#{i + 1}</span>
                    <span className="w-2 h-2 rounded-full" style={{ background: SEG_C[p.segment_code] || '#4A6080' }} />
                    <span className="text-xs font-medium flex-1" style={{ color: '#F0F4FF' }}>{p.player_name}</span>
                    <span className="font-mono text-xs font-bold" style={{ color: '#FFD700' }}>{p.churn_score}</span>
                    <span className="text-[9px] px-1 rounded" style={{ background: `${TIER_C[p.tier_id]}20`, color: TIER_C[p.tier_id] }}>{p.tier_name}</span>
                  </button>
                ))}
              </div>
              {detail && (
                <div className="col-span-7 rounded-lg border p-4 space-y-4" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-heading text-lg font-semibold" style={{ color: '#F0F4FF' }}>{detail.player_name}</h3>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs font-mono" style={{ color: '#4A6080' }}>{detail.player_id}</span>
                        <Trophy size={12} weight="fill" style={{ color: TIER_C[detail.tier_id] }} />
                        <span className="text-[10px]" style={{ color: TIER_C[detail.tier_id] }}>{detail.tier_name}</span>
                        <span className="text-[10px] px-1.5 rounded" style={{ background: `${SEG_C[detail.segment_code]}20`, color: SEG_C[detail.segment_code] }}>{detail.segment_label}</span>
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="font-mono text-3xl font-black" style={{ color: '#FFD700' }}>{detail.churn_score}</div>
                      <div className="text-[9px] uppercase tracking-widest" style={{ color: '#4A6080' }}>Churn Score</div>
                    </div>
                  </div>
                  <div className="grid grid-cols-4 gap-2">
                    {[
                      { l: 'Play-Back', v: `${(detail.play_back_rate * 100).toFixed(0)}%`, c: '#00D97E', info: 'Share of winnings the player puts back into play. Higher = the player keeps feeding the machine.' },
                      { l: 'Cash-Out', v: `${(detail.cash_out_rate * 100).toFixed(0)}%`, c: '#FF3B3B', info: 'Share of winnings the player cashes out. High cash-out players leave with money instead of replaying.' },
                      { l: 'Lapse Risk', v: `${detail.lapse_risk}%`, c: detail.lapse_risk > 50 ? '#FF3B3B' : '#00D97E', info: 'Probability this player stops visiting soon. Over 50% is a red flag — consider sending POC.' },
                      { l: 'POC ROI', v: `${detail.poc_roi_lifetime}:1`, c: '#FFD700', info: 'Lifetime return on POC — for every $1 of bonus sent, how much coin-in came back. 3:1 or better is healthy.' },
                    ].map(m => (
                      <div key={m.l} className="rounded p-2" style={{ background: '#111827' }}>
                        <div className="text-[8px] uppercase tracking-wider flex items-center" style={{ color: '#4A6080' }}>{m.l}<InfoTip label={m.l} description={m.info} /></div>
                        <div className="font-mono text-sm font-bold" style={{ color: m.c }}>{m.v}</div>
                      </div>
                    ))}
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-[10px] font-mono">
                    <div style={{ color: '#4A6080' }}>Coin-In: <span style={{ color: '#00B4D8' }}>{fmt(detail.lifetime_coin_in)}</span></div>
                    <div style={{ color: '#4A6080' }}>Visits: <span style={{ color: '#F0F4FF' }}>{detail.lifetime_visits}</span></div>
                    <div style={{ color: '#4A6080' }}>Avg Bet: <span style={{ color: '#F0F4FF' }}>${detail.avg_bet_size}</span></div>
                    <div style={{ color: '#4A6080' }}>Sessions 30d: <span style={{ color: '#F0F4FF' }}>{detail.visits_30d}</span></div>
                    <div style={{ color: '#4A6080' }}>Avg Session: <span style={{ color: '#F0F4FF' }}>{detail.avg_session_length_mins}min</span></div>
                    <div style={{ color: '#4A6080' }}>POC Total: <span style={{ color: '#00D97E' }}>{fmt(detail.total_poc_awarded)}</span></div>
                  </div>
                  {/* Quick POC Award */}
                  <div className="flex items-center gap-2 pt-2 border-t" style={{ borderColor: '#1A2540' }}>
                    <span className="text-[10px]" style={{ color: '#4A6080' }}>Award POC:</span>
                    {[5, 10, 15, 25, 50].map(a => (
                      <button key={a} onClick={() => setPocAmount(a)} className="px-2 py-1 rounded text-[10px] font-mono" style={{ background: pocAmount === a ? '#FFD70020' : '#111827', color: pocAmount === a ? '#FFD700' : '#4A6080', border: '1px solid #1A2540' }}>${a}</button>
                    ))}
                    <button onClick={awardPoc} className="flex items-center gap-1 px-3 py-1 rounded text-[10px] font-medium" style={{ background: '#FFD700', color: '#070B14' }}>
                      <PaperPlaneTilt size={12} /> Send ${pocAmount} POC
                    </button>
                    <InfoTip description="Manually credit the selected player with bonus POC. Use this as a one-off courtesy or to recover a specific player." />
                  </div>
                  {/* Recent Awards */}
                  {detail.recent_awards?.length > 0 && (
                    <div>
                      <div className="text-[9px] uppercase tracking-wider mb-1" style={{ color: '#4A6080' }}>Recent POC Awards</div>
                      {detail.recent_awards.slice(0, 5).map(a => (
                        <div key={a.id} className="flex items-center gap-2 px-2 py-1 rounded text-[10px] mb-0.5" style={{ background: '#111827' }}>
                          <Crown size={10} style={{ color: '#FFD700' }} />
                          <span className="font-mono" style={{ color: '#00D97E' }}>${a.poc_amount}</span>
                          <span style={{ color: '#4A6080' }}>{a.trigger_type?.replace(/_/g, ' ')}</span>
                          <span className="ml-auto font-mono" style={{ color: '#4A6080' }}>{a.created_at?.slice(0, 10)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* BONUS RULES — Full CRUD */}
          {activeTab === 'rules' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono" style={{ color: '#4A6080' }}>{rules.length} rules ({rules.filter(r => r.is_active).length} active)</span>
                  <button onClick={runEngine} className="flex items-center gap-1 px-3 py-1.5 rounded text-[10px] font-medium" style={{ background: '#00D97E', color: '#070B14' }}><Lightning size={12} /> Run Engine Now</button>
                  <InfoTip description="Evaluate every active rule against the current player base right now and issue any qualifying POC awards immediately." />
                </div>
                <div className="flex items-center">
                  <button onClick={() => setShowNewRule(true)} className="flex items-center gap-1 px-3 py-1.5 rounded text-[10px] font-medium" style={{ background: '#FFD700', color: '#070B14' }}><Plus size={12} /> Create Rule</button>
                  <InfoTip description="Build a new automated bonus rule. Define a trigger, POC amount, and conditions — the engine will award POC whenever a player matches." />
                </div>
              </div>
              {/* New Rule Form */}
              {showNewRule && (
                <div className="rounded-lg border p-4 space-y-3" style={{ background: '#0C1322', borderColor: '#FFD70040' }}>
                  <h4 className="text-sm font-semibold flex items-center" style={{ color: '#F0F4FF' }}>Create New Reward Rule<InfoTip description="Define a new automated bonus rule. The engine will evaluate this rule against all players and award POC when conditions are met." /></h4>
                  <div className="grid grid-cols-3 gap-3">
                    <div><label className="block text-[9px] uppercase tracking-wider mb-1 flex items-center" style={{ color: '#4A6080' }}>Rule Name<InfoTip description="A short friendly name so operators know what this rule does (e.g. 'Weekend Loyalty Boost')." /></label><input value={newRule.name} onChange={e => setNewRule(p => ({ ...p, name: e.target.value }))} placeholder="Weekend Bonus" className="w-full px-3 py-2 rounded text-xs outline-none" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} /></div>
                    <div><label className="block text-[9px] uppercase tracking-wider mb-1 flex items-center" style={{ color: '#4A6080' }}>Trigger<InfoTip description="The event that fires this rule (e.g. card-in, coin-in milestone, lapse risk reached). Pick what action should earn the player POC." /></label><select value={newRule.trigger} onChange={e => setNewRule(p => ({ ...p, trigger: e.target.value }))} className="w-full px-3 py-2 rounded text-xs outline-none" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }}>{['card_in', 'coin_in_milestone', 'session_duration', 'post_win_playback', 'lapse_risk', 'return_visit', 'churn_threshold'].map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}</select></div>
                    <div><label className="block text-[9px] uppercase tracking-wider mb-1 flex items-center" style={{ color: '#4A6080' }}>POC Amount ($)<InfoTip description="Dollar value of the bonus sent to the player each time this rule fires. Tier multipliers may boost this." /></label><input type="number" value={newRule.poc_fixed} onChange={e => setNewRule(p => ({ ...p, poc_fixed: +e.target.value }))} className="w-full px-3 py-2 rounded text-xs outline-none font-mono" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} /></div>
                  </div>
                  <div className="grid grid-cols-4 gap-3">
                    <div><label className="block text-[9px] uppercase tracking-wider mb-1 flex items-center" style={{ color: '#4A6080' }}>Min Churn Score<InfoTip description="Only players with at least this churn score qualify. Higher numbers restrict to your top-tier loyal players." /></label><input type="number" value={newRule.condition_churn_min} onChange={e => setNewRule(p => ({ ...p, condition_churn_min: +e.target.value }))} className="w-full px-3 py-2 rounded text-xs outline-none font-mono" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} /></div>
                    <div><label className="block text-[9px] uppercase tracking-wider mb-1 flex items-center" style={{ color: '#4A6080' }}>Max Per Day<InfoTip description="Cap on how many times a single player can hit this rule per day. Prevents runaway bonusing." /></label><input type="number" value={newRule.max_per_day} onChange={e => setNewRule(p => ({ ...p, max_per_day: +e.target.value }))} className="w-full px-3 py-2 rounded text-xs outline-none font-mono" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} /></div>
                    <div><label className="block text-[9px] uppercase tracking-wider mb-1 flex items-center" style={{ color: '#4A6080' }}>Cooldown (min)<InfoTip description="Minimum minutes between awards to the same player under this rule. Stops back-to-back payouts." /></label><input type="number" value={newRule.cooldown_min} onChange={e => setNewRule(p => ({ ...p, cooldown_min: +e.target.value }))} className="w-full px-3 py-2 rounded text-xs outline-none font-mono" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} /></div>
                    <div><label className="block text-[9px] uppercase tracking-wider mb-1 flex items-center" style={{ color: '#4A6080' }}>Time Window<InfoTip description="When the rule is allowed to fire: always, weekdays only, weekends only, or happy-hour window." /></label><select value={newRule.condition_time_window} onChange={e => setNewRule(p => ({ ...p, condition_time_window: e.target.value }))} className="w-full px-3 py-2 rounded text-xs outline-none" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }}>{['always', 'weekdays', 'weekends', 'happy_hour'].map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}</select></div>
                  </div>
                  <div><label className="block text-[9px] uppercase tracking-wider mb-1 flex items-center" style={{ color: '#4A6080' }}>Message Template (use {'{amount}'} for POC value)<InfoTip description="The message the player sees when the POC lands — include {amount} to substitute the dollar value." /></label><input value={newRule.message_template} onChange={e => setNewRule(p => ({ ...p, message_template: e.target.value }))} className="w-full px-3 py-2 rounded text-xs outline-none" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} /></div>
                  <div className="flex gap-2"><button onClick={createRule} className="px-4 py-2 rounded text-xs font-medium" style={{ background: '#FFD700', color: '#070B14' }}>Create Rule</button><button onClick={() => setShowNewRule(false)} className="px-4 py-2 rounded text-xs" style={{ color: '#4A6080' }}>Cancel</button></div>
                </div>
              )}
              {/* Rule List */}
              {rules.map(r => (
                <div key={r.id} className="rounded-lg border p-4" style={{ background: editRule?.id === r.id ? '#111827' : '#0C1322', borderColor: editRule?.id === r.id ? '#FFD70040' : r.is_active ? '#00D97E30' : '#1A2540' }}>
                  {/* Confirm Delete Dialog */}
                  {confirmDeleteId === r.id && (
                    <div className="mb-3 rounded-lg p-3 flex items-center justify-between" style={{ background: 'rgba(255,59,59,0.08)', border: '1px solid rgba(255,59,59,0.3)' }}>
                      <span className="text-xs font-medium" style={{ color: '#FF3B3B' }}>Are you sure you want to delete "{r.name}"? This cannot be undone.</span>
                      <div className="flex gap-2">
                        <button onClick={() => { deleteRule(r.id); setConfirmDeleteId(null); }} className="px-3 py-1.5 rounded text-[10px] font-medium" style={{ background: '#FF3B3B', color: '#F0F4FF' }}>Yes, Delete</button>
                        <button onClick={() => setConfirmDeleteId(null)} className="px-3 py-1.5 rounded text-[10px]" style={{ color: '#4A6080', border: '1px solid #1A2540' }}>Cancel</button>
                      </div>
                    </div>
                  )}
                  {/* Edit Mode */}
                  {editRule?.id === r.id ? (
                    <div className="space-y-3">
                      <div className="flex items-center justify-between"><h4 className="text-xs font-semibold" style={{ color: '#FFD700' }}>Editing: {r.name}</h4></div>
                      <div className="grid grid-cols-3 gap-3">
                        <div><label className="block text-[8px] uppercase tracking-wider mb-0.5" style={{ color: '#4A6080' }}>Rule Name</label><input value={editRule.name} onChange={e => setEditRule(p => ({ ...p, name: e.target.value }))} className="w-full px-2 py-1.5 rounded text-xs outline-none" style={{ background: '#0C1322', border: '1px solid #1A2540', color: '#F0F4FF' }} /></div>
                        <div><label className="block text-[8px] uppercase tracking-wider mb-0.5" style={{ color: '#4A6080' }}>Trigger</label><select value={editRule.trigger} onChange={e => setEditRule(p => ({ ...p, trigger: e.target.value }))} className="w-full px-2 py-1.5 rounded text-xs outline-none" style={{ background: '#0C1322', border: '1px solid #1A2540', color: '#F0F4FF' }}>{['card_in', 'coin_in_milestone', 'session_duration', 'post_win_playback', 'lapse_risk', 'return_visit', 'churn_threshold'].map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}</select></div>
                        <div><label className="block text-[8px] uppercase tracking-wider mb-0.5" style={{ color: '#4A6080' }}>POC Amount ($)</label><input type="number" value={editRule.poc_fixed} onChange={e => setEditRule(p => ({ ...p, poc_fixed: +e.target.value }))} className="w-full px-2 py-1.5 rounded text-xs outline-none font-mono" style={{ background: '#0C1322', border: '1px solid #1A2540', color: '#F0F4FF' }} /></div>
                      </div>
                      <div className="grid grid-cols-4 gap-3">
                        <div><label className="block text-[8px] uppercase tracking-wider mb-0.5" style={{ color: '#4A6080' }}>Min Churn</label><input type="number" value={editRule.condition_churn_min || ''} onChange={e => setEditRule(p => ({ ...p, condition_churn_min: +e.target.value || null }))} className="w-full px-2 py-1.5 rounded text-xs outline-none font-mono" style={{ background: '#0C1322', border: '1px solid #1A2540', color: '#F0F4FF' }} /></div>
                        <div><label className="block text-[8px] uppercase tracking-wider mb-0.5" style={{ color: '#4A6080' }}>Max/Day</label><input type="number" value={editRule.max_per_day || ''} onChange={e => setEditRule(p => ({ ...p, max_per_day: +e.target.value || null }))} className="w-full px-2 py-1.5 rounded text-xs outline-none font-mono" style={{ background: '#0C1322', border: '1px solid #1A2540', color: '#F0F4FF' }} /></div>
                        <div><label className="block text-[8px] uppercase tracking-wider mb-0.5" style={{ color: '#4A6080' }}>Cooldown (min)</label><input type="number" value={editRule.cooldown_min || ''} onChange={e => setEditRule(p => ({ ...p, cooldown_min: +e.target.value || null }))} className="w-full px-2 py-1.5 rounded text-xs outline-none font-mono" style={{ background: '#0C1322', border: '1px solid #1A2540', color: '#F0F4FF' }} /></div>
                        <div><label className="block text-[8px] uppercase tracking-wider mb-0.5" style={{ color: '#4A6080' }}>Time Window</label><select value={editRule.condition_time_window || 'always'} onChange={e => setEditRule(p => ({ ...p, condition_time_window: e.target.value }))} className="w-full px-2 py-1.5 rounded text-xs outline-none" style={{ background: '#0C1322', border: '1px solid #1A2540', color: '#F0F4FF' }}>{['always', 'weekdays', 'weekends', 'happy_hour'].map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}</select></div>
                      </div>
                      <div><label className="block text-[8px] uppercase tracking-wider mb-0.5" style={{ color: '#4A6080' }}>Message Template</label><input value={editRule.message_template || ''} onChange={e => setEditRule(p => ({ ...p, message_template: e.target.value }))} className="w-full px-2 py-1.5 rounded text-xs outline-none" style={{ background: '#0C1322', border: '1px solid #1A2540', color: '#F0F4FF' }} /></div>
                      <div className="flex gap-2">
                        <button onClick={() => updateRule(r.id, editRule)} className="px-4 py-1.5 rounded text-xs font-medium" style={{ background: '#00D97E', color: '#070B14' }}>Save Changes</button>
                        <button onClick={() => setEditRule(null)} className="px-4 py-1.5 rounded text-xs" style={{ color: '#4A6080' }}>Cancel</button>
                      </div>
                    </div>
                  ) : (
                    /* View Mode */
                    <div className="flex items-center gap-3">
                      <button onClick={() => toggleRule(r.id)} className="w-10 h-5 rounded-full flex items-center transition-colors flex-shrink-0" style={{ background: r.is_active ? '#00D97E' : '#1A2540', justifyContent: r.is_active ? 'flex-end' : 'flex-start', padding: '2px' }}><span className="w-4 h-4 rounded-full" style={{ background: '#F0F4FF' }} /></button>
                      <div className="flex-1">
                        <div className="text-xs font-semibold" style={{ color: '#F0F4FF' }}>{r.name}</div>
                        <div className="text-[10px] font-mono" style={{ color: '#4A6080' }}>
                          Trigger: {r.trigger} | POC: <span style={{ color: '#00D97E' }}>${r.poc_fixed}</span> | Churn: {r.condition_churn_min || 'any'}+ | Max/day: {r.max_per_day || '∞'} | Cooldown: {r.cooldown_min || 0}min | Window: {r.condition_time_window || 'always'}
                        </div>
                      </div>
                      <button data-testid={`edit-rule-${r.id}`} onClick={() => setEditRule({ ...r })} className="p-1.5 rounded transition-colors hover:bg-white/[0.05]" style={{ color: '#00B4D8' }} title="Edit rule"><Pencil size={14} /></button>
                      {r.is_custom && <button data-testid={`delete-rule-${r.id}`} onClick={() => setConfirmDeleteId(r.id)} className="p-1.5 rounded transition-colors hover:bg-white/[0.05]" style={{ color: '#FF3B3B' }} title="Delete rule"><Trash size={14} /></button>}
                      <span className="font-mono text-xs flex-shrink-0" style={{ color: r.is_active ? '#00D97E' : '#4A6080' }}>{r.is_active ? 'ACTIVE' : 'OFF'}</span>
                    </div>
                  )}
                </div>
              ))}
              {/* Engine Status */}
              {engineStatus && (
                <div className="rounded-lg border p-3 mt-3" style={{ background: '#111827', borderColor: '#1A2540' }}>
                  <div className="flex items-center gap-4 text-[10px] font-mono">
                    <span style={{ color: engineStatus.auto_enabled ? '#00D97E' : '#FF3B3B' }}>Engine: {engineStatus.auto_enabled ? 'AUTO' : 'MANUAL'}</span>
                    <span style={{ color: '#4A6080' }}>Budget: ${engineStatus.budget_daily}</span>
                    <span style={{ color: '#00D97E' }}>Spent today: ${engineStatus.budget_spent_today}</span>
                    <span style={{ color: '#FFD700' }}>Remaining: ${engineStatus.budget_remaining}</span>
                    <span style={{ color: '#4A6080' }}>Awards today: {engineStatus.awards_today}</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* RTP COMPENSATION */}
          {activeTab === 'rtp' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-heading text-lg font-semibold flex items-center" style={{ color: '#F0F4FF' }}>RTP Compensation — Players Below 70% Return<InfoTip label="RTP Compensation" description="RTP (return to player) is the share of a player's wagers they win back. Players running cold — well below the advertised RTP — may leave unhappy. Use this tool to find them and send POC to smooth their experience." /></h3>
                <div className="flex items-center">
                  <button onClick={fetchRtpPlayers} className="flex items-center gap-1 px-4 py-2 rounded text-xs font-medium" style={{ background: '#00B4D8', color: '#070B14' }}><Warning size={14} /> Scan Players</button>
                  <InfoTip description="Run a scan across carded players for anyone whose RTP is under 70% with at least $50 played. Returns a list you can review and compensate." />
                </div>
              </div>
              {rtpPlayers.length > 0 ? (
                <div className="space-y-2">
                  {rtpPlayers.map(p => (
                    <div key={p.player_id} className="rounded-lg border p-4 flex items-center gap-4" style={{ background: '#0C1322', borderColor: '#FF3B3B30' }}>
                      <div className="text-center w-16">
                        <div className="font-mono text-xl font-black" style={{ color: p.rtp_pct >= 65 ? '#FFB800' : '#FF3B3B' }}>{p.rtp_pct}%</div>
                        <div className="text-[8px] uppercase" style={{ color: '#4A6080' }}>RTP</div>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2"><span className="text-xs font-semibold" style={{ color: '#F0F4FF' }}>{p.player_name}</span><span className="text-[10px] font-mono" style={{ color: '#4A6080' }}>{p.player_id}</span>{p.tier && <span className="text-[9px] px-1 rounded" style={{ background: '#FFD70020', color: '#FFD700' }}>{p.tier}</span>}</div>
                        <div className="text-[10px] font-mono mt-0.5" style={{ color: '#4A6080' }}>Wagered: ${p.total_wagered?.toLocaleString()} | Won: ${p.total_won?.toLocaleString()} | Deficit: <span style={{ color: '#FF3B3B' }}>${p.deficit_dollars?.toLocaleString()}</span> | Sessions: {p.sessions}{p.has_pending_compensation && <span style={{ color: '#FFB800' }}> | Has pending POC</span>}</div>
                      </div>
                      <div className="flex gap-2">
                        <button onClick={() => compensateRtp(p.player_id, true)} className="px-3 py-1.5 rounded text-[10px] font-medium" style={{ background: '#FFD700', color: '#070B14' }}>Auto Compensate</button>
                        <button onClick={() => sendWalletPoc(p.player_id, 25)} className="px-3 py-1.5 rounded text-[10px] font-medium" style={{ background: 'rgba(0,180,216,0.1)', color: '#00B4D8', border: '1px solid rgba(0,180,216,0.2)' }}>Send $25 POC</button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-lg border p-8 text-center" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
                  <Warning size={40} className="mx-auto mb-3" style={{ color: '#1A2540' }} />
                  <div className="text-sm" style={{ color: '#4A6080' }}>Click "Scan Players" to find players below 70% RTP</div>
                  <div className="text-xs mt-1" style={{ color: '#4A6080' }}>These players may need compensation to maintain loyalty</div>
                </div>
              )}
            </div>
          )}

          {/* BUSINESS IMPACT / ROI */}
          {activeTab === 'roi' && roi && (
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-lg border p-6 text-center" style={{ background: '#0C1322', borderColor: '#FFD70030' }}>
                <div className="text-[10px] uppercase tracking-wider mb-2 flex items-center justify-center" style={{ color: '#4A6080' }}>POC ROI ({roi.period_days} days)<InfoTip label="POC ROI" description="For every $1 of POC bonus sent out, how many dollars of coin-in came back from those players. Above 3:1 is healthy for most routes." /></div>
                <div className="font-mono text-5xl font-black" style={{ color: '#FFD700' }}>{roi.roi}:1</div>
                <div className="text-xs mt-2" style={{ color: '#4A6080' }}>Target: {roi.target_roi}:1</div>
              </div>
              <div className="rounded-lg border p-6 space-y-3" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
                <div className="flex justify-between text-sm"><span className="flex items-center" style={{ color: '#4A6080' }}>Total POC Invested<InfoTip description="Total dollars of POC awarded during the reporting window — the cost side of the ROI calculation." /></span><span className="font-mono font-bold" style={{ color: '#FF3B3B' }}>{fmt(roi.total_poc)}</span></div>
                <div className="flex justify-between text-sm"><span className="flex items-center" style={{ color: '#4A6080' }}>Coin-In Generated<InfoTip description="Estimated wagers made by players who received a POC bonus. The return side of the ROI calculation." /></span><span className="font-mono font-bold" style={{ color: '#00D97E' }}>{fmt(roi.estimated_coin_in_from_poc)}</span></div>
                <div className="flex justify-between text-sm"><span className="flex items-center" style={{ color: '#4A6080' }}>Awards Count<InfoTip description="Number of individual POC awards issued in the period." /></span><span className="font-mono font-bold" style={{ color: '#F0F4FF' }}>{roi.awards_count}</span></div>
                <div className="flex justify-between text-sm border-t pt-2" style={{ borderColor: '#1A2540' }}><span className="flex items-center" style={{ color: '#F0F4FF' }}>Net Return per $1 POC<InfoTip description="Coin-in generated divided by POC spent. The bottom-line answer to 'is bonusing worth it?'." /></span><span className="font-mono font-bold text-lg" style={{ color: '#FFD700' }}>${roi.roi}</span></div>
              </div>
            </div>
          )}

          {/* SETTINGS / CONFIGURATION */}
          {activeTab === 'config' && config && (
            <div className="space-y-4">
              <h3 className="font-heading text-lg font-semibold flex items-center gap-2" style={{ color: '#F0F4FF' }}><GearSix size={20} /> PIRS Configuration<InfoTip label="PIRS Configuration" description="Control the limits and behavior of the automated reward engine. Set budgets before enabling auto-awards." /></h3>
              <div className="rounded-lg border p-5 space-y-4" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
                <h4 className="text-sm font-semibold flex items-center" style={{ color: '#FFD700' }}>Budget Controls<InfoTip description="Hard spending caps for the bonus engine. If a limit is hit, the engine stops awarding POC until the window resets." /></h4>
                <p className="text-xs" style={{ color: '#4A6080' }}>Set spending limits to control how much POC the system awards automatically.</p>
                <div className="grid grid-cols-3 gap-3">
                  {[['budget_daily_limit', 'Daily Budget ($)'], ['budget_weekly_limit', 'Weekly Budget ($)'], ['budget_monthly_limit', 'Monthly Budget ($)'], ['budget_per_player_daily', 'Per Player Daily ($)'], ['budget_per_player_session', 'Per Player Session ($)'], ['max_poc_amount', 'Max POC Amount ($)']].map(([k, l]) => (
                    <div key={k}><label className="block text-[9px] uppercase tracking-wider mb-1" style={{ color: '#4A6080' }}>{l}</label><input type="number" value={config[k] || ''} onChange={e => setConfig(p => ({ ...p, [k]: +e.target.value }))} className="w-full px-3 py-2 rounded text-sm outline-none font-mono" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} /></div>
                  ))}
                </div>
              </div>
              <div className="rounded-lg border p-5 space-y-3" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
                <h4 className="text-sm font-semibold flex items-center" style={{ color: '#00B4D8' }}>Time-Based Multipliers<InfoTip description="Boost POC payouts during specific windows like happy hour or weekends to drive visits at targeted times." /></h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="flex items-center gap-2 text-xs mb-2 cursor-pointer" style={{ color: '#F0F4FF' }}><input type="checkbox" checked={config.happy_hour_enabled || false} onChange={e => setConfig(p => ({ ...p, happy_hour_enabled: e.target.checked }))} className="w-4 h-4" />Enable Happy Hour</label>
                    <div className="grid grid-cols-3 gap-2">
                      <div><label className="block text-[8px]" style={{ color: '#4A6080' }}>Start</label><input value={config.happy_hour_start || '16:00'} onChange={e => setConfig(p => ({ ...p, happy_hour_start: e.target.value }))} className="w-full px-2 py-1 rounded text-xs outline-none font-mono" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} /></div>
                      <div><label className="block text-[8px]" style={{ color: '#4A6080' }}>End</label><input value={config.happy_hour_end || '18:00'} onChange={e => setConfig(p => ({ ...p, happy_hour_end: e.target.value }))} className="w-full px-2 py-1 rounded text-xs outline-none font-mono" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} /></div>
                      <div><label className="block text-[8px]" style={{ color: '#4A6080' }}>Multiplier</label><input type="number" step="0.1" value={config.happy_hour_multiplier || 1.5} onChange={e => setConfig(p => ({ ...p, happy_hour_multiplier: +e.target.value }))} className="w-full px-2 py-1 rounded text-xs outline-none font-mono" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} /></div>
                    </div>
                  </div>
                  <div>
                    <label className="block text-[9px] uppercase tracking-wider mb-1" style={{ color: '#4A6080' }}>Weekend Multiplier</label>
                    <input type="number" step="0.1" value={config.weekend_multiplier || 1.0} onChange={e => setConfig(p => ({ ...p, weekend_multiplier: +e.target.value }))} className="w-full px-3 py-2 rounded text-sm outline-none font-mono" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} />
                    <div className="text-[8px]" style={{ color: '#4A6080' }}>1.0 = no boost, 1.25 = 25% more on weekends</div>
                  </div>
                </div>
              </div>
              <div className="rounded-lg border p-5 space-y-3" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
                <h4 className="text-sm font-semibold flex items-center" style={{ color: '#00D97E' }}>Engine Controls<InfoTip description="Toggle auto-running of the rule engine and player score recalculation. Disable if you want everything to be manual operator action." /></h4>
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-xs cursor-pointer" style={{ color: '#F0F4FF' }}><input type="checkbox" checked={config.auto_rules_enabled || false} onChange={e => setConfig(p => ({ ...p, auto_rules_enabled: e.target.checked }))} className="w-4 h-4" />Auto-run reward rules (award POC when conditions met)</label>
                  <label className="flex items-center gap-2 text-xs cursor-pointer" style={{ color: '#F0F4FF' }}><input type="checkbox" checked={config.auto_scale_rewards || false} onChange={e => setConfig(p => ({ ...p, auto_scale_rewards: e.target.checked }))} className="w-4 h-4" />Auto-scale as player base grows (recalculate scores each run)</label>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div><label className="block text-[9px] uppercase tracking-wider mb-1" style={{ color: '#4A6080' }}>New Player Welcome POC ($)</label><input type="number" value={config.new_player_welcome_poc || 10} onChange={e => setConfig(p => ({ ...p, new_player_welcome_poc: +e.target.value }))} className="w-full px-3 py-2 rounded text-sm outline-none font-mono" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} /></div>
                  <div><label className="block text-[9px] uppercase tracking-wider mb-1" style={{ color: '#4A6080' }}>Min POC Amount ($)</label><input type="number" value={config.min_poc_amount || 5} onChange={e => setConfig(p => ({ ...p, min_poc_amount: +e.target.value }))} className="w-full px-3 py-2 rounded text-sm outline-none font-mono" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} /></div>
                </div>
              </div>
              <div className="flex items-center gap-1"><button onClick={() => updateConfig(config)} className="w-full py-3 rounded-lg text-sm font-semibold flex items-center justify-center" style={{ background: '#FFD700', color: '#070B14' }}>Save All Configuration Changes</button><InfoTip description="Persist every setting change above. Nothing takes effect until this is clicked." /></div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
