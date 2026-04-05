import { useState, useEffect, useCallback, useRef } from 'react';
import api, { API_URL } from '@/lib/api';
import { useNavigate } from 'react-router-dom';
import {
  Cpu, ArrowLeft, Desktop, Warning, Lightning, Trophy,
  CurrencyDollar, Users, Crown, Star, Pulse, Clock,
  SealCheck, WifiX, XCircle, Wrench
} from '@phosphor-icons/react';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import Marquee from 'react-fast-marquee';
import InfoTip from '@/components/InfoTip';

const STATUS_C = { online: '#00D4AA', offline: '#FF3B30', error: '#FF3B30', maintenance: '#F5A623' };
const SEV_C = { critical: '#FF3B30', warning: '#F5A623', info: '#007AFF' };
const TIER_C = { Diamond: '#B9F2FF', Platinum: '#C0C0C0' };

function MiniTip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded px-2 py-1 text-[10px]" style={{ background: '#1A1E2A', border: '1px solid #272E3B' }}>
      <div className="font-mono" style={{ color: '#E8ECF1' }}>{label}</div>
      {payload.map((p, i) => <div key={i} style={{ color: p.color }}>{p.value}</div>)}
    </div>
  );
}

export default function CommandCenterPage() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState(null);
  const [devices, setDevices] = useState([]);
  const [events, setEvents] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [vipAlerts, setVipAlerts] = useState([]);
  const [jackpots, setJackpots] = useState([]);
  const [jpSummary, setJpSummary] = useState(null);
  const [finSummary, setFinSummary] = useState(null);
  const [charts, setCharts] = useState(null);
  const [activeSessions, setActiveSessions] = useState([]);
  const [wsConnected, setWsConnected] = useState(false);
  const [liveCount, setLiveCount] = useState(0);
  const [clock, setClock] = useState(new Date());
  const wsRef = useRef(null);

  // Clock
  useEffect(() => {
    const t = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  // Fetch all data
  const fetchData = useCallback(async () => {
    try {
      const [sumR, devR, evtR, alertR, vipR, jpR, jpSumR, finR, chartR, sessR] = await Promise.all([
        api.get('/dashboard/summary'),
        api.get('/dashboard/device-health?limit=85'),
        api.get('/dashboard/recent-events?limit=25'),
        api.get('/dashboard/recent-alerts?limit=20'),
        api.get('/events/vip-alerts?limit=10'),
        api.get('/jackpots?status=active'),
        api.get('/jackpots/summary'),
        api.get('/financial/summary'),
        api.get('/dashboard/charts'),
        api.get('/players/active'),
      ]);
      setSummary(sumR.data);
      setDevices(devR.data.devices || []);
      setEvents(evtR.data.events || []);
      setAlerts(alertR.data.alerts || []);
      setVipAlerts(vipR.data.alerts || []);
      setJackpots(jpR.data.jackpots || []);
      setJpSummary(jpSumR.data);
      setFinSummary(finR.data);
      setCharts(chartR.data);
      setActiveSessions(sessR.data.sessions || []);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchData(); const iv = setInterval(fetchData, 20000); return () => clearInterval(iv); }, [fetchData]);

  // WebSocket
  useEffect(() => {
    const wsUrl = API_URL.replace('https://', 'wss://').replace('http://', 'ws://');
    let ws, reconnect;
    const connect = () => {
      ws = new WebSocket(`${wsUrl}/api/events/ws`);
      wsRef.current = ws;
      ws.onopen = () => setWsConnected(true);
      ws.onmessage = (msg) => {
        try {
          const evt = JSON.parse(msg.data);
          if (evt.type === 'vip_player_alert') {
            setVipAlerts(prev => [evt, ...prev].slice(0, 10));
          } else {
            setEvents(prev => [evt, ...prev.filter(e => e.id !== evt.id)].slice(0, 30));
            setLiveCount(prev => prev + 1);
          }
        } catch {}
      };
      ws.onclose = () => { setWsConnected(false); reconnect = setTimeout(connect, 3000); };
      ws.onerror = () => ws.close();
    };
    connect();
    return () => { if (reconnect) clearTimeout(reconnect); if (ws) ws.close(); };
  }, []);

  const s = summary;
  const fmt = (v) => v != null ? `$${Number(v).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}` : '--';

  return (
    <div data-testid="command-center" className="fixed inset-0 z-[100] overflow-hidden flex flex-col" style={{ background: '#060810' }}>
      {/* Top Bar */}
      <div className="flex items-center justify-between px-5 h-10 flex-shrink-0" style={{ background: '#0A0C10', borderBottom: '1px solid #1A1E2A' }}>
        <div className="flex items-center gap-3">
          <button data-testid="exit-command-center" onClick={() => navigate('/')} className="flex items-center gap-1.5 text-xs transition-colors" style={{ color: '#6B7A90' }}>
            <ArrowLeft size={14} /> Exit
          </button><InfoTip label="Exit" description="Leaves the full-screen command center and returns you to the normal dashboard." />
          <InfoTip label="Command Center" description="A big-screen, read-only floor overview designed for a control room. Everything updates live — device health, jackpots, VIP players and alerts — so you can spot a problem from across the room." />
          <div className="w-px h-4" style={{ background: '#272E3B' }} />
          <div className="flex items-center gap-2">
            <Cpu size={16} weight="bold" style={{ color: '#00D4AA' }} />
            <span className="font-heading text-sm font-bold tracking-tight" style={{ color: '#E8ECF1' }}>UGG COMMAND CENTER</span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5 text-xs font-mono" style={{ color: wsConnected ? '#00D4AA' : '#FF3B30' }}>
            <Pulse size={14} className={wsConnected ? 'animate-pulse' : ''} />
            {wsConnected ? `LIVE | ${liveCount} events` : 'RECONNECTING'}
          </span>
          <span className="font-mono text-xs tabular-nums" style={{ color: '#E8ECF1' }}>
            {clock.toLocaleTimeString()} UTC
          </span>
        </div>
      </div>

      {/* Main Grid */}
      <div className="flex-1 grid grid-cols-12 grid-rows-6 gap-px p-px overflow-hidden" style={{ background: '#1A1E2A' }}>

        {/* === ROW 1: KPI Strip (spans full width) === */}
        <div className="col-span-2 row-span-1 p-3 flex flex-col justify-center" style={{ background: '#0A0C10' }}>
          <div className="text-[9px] uppercase tracking-widest mb-1 flex items-center" style={{ color: '#6B7A90' }}>Devices<InfoTip label="Devices" description="Total devices on the floor, with a live breakdown of how many are online, offline or in error. Keep an eye on the 'err' number — each one is a machine not earning." /></div>
          <div className="font-mono text-2xl font-black" style={{ color: '#00D4AA' }}>{s?.devices?.total ?? '--'}</div>
          <div className="text-[10px] font-mono" style={{ color: '#6B7A90' }}>{s?.devices?.online ?? 0} on | {s?.devices?.offline ?? 0} off | {s?.devices?.error ?? 0} err</div>
        </div>
        <div className="col-span-2 row-span-1 p-3 flex flex-col justify-center" style={{ background: '#0A0C10' }}>
          <div className="text-[9px] uppercase tracking-widest mb-1 flex items-center" style={{ color: '#6B7A90' }}>Active Alerts<InfoTip label="Active Alerts" description="Unresolved alerts across the floor. The subline splits them by severity — critical first, warning second. If critical isn't zero, action is needed now." /></div>
          <div className="font-mono text-2xl font-black" style={{ color: '#FF3B30' }}>{s?.alerts?.active ?? '--'}</div>
          <div className="text-[10px] font-mono" style={{ color: '#6B7A90' }}>{s?.alerts?.critical ?? 0} crit | {s?.alerts?.warning ?? 0} warn</div>
        </div>
        <div className="col-span-2 row-span-1 p-3 flex flex-col justify-center" style={{ background: '#0A0C10' }}>
          <div className="text-[9px] uppercase tracking-widest mb-1 flex items-center" style={{ color: '#6B7A90' }}>Coin In<InfoTip label="Coin In" description="Total money wagered across the floor today. The 'Hold' underneath is what the house is keeping as a percentage." /></div>
          <div className="font-mono text-2xl font-black" style={{ color: '#007AFF' }}>{fmt(finSummary?.coin_in)}</div>
          <div className="text-[10px] font-mono" style={{ color: '#6B7A90' }}>Hold: {finSummary?.hold_percentage ?? 0}%</div>
        </div>
        <div className="col-span-2 row-span-1 p-3 flex flex-col justify-center" style={{ background: '#0A0C10' }}>
          <div className="text-[9px] uppercase tracking-widest mb-1 flex items-center" style={{ color: '#6B7A90' }}>JP Liability<InfoTip label="JP Liability" description="The total amount currently owed if every progressive jackpot hit right now. 'Active' is how many progressives are running, 'hits' is how many have paid out today." /></div>
          <div className="font-mono text-2xl font-black" style={{ color: '#FFD700' }}>{fmt(jpSummary?.total_current_liability)}</div>
          <div className="text-[10px] font-mono" style={{ color: '#6B7A90' }}>{jpSummary?.active ?? 0} active | {jpSummary?.total_hits ?? 0} hits</div>
        </div>
        <div className="col-span-2 row-span-1 p-3 flex flex-col justify-center" style={{ background: '#0A0C10' }}>
          <div className="text-[9px] uppercase tracking-widest mb-1 flex items-center" style={{ color: '#6B7A90' }}>Events<InfoTip label="Events" description="Total standardized events the platform has processed. Useful as a heartbeat — if this stops moving, the pipeline has stalled." /></div>
          <div className="font-mono text-2xl font-black" style={{ color: '#E8ECF1' }}>{s?.events?.total ?? '--'}</div>
          <div className="text-[10px] font-mono" style={{ color: '#6B7A90' }}>canonical total</div>
        </div>
        <div className="col-span-2 row-span-1 p-3 flex flex-col justify-center" style={{ background: '#0A0C10' }}>
          <div className="text-[9px] uppercase tracking-widest mb-1 flex items-center" style={{ color: '#6B7A90' }}>Active Players<InfoTip label="Active Players" description="Number of players sitting at a machine with their loyalty card inserted right now." /></div>
          <div className="font-mono text-2xl font-black" style={{ color: '#8B5CF6' }}>{activeSessions.length}</div>
          <div className="text-[10px] font-mono" style={{ color: '#6B7A90' }}>sessions now</div>
        </div>

        {/* === ROW 2-3: Device Map (left) + Event Volume Chart (center) + Event Feed (right) === */}
        <div className="col-span-5 row-span-2 p-3 flex flex-col overflow-hidden" style={{ background: '#0A0C10' }}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-[9px] uppercase tracking-widest font-medium flex items-center" style={{ color: '#6B7A90' }}>Device Health Map<InfoTip label="Device Health Map" description="A tile for every device on the floor, color-coded by status. Green is online, red is offline or errored, amber is maintenance. A fast visual way to spot clusters of trouble." /></span>
            <div className="flex gap-2 text-[8px]" style={{ color: '#6B7A90' }}>
              <span className="flex items-center gap-0.5"><SealCheck size={8} style={{ color: '#00D4AA' }} />On</span>
              <span className="flex items-center gap-0.5"><WifiX size={8} style={{ color: '#FF3B30' }} />Off</span>
              <span className="flex items-center gap-0.5"><Wrench size={8} style={{ color: '#F5A623' }} />Maint</span>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto">
            <div className="grid grid-cols-10 gap-1" data-testid="cc-device-grid">
              {devices.map(d => (
                <div key={d.id} className="rounded p-1 text-center" style={{ background: `${STATUS_C[d.status]}08`, border: `1px solid ${STATUS_C[d.status]}25` }}>
                  <div className="font-mono text-[7px] font-bold truncate" style={{ color: STATUS_C[d.status] }}>{d.external_ref}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="col-span-4 row-span-2 p-3 flex flex-col" style={{ background: '#0A0C10' }}>
          <span className="text-[9px] uppercase tracking-widest font-medium mb-2 flex items-center" style={{ color: '#6B7A90' }}>Event Volume (24h)<InfoTip label="Event Volume (24h)" description="Hour-by-hour count of events flowing in for the last day. A flatline means the pipeline has stopped; a spike usually means an incident is unfolding." /></span>
          <div className="flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={charts?.hourly_event_volume || []}>
                <defs>
                  <linearGradient id="ccEvtG" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00D4AA" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#00D4AA" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="hour" tick={{ fill: '#6B7A90', fontSize: 8 }} axisLine={false} tickLine={false} interval={4} />
                <YAxis tick={{ fill: '#6B7A90', fontSize: 8 }} axisLine={false} tickLine={false} width={25} />
                <Tooltip content={<MiniTip />} />
                <Area type="monotone" dataKey="events" stroke="#00D4AA" fill="url(#ccEvtG)" strokeWidth={1.5} name="Events" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          {/* Severity distribution inline */}
          <div className="flex items-center gap-3 mt-1">
            <ResponsiveContainer width="100%" height={50}>
              <BarChart data={charts?.severity_distribution || []} barSize={14}>
                <XAxis dataKey="name" tick={{ fill: '#6B7A90', fontSize: 8 }} axisLine={false} tickLine={false} />
                <Bar dataKey="value" radius={[2, 2, 0, 0]}>
                  {(charts?.severity_distribution || []).map((e, i) => {
                    const c = { Info: '#007AFF', Warning: '#F5A623', Critical: '#FF3B30' };
                    return <Cell key={i} fill={c[e.name] || '#6B7A90'} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="col-span-3 row-span-2 flex flex-col overflow-hidden" style={{ background: '#0A0C10' }}>
          <div className="px-3 pt-3 pb-1 flex items-center justify-between">
            <span className="text-[9px] uppercase tracking-widest font-medium flex items-center" style={{ color: '#6B7A90' }}>Live Event Feed<InfoTip label="Live Event Feed" description="Every event from every device as it arrives. Newest at the top. Watch this to get a feel for what's happening in real time." /></span>
            <span className={`w-1.5 h-1.5 rounded-full ${wsConnected ? 'pulse-online' : ''}`} style={{ background: wsConnected ? '#00D4AA' : '#FF3B30' }} />
          </div>
          <div className="flex-1 overflow-y-auto" data-testid="cc-event-feed">
            {events.map((evt, i) => (
              <div key={evt.id || i} className={`px-3 py-1 border-b text-[10px] ${i === 0 ? 'animate-slide-in animate-fade-highlight' : ''}`} style={{ borderColor: '#1A1E2A' }}>
                <div className="flex items-center justify-between">
                  <span className="font-mono" style={{ color: '#6B7A90' }}>{new Date(evt.occurred_at).toLocaleTimeString()}</span>
                  <span className="font-mono px-1 py-0.5 rounded text-[8px]" style={{ background: `${SEV_C[evt.severity] || '#6B7A90'}20`, color: SEV_C[evt.severity] || '#6B7A90' }}>{evt.severity}</span>
                </div>
                <div className="font-mono font-medium truncate" style={{ color: '#E8ECF1' }}>{evt.event_type}</div>
                <div className="truncate" style={{ color: '#6B7A90' }}>{evt.device_ref || evt.device_id?.slice(0, 8)}</div>
              </div>
            ))}
          </div>
        </div>

        {/* === ROW 4-5: Jackpots (left) + VIP Alerts (center) + Active Players (right) === */}
        <div className="col-span-5 row-span-2 p-3 flex flex-col overflow-hidden" style={{ background: '#0A0C10' }}>
          <div className="flex items-center gap-2 mb-2">
            <Trophy size={14} style={{ color: '#FFD700' }} />
            <span className="text-[9px] uppercase tracking-widest font-medium flex items-center" style={{ color: '#6B7A90' }}>Progressive Jackpots<InfoTip label="Progressive Jackpots" description="Live status of your progressive jackpot pools. The bar shows how close each one is to its ceiling — as it gets near the top, a hit becomes more likely." /></span>
          </div>
          <div className="flex-1 overflow-y-auto space-y-1.5" data-testid="cc-jackpots">
            {jackpots.slice(0, 6).map(jp => {
              const pct = ((jp.current_amount - jp.base_amount) / (jp.ceiling_amount - jp.base_amount) * 100);
              return (
                <div key={jp.id} className="rounded p-2.5" style={{ background: '#12151C', border: '1px solid #1A1E2A' }}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium" style={{ color: '#E8ECF1' }}>{jp.name}</span>
                    <span className="text-[9px] font-mono px-1 py-0.5 rounded capitalize" style={{ background: `${STATUS_C[jp.status] || '#6B7A90'}15`, color: STATUS_C[jp.status] || '#6B7A90' }}>{jp.type}</span>
                  </div>
                  <div className="font-mono text-lg font-black" style={{ color: '#FFD700' }}>${jp.current_amount?.toLocaleString()}</div>
                  <div className="h-1 rounded-full mt-1 overflow-hidden" style={{ background: '#272E3B' }}>
                    <div className="h-full rounded-full" style={{ width: `${Math.min(pct, 100)}%`, background: pct > 80 ? '#FF3B30' : pct > 50 ? '#F5A623' : '#00D4AA' }} />
                  </div>
                  <div className="flex justify-between text-[8px] font-mono mt-0.5">
                    <span style={{ color: '#6B7A90' }}>{fmt(jp.base_amount)}</span>
                    <span style={{ color: '#6B7A90' }}>{jp.linked_device_count} devices | {jp.contribution_rate}%</span>
                    <span style={{ color: '#6B7A90' }}>{fmt(jp.ceiling_amount)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="col-span-4 row-span-2 p-3 flex flex-col overflow-hidden" style={{ background: '#0A0C10' }}>
          <div className="flex items-center gap-2 mb-2">
            <Crown size={14} weight="fill" style={{ color: '#FFD700' }} />
            <span className="text-[9px] uppercase tracking-widest font-medium flex items-center" style={{ color: '#6B7A90' }}>VIP Player Alerts<InfoTip label="VIP Player Alerts" description="Real-time notifications when a Platinum or Diamond tier player cards in. Use these to dispatch hosts for a personal welcome." /></span>
          </div>
          <div className="flex-1 overflow-y-auto space-y-1" data-testid="cc-vip-alerts">
            {vipAlerts.length === 0 ? (
              <div className="flex-1 flex items-center justify-center text-[10px]" style={{ color: '#6B7A90' }}>
                Waiting for Platinum/Diamond player card-ins...
              </div>
            ) : (
              vipAlerts.map(a => (
                <div key={a.id} className="rounded p-2.5" style={{ background: `${TIER_C[a.player_tier] || '#6B7A90'}06`, border: `1px solid ${TIER_C[a.player_tier] || '#272E3B'}20` }}>
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <Crown size={12} weight="fill" style={{ color: TIER_C[a.player_tier] || '#FFD700' }} />
                      <span className="text-xs font-semibold" style={{ color: '#E8ECF1' }}>{a.player_name}</span>
                      <span className="text-[8px] font-mono px-1 py-0.5 rounded flex items-center gap-0.5" style={{ background: `${TIER_C[a.player_tier]}15`, color: TIER_C[a.player_tier] }}>
                        <Star size={8} weight="fill" /> {a.player_tier}
                      </span>
                    </div>
                    <span className="text-[9px] font-mono" style={{ color: '#6B7A90' }}>{new Date(a.occurred_at).toLocaleTimeString()}</span>
                  </div>
                  <div className="flex items-center gap-3 text-[9px] font-mono">
                    <span style={{ color: '#00D4AA' }}>${(a.lifetime_value / 1000).toFixed(1)}k lifetime</span>
                    <span style={{ color: '#6B7A90' }}>{a.device_ref}</span>
                    <span style={{ color: '#6B7A90' }}>{a.total_visits} visits</span>
                  </div>
                  <div className="flex gap-1 mt-1">
                    {a.preferred_games?.slice(0, 3).map(g => (
                      <span key={g} className="text-[7px] px-1 py-0.5 rounded" style={{ background: '#1A1E2A', color: '#6B7A90' }}>{g}</span>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="col-span-3 row-span-2 p-3 flex flex-col overflow-hidden" style={{ background: '#0A0C10' }}>
          <div className="flex items-center gap-2 mb-2">
            <Users size={14} style={{ color: '#8B5CF6' }} />
            <span className="text-[9px] uppercase tracking-widest font-medium flex items-center" style={{ color: '#6B7A90' }}>Active Sessions ({activeSessions.length})<InfoTip label="Active Sessions" description="Players currently sitting at a machine with their loyalty card inserted. Shows their tier, time in seat, amount wagered and net result so far." /></span>
          </div>
          <div className="flex-1 overflow-y-auto space-y-1" data-testid="cc-active-sessions">
            {activeSessions.slice(0, 12).map(sess => (
              <div key={sess.id} className="rounded px-2.5 py-2 flex items-center gap-2" style={{ background: '#12151C', border: '1px solid #1A1E2A' }}>
                <span className="w-1.5 h-1.5 rounded-full pulse-online" style={{ background: '#00D4AA' }} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] font-medium truncate" style={{ color: '#E8ECF1' }}>{sess.player_name}</span>
                    <span className="text-[7px] font-mono px-1 py-0.5 rounded" style={{ background: `${TIER_C[sess.player_tier] || '#6B7A90'}15`, color: TIER_C[sess.player_tier] || '#6B7A90' }}>{sess.player_tier}</span>
                  </div>
                  <div className="text-[8px] font-mono" style={{ color: '#6B7A90' }}>
                    {sess.device_ref} | {sess.duration_minutes}m | ${sess.total_wagered?.toLocaleString()}
                  </div>
                </div>
                <span className="text-[9px] font-mono" style={{ color: sess.net_result >= 0 ? '#00D4AA' : '#FF3B30' }}>
                  {sess.net_result >= 0 ? '+' : ''}{fmt(sess.net_result)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* === ROW 6: Alert Ticker (full width) === */}
        <div className="col-span-12 row-span-1 flex items-center overflow-hidden" style={{ background: '#0A0C10' }}>
          {alerts.length > 0 ? (
            <Marquee speed={50} gradient={false} pauseOnHover className="h-full">
              {alerts.map(a => (
                <span key={a.id} className="inline-flex items-center gap-2 px-5 font-mono text-[11px]" style={{ color: SEV_C[a.severity] }}>
                  <span className="w-1.5 h-1.5 rounded-full" style={{ background: SEV_C[a.severity] }} />
                  {a.message}
                </span>
              ))}
            </Marquee>
          ) : (
            <div className="w-full text-center text-[10px] font-mono" style={{ color: '#272E3B' }}>NO ACTIVE ALERTS</div>
          )}
        </div>
      </div>
    </div>
  );
}
