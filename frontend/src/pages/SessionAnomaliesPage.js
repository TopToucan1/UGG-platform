import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import { Warning, CheckCircle, XCircle, Funnel } from '@phosphor-icons/react';
import InfoTip from '@/components/InfoTip';

const RULE_LABELS = {
  RAPID_CYCLING: 'Rapid Cycling',
  LOW_PLAY_FLIP: 'Low Play Flip',
  HOPPER: 'Device Hopping',
  PIN_CHURN: 'PIN Churn',
  MICRO_SESSION: 'Micro Session',
};

const RULE_DESCRIPTIONS = {
  RAPID_CYCLING: 'Same player started 4 or more credit sessions on the same EGM within 30 minutes. Can indicate bonus farming, promotion abuse, or unusual play patterns. Investigate — legitimate players rarely do this.',
  LOW_PLAY_FLIP: 'Player dropped $50 or more, played 3 or fewer games, then cashed out 90%+ of what they put in. This is the classic money-movement / laundering pattern — someone using the EGM as an ATM. HIGH PRIORITY: always investigate.',
  HOPPER: 'Same player active on 3 or more different EGMs within 60 minutes. May indicate PIN sharing (someone gave their PIN to a friend) or unusual chase behavior. Check if promotion qualification is being gamed.',
  PIN_CHURN: 'Player logged out of their PIN 5 or more times in an hour while still having credits on the machine. Could indicate PIN sharing between people at the same EGM or very indecisive play.',
  MICRO_SESSION: 'A session that lasted under 60 seconds with 0 or 1 games played. Usually harmless (player changed their mind), but worth noting if many come from the same player.',
};

const SEVERITY_COLOR = {
  HIGH: { bg: 'rgba(255,59,48,0.12)', fg: '#FF6B6B', border: '#FF3B30' },
  MEDIUM: { bg: 'rgba(255,184,0,0.12)', fg: '#FFB800', border: '#FFB800' },
  LOW: { bg: 'rgba(0,212,170,0.12)', fg: '#00D4AA', border: '#00D4AA' },
};

export default function SessionAnomaliesPage() {
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('open');
  const [filterSeverity, setFilterSeverity] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/players-pin/anomalies', {
        params: {
          status: filterStatus || undefined,
          severity: filterSeverity || undefined,
          limit: 200,
        },
      });
      setAnomalies(res.data.anomalies || []);
    } finally { setLoading(false); }
  }, [filterStatus, filterSeverity]);

  useEffect(() => { load(); const t = setInterval(load, 6000); return () => clearInterval(t); }, [load]);

  const act = async (id, action) => {
    try {
      await api.post(`/players-pin/anomalies/${id}/${action}`);
      load();
    } catch {}
  };

  const counts = {
    high: anomalies.filter(a => a.severity === 'HIGH').length,
    medium: anomalies.filter(a => a.severity === 'MEDIUM').length,
    low: anomalies.filter(a => a.severity === 'LOW').length,
  };

  return (
    <div data-testid="session-anomalies-page" className="space-y-4">
      <h1 className="font-heading text-2xl font-bold tracking-tight flex items-center gap-3" style={{ color: '#E8ECF1' }}>
        <Warning size={24} /> Session Anomalies
        <InfoTip
          size={14}
          label="Session Anomalies"
          description="Automatic detection of suspicious player behavior. UGG watches every closed credit session and flags patterns that suggest gaming-the-system, money movement, PIN sharing, or bonus abuse. Review HIGH severity items daily."
        />
      </h1>

      <div className="grid grid-cols-4 gap-4">
        <Stat label="Total Shown" value={anomalies.length} info="Number of anomalies matching your current filters. Adjust the filters below to change what's counted." />
        <Stat label="High Severity" value={counts.high} warn={counts.high > 0} info="Anomalies flagged as HIGH severity (LOW_PLAY_FLIP, RAPID_CYCLING, HOPPER). These should be investigated the same day." />
        <Stat label="Medium" value={counts.medium} info="Medium severity anomalies (PIN_CHURN). Review weekly or when patterns accumulate on the same player." />
        <Stat label="Low" value={counts.low} info="Low severity anomalies (MICRO_SESSION). Usually benign — check only if clustering on a specific player." />
      </div>

      <div className="flex items-center gap-3">
        <Funnel size={16} style={{ color: '#6B7A90' }} />
        <div className="flex items-center">
          <Select value={filterStatus} onChange={setFilterStatus} options={[
            { value: 'open', label: 'Open' },
            { value: 'acknowledged', label: 'Acknowledged' },
            { value: 'dismissed', label: 'Dismissed' },
            { value: '', label: 'All Statuses' },
          ]} />
          <InfoTip description="Filter by status. 'Open' = needs review. 'Acknowledged' = someone is looking into it. 'Dismissed' = confirmed false positive. Default is Open so you only see items that still need attention." />
        </div>
        <div className="flex items-center">
          <Select value={filterSeverity} onChange={setFilterSeverity} options={[
            { value: '', label: 'All Severities' },
            { value: 'HIGH', label: 'High' },
            { value: 'MEDIUM', label: 'Medium' },
            { value: 'LOW', label: 'Low' },
          ]} />
          <InfoTip description="Filter by severity level. Start with HIGH when reviewing for the first time each day." />
        </div>
      </div>

      <div className="space-y-2">
        {loading ? (
          <div className="text-center py-8 text-xs" style={{ color: '#6B7A90' }}>Loading...</div>
        ) : anomalies.length === 0 ? (
          <div className="text-center py-8 text-xs" style={{ color: '#6B7A90' }}>No anomalies match the current filter.</div>
        ) : anomalies.map(a => {
          const c = SEVERITY_COLOR[a.severity] || SEVERITY_COLOR.LOW;
          return (
            <div key={a.id} className="rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B', borderLeft: `3px solid ${c.border}` }}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-medium px-2 py-0.5 rounded font-mono uppercase" style={{ background: c.bg, color: c.fg }}>
                      {a.severity}
                    </span>
                    <InfoTip description={a.severity === 'HIGH' ? 'HIGH severity — investigate today. Strong pattern of gaming-the-system behavior.' : a.severity === 'MEDIUM' ? 'MEDIUM severity — investigate this week or if pattern repeats for the same player.' : 'LOW severity — usually harmless. Check only if clustering.'} />
                    <span className="text-sm font-medium" style={{ color: '#E8ECF1' }}>
                      {RULE_LABELS[a.rule_code] || a.rule_code}
                    </span>
                    <InfoTip label={RULE_LABELS[a.rule_code] || a.rule_code} description={RULE_DESCRIPTIONS[a.rule_code] || 'Custom rule triggered. See detail text below for specifics.'} />
                    <span className="text-[10px] font-mono" style={{ color: '#6B7A90' }}>
                      {new Date(a.detected_at).toLocaleString()}
                    </span>
                    {a.status !== 'open' && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded font-mono uppercase" style={{ background: 'rgba(107,122,144,0.15)', color: '#A3AEBE' }}>
                        {a.status}
                      </span>
                    )}
                  </div>
                  <div className="text-xs mt-1.5" style={{ color: '#A3AEBE' }}>{a.detail}</div>
                  {a.player_id && (
                    <div className="text-[11px] font-mono mt-1 flex items-center" style={{ color: '#6B7A90' }}>
                      player: {a.player_id.slice(0, 12)} | sessions: {(a.related_session_ids || []).length}
                      <InfoTip description="Shows which player triggered this anomaly and how many sessions are implicated. If the same player ID appears across many anomalies, consider deactivating their account until you can investigate in person." />
                    </div>
                  )}
                </div>
                {a.status === 'open' && (
                  <div className="flex items-center gap-0.5 flex-shrink-0">
                    <button onClick={() => act(a.id, 'ack')} className="p-1.5 rounded hover:bg-white/5" style={{ color: '#00D4AA' }}>
                      <CheckCircle size={16} />
                    </button>
                    <InfoTip description="Acknowledge — marks this anomaly as 'I'm looking into it'. It stays in the acknowledged list for record-keeping but drops off the default Open view." />
                    <button onClick={() => act(a.id, 'dismiss')} className="p-1.5 rounded hover:bg-white/5" style={{ color: '#6B7A90' }}>
                      <XCircle size={16} />
                    </button>
                    <InfoTip description="Dismiss — marks this as a false positive. Use when the behavior has a legitimate explanation and doesn't need further action. Dismissing does not delete the record." />
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function Stat({ label, value, warn, info }) {
  return (
    <div className="rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
      <div className="flex items-center text-[11px] uppercase tracking-wider mb-2" style={{ color: '#6B7A90' }}>
        {label}
        {info && <InfoTip description={info} />}
      </div>
      <div className="font-mono text-2xl font-bold" style={{ color: warn ? '#FF6B6B' : '#E8ECF1' }}>{value}</div>
    </div>
  );
}

function Select({ value, onChange, options }) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="px-3 py-1.5 rounded border text-xs"
      style={{ background: '#12151C', borderColor: '#272E3B', color: '#E8ECF1' }}
    >
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}
