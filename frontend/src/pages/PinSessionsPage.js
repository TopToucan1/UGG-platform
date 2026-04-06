import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import { ClockCounterClockwise, CurrencyDollar, IdentificationCard, Desktop, ArrowRight, X } from '@phosphor-icons/react';
import InfoTip from '@/components/InfoTip';

export default function PinSessionsPage() {
  const [tab, setTab] = useState('active');
  const [credit, setCredit] = useState([]);
  const [pin, setPin] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detail, setDetail] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [sm, act, ch, ph] = await Promise.allSettled([
        api.get('/players-pin/summary'),
        api.get('/players-pin/sessions/active'),
        api.get('/players-pin/sessions/credit', { params: { limit: 100 } }),
        api.get('/players-pin/sessions/pin', { params: { limit: 100 } }),
      ]);
      if (sm.status === 'fulfilled') setSummary(sm.value.data);
      if (tab === 'active') {
        if (act.status === 'fulfilled') {
          setCredit(act.value.data.credit_sessions || []);
          setPin(act.value.data.pin_sessions || []);
        }
      } else {
        if (ch.status === 'fulfilled') setCredit(ch.value.data.sessions || []);
        if (ph.status === 'fulfilled') setPin(ph.value.data.sessions || []);
      }
    } finally { setLoading(false); }
  }, [tab]);

  useEffect(() => { load(); const t = setInterval(load, 5000); return () => clearInterval(t); }, [load]);

  const openDetail = async (sessionId) => {
    try {
      const res = await api.get(`/players-pin/sessions/credit/${sessionId}`);
      setDetail(res.data);
    } catch {}
  };

  return (
    <div data-testid="pin-sessions-page" className="space-y-4">
      <h1 className="font-heading text-2xl font-bold tracking-tight flex items-center gap-3" style={{ color: '#E8ECF1' }}>
        <ClockCounterClockwise size={24} /> PIN Sessions
        <InfoTip
          size={14}
          label="PIN Sessions"
          description="Live and historical view of credit sessions (money layer) and PIN sessions (player layer). A credit session starts when money is inserted at zero balance and ends when balance hits zero. A PIN session starts when a player enters their PIN and ends on logout or when the credit session ends."
        />
      </h1>

      {summary && (
        <div className="grid grid-cols-5 gap-4">
          <Stat
            label="Active Credit"
            value={summary.active_credit_sessions}
            accent
            info="EGMs right now with credits > $0 on them (money has been inserted and balance has not yet returned to zero). This is independent of whether anyone is logged in."
          />
          <Stat
            label="Active PIN"
            value={summary.active_pin_sessions}
            accent
            info="Players right now logged in at an EGM via PIN. One-PIN-one-EGM is enforced, so this number also equals the count of unique players currently playing."
          />
          <Stat
            label="Total Credit"
            value={summary.total_credit_sessions}
            info="All-time count of credit sessions ever recorded in the system, including active and closed."
          />
          <Stat
            label="Total PIN"
            value={summary.total_pin_sessions}
            info="All-time count of PIN sessions ever recorded. Typically higher than credit sessions because one credit session can contain multiple PIN logins."
          />
          <Stat
            label="Open Anomalies"
            value={summary.open_anomalies}
            warn={summary.open_anomalies > 0}
            info="Suspicious-behavior flags that haven't been acknowledged or dismissed yet. Review them on the Session Anomalies page."
          />
        </div>
      )}

      <div className="flex gap-2 border-b items-center" style={{ borderColor: '#272E3B' }}>
        {[
          { id: 'active', label: 'Active Now', info: 'Shows only sessions that are currently open (not yet ended). Auto-refreshes every 5 seconds.' },
          { id: 'history', label: 'Recent History', info: 'Shows the most recent 100 credit and 100 PIN sessions, including closed ones. Useful for reviewing what happened earlier today or this week.' },
        ].map(t => (
          <div key={t.id} className="flex items-center">
            <button onClick={() => setTab(t.id)} data-testid={`sessions-tab-${t.id}`}
              className="px-4 py-2.5 text-xs font-medium uppercase tracking-wider transition-colors"
              style={{ color: tab === t.id ? '#00D4AA' : '#6B7A90', borderBottom: tab === t.id ? '2px solid #00D4AA' : '2px solid transparent' }}
            >{t.label}</button>
            <InfoTip description={t.info} />
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <CurrencyDollar size={16} style={{ color: '#00D4AA' }} />
            <span className="text-xs uppercase tracking-wider font-medium" style={{ color: '#A3AEBE' }}>Credit Sessions</span>
            <span className="text-xs font-mono" style={{ color: '#6B7A90' }}>({credit.length})</span>
            <InfoTip description="The MONEY layer. Each card is one EGM's balance session — starts when money goes in at zero, ends when balance returns to zero. Click a card to see full financial detail and which players were logged in during it." />
          </div>
          <div className="rounded border overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }}>
            {loading ? <Loading /> : credit.length === 0 ? <Empty label="No credit sessions" /> : credit.map(c => (
              <button key={c.id} onClick={() => openDetail(c.id)} className="w-full text-left px-4 py-3 border-b hover:bg-white/5 transition-colors" style={{ borderColor: '#272E3B40' }}>
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs" style={{ color: '#E8ECF1' }}>{c.device_id?.slice(0, 12)}</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded font-mono uppercase" style={{
                    background: c.is_active ? 'rgba(0,212,170,0.1)' : 'rgba(107,122,144,0.1)',
                    color: c.is_active ? '#00D4AA' : '#6B7A90',
                  }}>{c.is_active ? 'ACTIVE' : c.end_reason || 'closed'}</span>
                </div>
                <div className="flex items-center justify-between mt-1 text-[11px]" style={{ color: '#6B7A90' }}>
                  <span>{c.start_trigger} ${c.start_amount?.toFixed(2)} → {c.total_out?.toFixed(2) || '0.00'} out</span>
                  <span>{c.games_played || 0} games</span>
                </div>
                <div className="text-[10px] font-mono mt-1" style={{ color: '#6B7A90' }}>{fmt(c.started_at)}</div>
              </button>
            ))}
          </div>
        </div>

        <div>
          <div className="flex items-center gap-2 mb-2">
            <IdentificationCard size={16} style={{ color: '#00D4AA' }} />
            <span className="text-xs uppercase tracking-wider font-medium" style={{ color: '#A3AEBE' }}>PIN Sessions</span>
            <span className="text-xs font-mono" style={{ color: '#6B7A90' }}>({pin.length})</span>
            <InfoTip description="The PLAYER layer. Each card is one player's login session at an EGM — starts when they enter their PIN, ends when they log out or when the credit session on that EGM ends. A single credit session can contain multiple PIN sessions if players swap." />
          </div>
          <div className="rounded border overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }}>
            {loading ? <Loading /> : pin.length === 0 ? <Empty label="No PIN sessions" /> : pin.map(p => (
              <div key={p.id} className="px-4 py-3 border-b" style={{ borderColor: '#272E3B40' }}>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium" style={{ color: '#E8ECF1' }}>{p.player_name || p.player_id?.slice(0, 8)}</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded font-mono uppercase" style={{
                    background: p.is_active ? 'rgba(0,212,170,0.1)' : 'rgba(107,122,144,0.1)',
                    color: p.is_active ? '#00D4AA' : '#6B7A90',
                  }}>{p.is_active ? 'ACTIVE' : p.end_reason || 'closed'}</span>
                </div>
                <div className="flex items-center gap-2 mt-1 text-[11px] font-mono" style={{ color: '#6B7A90' }}>
                  <Desktop size={11} />
                  <span>{p.device_id?.slice(0, 12)}</span>
                  {p.credit_session_id && <><ArrowRight size={10} /><CurrencyDollar size={11} /></>}
                </div>
                <div className="flex items-center justify-between mt-1 text-[11px]" style={{ color: '#6B7A90' }}>
                  <span>{p.games_played || 0} games / net ${p.net?.toFixed(2) || '0.00'}</span>
                  <span className="text-[10px] font-mono">{fmt(p.started_at)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {detail && <DetailPanel session={detail} onClose={() => setDetail(null)} />}
    </div>
  );
}

function Stat({ label, value, accent, warn, info }) {
  const color = warn ? '#FF6B6B' : accent ? '#00D4AA' : '#E8ECF1';
  return (
    <div className="rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
      <div className="flex items-center text-[11px] uppercase tracking-wider mb-2" style={{ color: '#6B7A90' }}>
        {label}
        {info && <InfoTip description={info} />}
      </div>
      <div className="font-mono text-2xl font-bold" style={{ color }}>{value ?? '--'}</div>
    </div>
  );
}

function Loading() { return <div className="px-4 py-6 text-center text-xs" style={{ color: '#6B7A90' }}>Loading...</div>; }
function Empty({ label }) { return <div className="px-4 py-6 text-center text-xs" style={{ color: '#6B7A90' }}>{label}</div>; }

function fmt(iso) {
  if (!iso) return '--';
  try { return new Date(iso).toLocaleTimeString(); } catch { return iso; }
}

function DetailPanel({ session, onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: 'rgba(0,0,0,0.7)' }} onClick={onClose}>
      <div className="rounded border w-full max-w-2xl max-h-[80vh] overflow-y-auto" style={{ background: '#12151C', borderColor: '#272E3B' }} onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-4 py-3 border-b sticky top-0" style={{ background: '#12151C', borderColor: '#272E3B' }}>
          <span className="text-sm font-medium" style={{ color: '#E8ECF1' }}>Credit Session Detail</span>
          <button onClick={onClose} style={{ color: '#6B7A90' }}><X size={16} /></button>
        </div>
        <div className="p-4 space-y-3">
          <div className="grid grid-cols-2 gap-3 text-xs">
            <Kv k="Session ID" v={session.id} mono info="Unique identifier for this credit session. Use for cross-referencing with audit logs or support tickets." />
            <Kv k="Device" v={session.device_id} mono info="The EGM where this credit session took place." />
            <Kv k="Trigger" v={`${session.start_trigger} $${session.start_amount?.toFixed(2)}`} info="How the session started: 'bill_in' = cash bill inserted; 'ticket_in' = TITO voucher redeemed. The dollar amount is the opening deposit that brought the balance off zero." />
            <Kv k="Status" v={session.is_active ? 'ACTIVE' : session.end_reason} info="ACTIVE = balance still > 0. Otherwise shows how the session ended: played_down (played to zero), cashout_ticket (TITO printed), cashout_cash, handpay (attendant paid jackpot), or transfer_out." />
            <Kv k="Started" v={fmt(session.started_at)} info="Timestamp when balance first went above zero on this EGM." />
            <Kv k="Ended" v={fmt(session.ended_at)} info="Timestamp when balance returned to zero and the session closed. Blank if still active." />
            <Kv k="Total In" v={`$${session.total_in?.toFixed(2) || '0.00'}`} info="Sum of every bill and ticket inserted during this session. Represents the total money the player put at risk." />
            <Kv k="Total Out" v={`$${session.total_out?.toFixed(2) || '0.00'}`} info="Sum of cashouts and TITO tickets printed during this session. Represents money the player took away." />
            <Kv k="Coin In" v={`$${session.coin_in?.toFixed(2) || '0.00'}`} info="Total wagered ('handle') during the session — the sum of every bet. Different from Total In: a player can wager the same $20 many times if they win and play it back." />
            <Kv k="Coin Out" v={`$${session.coin_out?.toFixed(2) || '0.00'}`} info="Total won during the session — the sum of every winning payout. Different from Total Out: winnings add to credit meter; cashouts remove from it." />
            <Kv k="Games" v={session.games_played || 0} info="Number of complete game rounds played during this session. A very low number with high Total In is a red flag — see Anomalies (LOW_PLAY_FLIP)." />
            <Kv k="Net" v={`$${session.net?.toFixed(2) || '0.00'}`} accent={session.net > 0} info="Coin Out minus Coin In. Positive means the player was up on wagers at session end (not necessarily what they walked away with — that's Total Out minus Total In)." />
          </div>

          <div>
            <div className="flex items-center text-[11px] uppercase tracking-wider mb-2" style={{ color: '#6B7A90' }}>
              PIN Sessions During This Credit Session
              <InfoTip description="Lists every player login that happened while this credit session was active. Zero entries means the session was played anonymously. Multiple entries means the balance was shared between different PINs (e.g., player A logged out with credits remaining, player B logged in and finished them)." />
            </div>
            {(session.pin_sessions || []).length === 0 ? (
              <div className="text-xs" style={{ color: '#6B7A90' }}>Anonymous — no PIN sessions</div>
            ) : (
              <div className="space-y-2">
                {session.pin_sessions.map(ps => (
                  <div key={ps.id} className="rounded border p-2 text-xs" style={{ background: '#0A0C10', borderColor: '#272E3B' }}>
                    <div className="flex items-center justify-between">
                      <span style={{ color: '#E8ECF1' }}>{ps.player_name}</span>
                      <span className="text-[10px] font-mono" style={{ color: '#6B7A90' }}>{ps.end_reason || 'active'}</span>
                    </div>
                    <div className="text-[11px] font-mono mt-1" style={{ color: '#6B7A90' }}>
                      {fmt(ps.started_at)} → {fmt(ps.ended_at)} | {ps.games_played || 0} games | net ${ps.net?.toFixed(2) || '0.00'}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Kv({ k, v, mono, accent, info }) {
  return (
    <div>
      <div className="flex items-center text-[10px] uppercase tracking-wider" style={{ color: '#6B7A90' }}>
        {k}
        {info && <InfoTip description={info} />}
      </div>
      <div className={mono ? 'font-mono' : ''} style={{ color: accent ? '#00D4AA' : '#E8ECF1' }}>{v ?? '--'}</div>
    </div>
  );
}
