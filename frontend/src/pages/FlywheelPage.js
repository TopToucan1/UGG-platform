import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import { Atom, Lightning, Users, ChartBar, GearSix, ListChecks, Play, Pause, ArrowClockwise, ToggleLeft, ToggleRight } from '@phosphor-icons/react';
import InfoTip from '@/components/InfoTip';

const FAMILY_COLORS = {
  loss_recovery: '#FF6B6B', milestone_proximity: '#FFB800', re_entry: '#00D4AA',
  low_friction_earn_path: '#8B5CF6', social_proof: '#00B4D8', group_momentum: '#EC4899',
  shareable_moment: '#FFD700', interest_match: '#06B6D4', resource_deployment: '#F97316',
  session_extension: '#10B981', cold_streak_comfort: '#6366F1',
};

const STATUS_COLORS = {
  approved: '#00D4AA', dispatched: '#00B4D8', delivered: '#FFD700',
  rejected: '#FF6B6B', failed: '#FF3B30', completed: '#6B7A90',
};

export default function FlywheelPage() {
  const [tab, setTab] = useState('overview');
  const [dashboard, setDashboard] = useState(null);
  const [rules, setRules] = useState([]);
  const [actions, setActions] = useState([]);
  const [profiles, setProfiles] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      if (tab === 'overview') {
        const [d, l] = await Promise.allSettled([api.get('/flywheel/dashboard'), api.get('/flywheel/logs', { params: { limit: 20 } })]);
        if (d.status === 'fulfilled') setDashboard(d.value.data);
        if (l.status === 'fulfilled') setLogs(l.value.data.logs || []);
      } else if (tab === 'rules') {
        const r = await api.get('/flywheel/rules');
        setRules(r.data.rules || []);
      } else if (tab === 'actions') {
        const a = await api.get('/flywheel/actions', { params: { limit: 100 } });
        setActions(a.data.actions || []);
      } else if (tab === 'profiles') {
        const p = await api.get('/flywheel/profiles', { params: { limit: 100 } });
        setProfiles(p.data.profiles || []);
      } else if (tab === 'logs') {
        const l = await api.get('/flywheel/logs', { params: { limit: 100 } });
        setLogs(l.data.logs || []);
      }
    } catch { /* API not available */ } finally { setLoading(false); }
  }, [tab]);

  useEffect(() => { load(); const t = setInterval(load, tab === 'overview' ? 5000 : 10000); return () => clearInterval(t); }, [load, tab]);

  const toggleRule = async (key) => { await api.post(`/flywheel/rules/${key}/toggle`); load(); };
  const runWorker = async (name) => { await api.post(`/flywheel/engine/run-now/${name}`); load(); };
  const pauseEngine = async () => { await api.post('/flywheel/engine/pause'); load(); };
  const resumeEngine = async () => { await api.post('/flywheel/engine/resume'); load(); };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: ChartBar },
    { id: 'rules', label: 'Rules', icon: ListChecks },
    { id: 'actions', label: 'Action Queue', icon: Lightning },
    { id: 'profiles', label: 'Profiles', icon: Users },
    { id: 'logs', label: 'Worker Logs', icon: ArrowClockwise },
    { id: 'config', label: 'Engine Control', icon: GearSix },
  ];

  return (
    <div data-testid="flywheel-page" className="space-y-4">
      <h1 className="font-heading text-2xl font-bold tracking-tight flex items-center gap-3" style={{ color: '#E8ECF1' }}>
        <Atom size={24} /> FlywheelOS Engagement Engine
        <InfoTip size={14} label="FlywheelOS" description="Intelligent engagement engine that automatically evaluates player behavior, scores next-best-actions, and delivers targeted POC offers to EGMs. Powered by 11 rule families, a multi-factor decision engine, and 6 background workers." />
      </h1>

      <div className="flex gap-2 border-b" style={{ borderColor: '#272E3B' }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className="flex items-center gap-2 px-4 py-2.5 text-xs font-medium uppercase tracking-wider transition-colors"
            style={{ color: tab === t.id ? '#00D4AA' : '#6B7A90', borderBottom: tab === t.id ? '2px solid #00D4AA' : '2px solid transparent' }}>
            <t.icon size={16} /> {t.label}
          </button>
        ))}
      </div>

      {loading && !dashboard && <div className="text-center py-8 text-sm" style={{ color: '#6B7A90' }}>Loading...</div>}

      {/* ═══ OVERVIEW ═══ */}
      {tab === 'overview' && dashboard && (
        <div className="space-y-4">
          <div className="grid grid-cols-4 gap-4">
            <Stat label="Actions Today" value={dashboard.actions_approved} accent info="Approved engagement actions delivered to players today." />
            <Stat label="POC Awarded" value={`$${dashboard.poc_awarded_today?.toFixed(2)}`} accent info="Total Play-Only Credits issued by FlywheelOS today." />
            <Stat label="Events Processed" value={dashboard.events_today} info="Player events mapped and evaluated by the engagement pipeline today." />
            <Stat label="Active Rules" value={dashboard.rules_active} info="Number of enabled rule families currently evaluating events." />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
              <div className="flex items-center text-[11px] uppercase tracking-wider mb-3" style={{ color: '#6B7A90' }}>
                Lifecycle Distribution <InfoTip description="How players are classified by engagement stage. 'at_risk' and 'dormant' players are primary targets for re-entry rules." />
              </div>
              <div className="space-y-2">
                {(dashboard.lifecycle_distribution || []).map(l => (
                  <div key={l.stage} className="flex items-center justify-between text-xs">
                    <span className="px-2 py-0.5 rounded font-mono text-[10px] uppercase" style={{
                      background: l.stage === 'power' ? 'rgba(0,212,170,0.1)' : l.stage === 'at_risk' ? 'rgba(255,59,48,0.1)' : l.stage === 'dormant' ? 'rgba(107,122,144,0.1)' : 'rgba(0,180,216,0.1)',
                      color: l.stage === 'power' ? '#00D4AA' : l.stage === 'at_risk' ? '#FF6B6B' : l.stage === 'dormant' ? '#6B7A90' : '#00B4D8',
                    }}>{l.stage}</span>
                    <span className="font-mono" style={{ color: '#E8ECF1' }}>{l.count}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
              <div className="flex items-center text-[11px] uppercase tracking-wider mb-3" style={{ color: '#6B7A90' }}>
                Top Rule Families Today <InfoTip description="Which rule families generated the most approved actions today." />
              </div>
              <div className="space-y-2">
                {(dashboard.top_families || []).map(f => (
                  <div key={f.family} className="flex items-center justify-between text-xs">
                    <span className="font-mono" style={{ color: FAMILY_COLORS[f.family] || '#A3AEBE' }}>{f.family}</span>
                    <span className="font-mono" style={{ color: '#E8ECF1' }}>{f.count}</span>
                  </div>
                ))}
                {(dashboard.top_families || []).length === 0 && <div className="text-xs" style={{ color: '#6B7A90' }}>No actions yet today.</div>}
              </div>
            </div>
          </div>
          {logs.length > 0 && (
            <div className="rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
              <div className="flex items-center text-[11px] uppercase tracking-wider mb-3" style={{ color: '#6B7A90' }}>
                Recent Worker Runs <InfoTip description="Execution logs from the 6 background workers. Green = completed, red = failed." />
              </div>
              <div className="space-y-1">
                {logs.slice(0, 10).map(l => (
                  <div key={l.id} className="flex items-center justify-between text-[11px] font-mono">
                    <span style={{ color: '#A3AEBE' }}>{l.worker_name}</span>
                    <span style={{ color: l.status === 'completed' ? '#00D4AA' : l.status === 'failed' ? '#FF6B6B' : '#FFB800' }}>{l.status}</span>
                    <span style={{ color: '#6B7A90' }}>{l.items_processed} items</span>
                    <span style={{ color: '#6B7A90' }}>{l.summary?.slice(0, 50)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ═══ RULES ═══ */}
      {tab === 'rules' && (
        <div className="rounded border overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }}>
          <div className="grid grid-cols-[2fr_1.5fr_1fr_1fr_1fr_auto] gap-2 px-4 py-2 text-[11px] uppercase tracking-wider font-medium border-b" style={{ color: '#6B7A90', borderColor: '#272E3B' }}>
            <div className="flex items-center">Rule Name <InfoTip description="Human-readable name. Click toggle to enable/disable without deleting." /></div>
            <div>Family</div><div>Trigger</div><div>Priority</div><div>POC Base</div><div>Active</div>
          </div>
          {rules.map(r => (
            <div key={r.key} className="grid grid-cols-[2fr_1.5fr_1fr_1fr_1fr_auto] gap-2 px-4 py-2.5 border-b items-center text-xs" style={{ borderColor: '#272E3B40', opacity: r.enabled ? 1 : 0.5 }}>
              <div style={{ color: '#E8ECF1' }}>{r.name || r.key}</div>
              <div><span className="px-1.5 py-0.5 rounded text-[10px] font-mono" style={{ background: `${FAMILY_COLORS[r.family] || '#6B7A90'}20`, color: FAMILY_COLORS[r.family] || '#6B7A90' }}>{r.family}</span></div>
              <div className="font-mono" style={{ color: '#A3AEBE' }}>{r.trigger_type}</div>
              <div className="font-mono" style={{ color: '#E8ECF1' }}>{r.priority}</div>
              <div className="font-mono" style={{ color: r.poc_base > 0 ? '#00D4AA' : '#6B7A90' }}>{r.poc_base > 0 ? `$${r.poc_base}` : '--'}</div>
              <button onClick={() => toggleRule(r.key)} className="p-1" style={{ color: r.enabled ? '#00D4AA' : '#6B7A90' }}>
                {r.enabled ? <ToggleRight size={20} weight="fill" /> : <ToggleLeft size={20} />}
              </button>
            </div>
          ))}
        </div>
      )}

      {/* ═══ ACTION QUEUE ═══ */}
      {tab === 'actions' && (
        <div className="rounded border overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }}>
          <div className="grid grid-cols-[1.5fr_1.5fr_1fr_1fr_1fr_1fr] gap-2 px-4 py-2 text-[11px] uppercase tracking-wider font-medium border-b" style={{ color: '#6B7A90', borderColor: '#272E3B' }}>
            <div>Player</div><div>Rule</div><div>Family</div><div>POC</div><div>Score</div><div>Status</div>
          </div>
          {actions.length === 0 ? (
            <div className="px-4 py-8 text-center text-xs" style={{ color: '#6B7A90' }}>No actions yet. The engine generates actions as players interact with EGMs.</div>
          ) : actions.map(a => (
            <div key={a.id} className="grid grid-cols-[1.5fr_1.5fr_1fr_1fr_1fr_1fr] gap-2 px-4 py-2.5 border-b items-center text-xs" style={{ borderColor: '#272E3B40' }}>
              <div className="font-mono truncate" style={{ color: '#E8ECF1' }}>{a.actor_id?.slice(0, 12)}</div>
              <div style={{ color: '#A3AEBE' }}>{a.rule_key}</div>
              <div><span className="px-1.5 py-0.5 rounded text-[10px] font-mono" style={{ background: `${FAMILY_COLORS[a.family] || '#6B7A90'}20`, color: FAMILY_COLORS[a.family] || '#6B7A90' }}>{a.family}</span></div>
              <div className="font-mono" style={{ color: a.poc_amount > 0 ? '#00D4AA' : '#6B7A90' }}>{a.poc_amount > 0 ? `$${a.poc_amount?.toFixed(2)}` : '--'}</div>
              <div className="font-mono" style={{ color: '#E8ECF1' }}>{(a.score * 100).toFixed(0)}%</div>
              <div><span className="px-1.5 py-0.5 rounded text-[10px] font-mono uppercase" style={{ background: `${STATUS_COLORS[a.status] || '#6B7A90'}20`, color: STATUS_COLORS[a.status] || '#6B7A90' }}>{a.status}</span></div>
            </div>
          ))}
        </div>
      )}

      {/* ═══ PROFILES ═══ */}
      {tab === 'profiles' && (
        <div className="rounded border overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }}>
          <div className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr_1fr] gap-2 px-4 py-2 text-[11px] uppercase tracking-wider font-medium border-b" style={{ color: '#6B7A90', borderColor: '#272E3B' }}>
            <div>Player</div><div>Stage</div><div>Fatigue</div><div>Sessions</div><div>Events/7d</div><div>Actions Today</div>
          </div>
          {profiles.length === 0 ? (
            <div className="px-4 py-8 text-center text-xs" style={{ color: '#6B7A90' }}>No profiles yet. Profiles are created as players interact via PIN sessions.</div>
          ) : profiles.map(p => (
            <div key={p.actor_id} className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr_1fr] gap-2 px-4 py-2.5 border-b items-center text-xs" style={{ borderColor: '#272E3B40' }}>
              <div className="font-mono truncate" style={{ color: '#E8ECF1' }}>{p.actor_id?.slice(0, 16)}</div>
              <div><span className="px-1.5 py-0.5 rounded text-[10px] font-mono uppercase" style={{
                background: p.lifecycle_stage === 'power' ? 'rgba(0,212,170,0.1)' : p.lifecycle_stage === 'at_risk' ? 'rgba(255,59,48,0.1)' : 'rgba(0,180,216,0.1)',
                color: p.lifecycle_stage === 'power' ? '#00D4AA' : p.lifecycle_stage === 'at_risk' ? '#FF6B6B' : '#00B4D8',
              }}>{p.lifecycle_stage}</span></div>
              <div className="font-mono" style={{ color: p.fatigue_score > 0.5 ? '#FF6B6B' : '#A3AEBE' }}>{(p.fatigue_score * 100).toFixed(0)}%</div>
              <div className="font-mono" style={{ color: '#E8ECF1' }}>{p.session_count || 0}</div>
              <div className="font-mono" style={{ color: '#E8ECF1' }}>{p.events_last_7_days || 0}</div>
              <div className="font-mono" style={{ color: '#E8ECF1' }}>{p.actions_today || 0}</div>
            </div>
          ))}
        </div>
      )}

      {/* ═══ WORKER LOGS ═══ */}
      {tab === 'logs' && (
        <div className="rounded border overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }}>
          <div className="grid grid-cols-[1.5fr_1fr_1fr_1fr_3fr] gap-2 px-4 py-2 text-[11px] uppercase tracking-wider font-medium border-b" style={{ color: '#6B7A90', borderColor: '#272E3B' }}>
            <div>Worker</div><div>Status</div><div>Items</div><div>Time</div><div>Summary</div>
          </div>
          {logs.map(l => (
            <div key={l.id} className="grid grid-cols-[1.5fr_1fr_1fr_1fr_3fr] gap-2 px-4 py-2 border-b items-center text-[11px] font-mono" style={{ borderColor: '#272E3B40' }}>
              <div style={{ color: '#E8ECF1' }}>{l.worker_name}</div>
              <div style={{ color: l.status === 'completed' ? '#00D4AA' : l.status === 'failed' ? '#FF6B6B' : '#FFB800' }}>{l.status}</div>
              <div style={{ color: '#A3AEBE' }}>{l.items_processed}</div>
              <div style={{ color: '#6B7A90' }}>{l.started_at ? new Date(l.started_at).toLocaleTimeString() : '--'}</div>
              <div className="truncate" style={{ color: '#6B7A90' }}>{l.summary || l.error_details || '--'}</div>
            </div>
          ))}
        </div>
      )}

      {/* ═══ ENGINE CONTROL ═══ */}
      {tab === 'config' && dashboard && (
        <div className="space-y-4">
          <div className="rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
            <div className="flex items-center text-[11px] uppercase tracking-wider mb-3" style={{ color: '#6B7A90' }}>
              Engine Status <InfoTip description="Shows whether the engine is running and the state of each background worker." />
            </div>
            <div className="flex items-center gap-4 mb-4">
              <span className="flex items-center gap-2 text-sm" style={{ color: dashboard.engine?.enabled ? '#00D4AA' : '#FF6B6B' }}>
                <span className="w-2.5 h-2.5 rounded-full" style={{ background: dashboard.engine?.started ? '#00D4AA' : '#FF6B6B' }} />
                {dashboard.engine?.started ? 'Running' : 'Stopped'}
              </span>
              <div className="flex items-center gap-2">
                <button onClick={pauseEngine} className="flex items-center gap-1 px-3 py-1.5 rounded text-xs" style={{ background: '#272E3B', color: '#A3AEBE' }}>
                  <Pause size={14} /> Pause
                </button>
                <button onClick={resumeEngine} className="flex items-center gap-1 px-3 py-1.5 rounded text-xs" style={{ background: '#00D4AA', color: '#0A0C10' }}>
                  <Play size={14} /> Resume
                </button>
              </div>
            </div>
            <div className="space-y-2">
              {(dashboard.engine?.workers || []).map(w => (
                <div key={w.name} className="flex items-center justify-between text-xs">
                  <span className="font-mono" style={{ color: '#E8ECF1' }}>{w.name}</span>
                  <span style={{ color: w.running ? '#00D4AA' : '#6B7A90' }}>{w.running ? 'active' : 'paused'}</span>
                  <span className="font-mono text-[10px]" style={{ color: '#6B7A90' }}>{w.last_run ? new Date(w.last_run).toLocaleTimeString() : 'never'}</span>
                  <button onClick={() => runWorker(w.name)} className="px-2 py-1 rounded text-[10px]" style={{ background: '#272E3B', color: '#A3AEBE' }}>
                    <ArrowClockwise size={12} /> Run Now
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, accent, info }) {
  return (
    <div className="rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
      <div className="flex items-center text-[11px] uppercase tracking-wider mb-2" style={{ color: '#6B7A90' }}>
        {label}{info && <InfoTip description={info} />}
      </div>
      <div className="font-mono text-2xl font-bold" style={{ color: accent ? '#00D4AA' : '#E8ECF1' }}>{value ?? '--'}</div>
    </div>
  );
}
