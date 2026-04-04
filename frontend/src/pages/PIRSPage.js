import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import { Crown, Users, CurrencyDollar, Lightning, Gauge, Warning, Trophy, PaperPlaneTilt, Sparkle, Star, CaretRight, Check } from '@phosphor-icons/react';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

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

  const fetchData = useCallback(async () => {
    const [dRes, pRes, rRes, roiRes] = await Promise.all([
      api.get('/pirs/dashboard'), api.get('/pirs/leaderboard'),
      api.get('/pirs/rules'), api.get('/pirs/analytics/roi'),
    ]);
    setDashboard(dRes.data); setPlayers(pRes.data.leaderboard || []);
    setRules(rRes.data.rules || []); setRoi(roiRes.data);
  }, []);
  useEffect(() => { fetchData(); }, [fetchData]);

  const selectPlayer = async (p) => { setSelected(p); const { data } = await api.get(`/pirs/players/${p.player_id}`); setDetail(data); };
  const awardPoc = async () => { if (!selected) return; await api.post('/pirs/poc/award', { player_id: selected.player_id, amount: pocAmount, trigger_type: 'campaign_manual' }); fetchData(); selectPlayer(selected); };
  const toggleRule = async (id) => { await api.post(`/pirs/rules/${id}/toggle`); const { data } = await api.get('/pirs/rules'); setRules(data.rules || []); };

  const d = dashboard;
  const fmt = v => v != null ? `$${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}` : '--';
  const tabs = [{ id: 'overview', label: 'Fleet Overview' }, { id: 'players', label: 'Player Intelligence' }, { id: 'rules', label: 'Bonus Rules' }, { id: 'roi', label: 'Business Impact' }];

  return (
    <div data-testid="pirs-dashboard" className="flex gap-0 h-full -m-6">
      <div className="flex-1 flex flex-col overflow-hidden" style={{ background: '#070B14' }}>
        <div className="px-6 pt-5 pb-3">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Crown size={26} weight="fill" style={{ color: '#FFD700' }} />
              <div><h1 className="font-heading text-2xl font-bold" style={{ color: '#F0F4FF' }}>PIRS — Player Intelligence</h1>
              <span className="text-xs" style={{ color: '#4A6080' }}>AI-Driven Churn Scoring & POC Bonusing</span></div>
            </div>
            <div className="flex gap-1">{tabs.map(t => (
              <button key={t.id} onClick={() => setActiveTab(t.id)} className="px-3 py-1.5 rounded text-[10px] font-medium uppercase tracking-wider"
                style={{ background: activeTab === t.id ? 'rgba(255,215,0,0.12)' : 'transparent', color: activeTab === t.id ? '#FFD700' : '#4A6080' }}>{t.label}</button>
            ))}</div>
          </div>
          {/* KPI Strip */}
          {d && (
            <div className="grid grid-cols-7 gap-2">
              {[
                { label: 'Players', value: d.total_players, color: '#F0F4FF', icon: Users },
                { label: 'Active Now', value: d.active_now, color: '#00D97E', icon: Lightning },
                { label: 'Avg Score', value: d.avg_churn_score, color: '#FFD700', icon: Gauge },
                { label: 'Lifetime Coin-In', value: fmt(d.total_lifetime_coin_in), color: '#00B4D8', icon: CurrencyDollar },
                { label: 'POC Today', value: fmt(d.poc_today), color: '#00D97E', icon: Crown },
                { label: 'Awards Today', value: d.poc_today_count || 0, color: '#8B5CF6', icon: Star },
                { label: 'Lapse Risk', value: d.at_risk_players, color: d.at_risk_players > 5 ? '#FF3B3B' : '#FFB800', icon: Warning },
              ].map(k => (
                <div key={k.label} className="rounded-lg p-3" style={{ background: '#111827', border: '1px solid #1A2540' }}>
                  <div className="flex items-center justify-between mb-1"><span className="text-[9px] uppercase tracking-widest" style={{ color: '#4A6080' }}>{k.label}</span><k.icon size={14} style={{ color: k.color }} /></div>
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
                <div className="text-[10px] uppercase tracking-wider mb-3 font-medium" style={{ color: '#4A6080' }}>Churn Score Distribution</div>
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
                <div className="text-[10px] uppercase tracking-wider mb-3 font-medium" style={{ color: '#4A6080' }}>Tiers</div>
                {(d.tiers || []).map(t => (
                  <div key={t.id} className="flex items-center gap-2 px-2 py-1.5 rounded mb-1" style={{ background: '#111827' }}>
                    <Trophy size={12} weight="fill" style={{ color: TIER_C[t.id] || '#4A6080' }} />
                    <span className="text-xs font-medium flex-1" style={{ color: '#F0F4FF' }}>{t.name}</span>
                    <span className="text-[9px] font-mono" style={{ color: '#4A6080' }}>{t.poc_multiplier}x POC</span>
                  </div>
                ))}
              </div>
              <div className="col-span-4 rounded-lg border p-4" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
                <div className="text-[10px] uppercase tracking-wider mb-3 font-medium" style={{ color: '#FFD700' }}>Live Bonus Feed</div>
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
                <div className="px-4 py-2 text-[10px] uppercase tracking-wider font-medium" style={{ color: '#FFD700' }}>Top Players by Churn Score</div>
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
                      { l: 'Play-Back', v: `${(detail.play_back_rate * 100).toFixed(0)}%`, c: '#00D97E' },
                      { l: 'Cash-Out', v: `${(detail.cash_out_rate * 100).toFixed(0)}%`, c: '#FF3B3B' },
                      { l: 'Lapse Risk', v: `${detail.lapse_risk}%`, c: detail.lapse_risk > 50 ? '#FF3B3B' : '#00D97E' },
                      { l: 'POC ROI', v: `${detail.poc_roi_lifetime}:1`, c: '#FFD700' },
                    ].map(m => (
                      <div key={m.l} className="rounded p-2" style={{ background: '#111827' }}>
                        <div className="text-[8px] uppercase tracking-wider" style={{ color: '#4A6080' }}>{m.l}</div>
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

          {/* BONUS RULES */}
          {activeTab === 'rules' && (
            <div className="space-y-2">
              {rules.map(r => (
                <div key={r.id} className="rounded-lg border p-4 flex items-center gap-4" style={{ background: '#0C1322', borderColor: r.is_active ? '#00D97E30' : '#1A2540' }}>
                  <button onClick={() => toggleRule(r.id)} className="w-10 h-5 rounded-full flex items-center transition-colors" style={{ background: r.is_active ? '#00D97E' : '#1A2540', justifyContent: r.is_active ? 'flex-end' : 'flex-start', padding: '2px' }}>
                    <span className="w-4 h-4 rounded-full" style={{ background: '#F0F4FF' }} />
                  </button>
                  <div className="flex-1">
                    <div className="text-xs font-semibold" style={{ color: '#F0F4FF' }}>{r.name}</div>
                    <div className="text-[10px] font-mono" style={{ color: '#4A6080' }}>Trigger: {r.trigger} | Churn min: {r.condition_churn_min || 'any'} | POC: ${r.poc_fixed} | Max/day: {r.max_per_day || r.max_per_session || '∞'}</div>
                  </div>
                  <span className="font-mono text-xs" style={{ color: r.is_active ? '#00D97E' : '#4A6080' }}>{r.is_active ? 'ACTIVE' : 'OFF'}</span>
                </div>
              ))}
            </div>
          )}

          {/* BUSINESS IMPACT / ROI */}
          {activeTab === 'roi' && roi && (
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-lg border p-6 text-center" style={{ background: '#0C1322', borderColor: '#FFD70030' }}>
                <div className="text-[10px] uppercase tracking-wider mb-2" style={{ color: '#4A6080' }}>POC ROI ({roi.period_days} days)</div>
                <div className="font-mono text-5xl font-black" style={{ color: '#FFD700' }}>{roi.roi}:1</div>
                <div className="text-xs mt-2" style={{ color: '#4A6080' }}>Target: {roi.target_roi}:1</div>
              </div>
              <div className="rounded-lg border p-6 space-y-3" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
                <div className="flex justify-between text-sm"><span style={{ color: '#4A6080' }}>Total POC Invested</span><span className="font-mono font-bold" style={{ color: '#FF3B3B' }}>{fmt(roi.total_poc)}</span></div>
                <div className="flex justify-between text-sm"><span style={{ color: '#4A6080' }}>Coin-In Generated</span><span className="font-mono font-bold" style={{ color: '#00D97E' }}>{fmt(roi.estimated_coin_in_from_poc)}</span></div>
                <div className="flex justify-between text-sm"><span style={{ color: '#4A6080' }}>Awards Count</span><span className="font-mono font-bold" style={{ color: '#F0F4FF' }}>{roi.awards_count}</span></div>
                <div className="flex justify-between text-sm border-t pt-2" style={{ borderColor: '#1A2540' }}><span style={{ color: '#F0F4FF' }}>Net Return per $1 POC</span><span className="font-mono font-bold text-lg" style={{ color: '#FFD700' }}>${roi.roi}</span></div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
