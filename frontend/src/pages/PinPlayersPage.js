import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import { IdentificationCard, Plus, Key, PencilSimple, Trash, MagnifyingGlass, X } from '@phosphor-icons/react';
import InfoTip from '@/components/InfoTip';

export default function PinPlayersPage() {
  const [players, setPlayers] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [editing, setEditing] = useState(null);
  const [pinChange, setPinChange] = useState(null);
  const [err, setErr] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setErr('');
    try {
      const [pl, sm] = await Promise.allSettled([
        api.get('/players-pin', { params: { q: query || undefined, limit: 200 } }),
        api.get('/players-pin/summary'),
      ]);
      if (pl.status === 'fulfilled') setPlayers(pl.value.data.players || []);
      else setErr('PIN Players API not available — backend may need a rebuild.');
      if (sm.status === 'fulfilled') setSummary(sm.value.data);
    } catch (e) {
      setErr(e.response?.data?.detail || 'Failed to load players');
    } finally {
      setLoading(false);
    }
  }, [query]);

  useEffect(() => { load(); }, [load]);

  return (
    <div data-testid="pin-players-page" className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-2xl font-bold tracking-tight flex items-center gap-3" style={{ color: '#E8ECF1' }}>
          <IdentificationCard size={24} /> PIN Players
          <InfoTip
            size={14}
            label="PIN Players"
            description="Manage player accounts that use numeric PINs (4–8 digits) instead of physical cards. Each player logs in at any EGM by entering their PIN to start a tracked session."
          />
        </h1>
        <div className="flex items-center">
          <button
            onClick={() => setShowCreate(true)}
            data-testid="pin-player-create-btn"
            className="flex items-center gap-2 px-4 py-2 rounded text-sm font-medium transition-colors"
            style={{ background: '#00D4AA', color: '#0A0C10' }}
          >
            <Plus size={16} weight="bold" /> New Player
          </button>
          <InfoTip
            label="Create New Player"
            description="Opens a form to register a new player account. You set their name and a 4–8 digit numeric PIN. The PIN is hashed and stored securely — not even operators can read it back after creation."
          />
        </div>
      </div>

      {summary && (
        <div className="grid grid-cols-4 gap-4">
          <SummaryCard
            label="Active Players"
            value={summary.active_players}
            info="Total count of player accounts currently in 'active' status across the whole system. Inactive/deactivated players are not counted."
          />
          <SummaryCard
            label="Active Credit Sessions"
            value={summary.active_credit_sessions}
            accent
            info="Number of EGMs right now that have credits > $0 on them (a bill or ticket was inserted and the balance has not yet returned to zero). This is the 'money layer' — independent of whether a player is logged in."
          />
          <SummaryCard
            label="Active PIN Sessions"
            value={summary.active_pin_sessions}
            accent
            info="Number of players right now logged in at an EGM via PIN. A player is only counted once (one-PIN-one-EGM enforcement). Does not include anonymous play."
          />
          <SummaryCard
            label="Open Anomalies"
            value={summary.open_anomalies}
            warn={summary.open_anomalies > 0}
            info="Suspicious behavior flags that have not yet been acknowledged or dismissed. Click the Session Anomalies page to review them. A non-zero value here means someone should look."
          />
        </div>
      )}

      <div className="flex items-center gap-2">
        <div className="relative flex-1 max-w-md">
          <MagnifyingGlass size={16} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: '#6B7A90' }} />
          <input
            data-testid="pin-player-search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by name, account, email..."
            className="w-full pl-9 pr-3 py-2 rounded border text-sm"
            style={{ background: '#12151C', borderColor: '#272E3B', color: '#E8ECF1' }}
          />
        </div>
        <InfoTip
          label="Search Players"
          description="Type any part of a player name, account reference, or email. Results update as you type. Leave empty to see all players."
        />
      </div>

      {err && <div className="rounded border p-3 text-xs" style={{ background: '#2D1416', borderColor: '#FF3B30', color: '#FF6B6B' }}>{err}</div>}

      <div className="rounded border overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }}>
        <div className="grid grid-cols-[2fr_1.5fr_1.5fr_1fr_1fr_auto] gap-2 px-4 py-2 text-[11px] uppercase tracking-wider font-medium border-b" style={{ color: '#6B7A90', borderColor: '#272E3B' }}>
          <div className="flex items-center">Name<InfoTip description="Full name of the player as entered when the account was created. This is what appears in session and anomaly reports." /></div>
          <div className="flex items-center">Account Ref<InfoTip description="Optional customer ID from your own loyalty or POS system. Useful for cross-referencing UGG data with external systems." /></div>
          <div className="flex items-center">Email<InfoTip description="Optional contact email. Not used for login (login is by PIN at the EGM). Reserved for future marketing and alert features." /></div>
          <div className="flex items-center">Status<InfoTip description="'active' means the PIN works and the player can log in at EGMs. 'inactive' means the account is disabled — historical data is kept but the PIN is rejected." /></div>
          <div className="flex items-center">Created<InfoTip description="Date the player account was first registered in UGG." /></div>
          <div></div>
        </div>
        {loading ? (
          <div className="px-4 py-8 text-center text-sm" style={{ color: '#6B7A90' }}>Loading...</div>
        ) : players.length === 0 ? (
          <div className="px-4 py-8 text-center text-sm" style={{ color: '#6B7A90' }}>No players yet. Click "New Player" to create one.</div>
        ) : players.map(p => (
          <div key={p.id} className="grid grid-cols-[2fr_1.5fr_1.5fr_1fr_1fr_auto] gap-2 px-4 py-2.5 border-b items-center text-xs" style={{ borderColor: '#272E3B40' }}>
            <div style={{ color: '#E8ECF1' }}>{p.name}</div>
            <div className="font-mono" style={{ color: '#A3AEBE' }}>{p.account_ref || '--'}</div>
            <div className="font-mono truncate" style={{ color: '#A3AEBE' }}>{p.email || '--'}</div>
            <div>
              <span className="px-1.5 py-0.5 rounded text-[10px] font-mono uppercase" style={{
                background: p.status === 'active' ? 'rgba(0,212,170,0.1)' : 'rgba(107,122,144,0.1)',
                color: p.status === 'active' ? '#00D4AA' : '#6B7A90',
              }}>{p.status}</span>
            </div>
            <div className="font-mono" style={{ color: '#6B7A90' }}>{p.created_at ? new Date(p.created_at).toLocaleDateString() : '--'}</div>
            <div className="flex items-center gap-0.5">
              <button onClick={() => setPinChange(p)} className="p-1.5 rounded hover:bg-white/5" style={{ color: '#A3AEBE' }}>
                <Key size={14} />
              </button>
              <InfoTip description="Change this player's PIN. Use when a player forgets their PIN or when you suspect their PIN has been compromised. The old PIN stops working immediately." />
              <button onClick={() => setEditing(p)} className="p-1.5 rounded hover:bg-white/5" style={{ color: '#A3AEBE' }}>
                <PencilSimple size={14} />
              </button>
              <InfoTip description="Edit this player's profile: name, email, phone, notes. PIN is changed separately using the key icon." />
              <button onClick={async () => { if (window.confirm(`Deactivate ${p.name}?`)) { await api.delete(`/players-pin/${p.id}`); load(); } }} className="p-1.5 rounded hover:bg-white/5" style={{ color: '#FF6B6B' }}>
                <Trash size={14} />
              </button>
              <InfoTip description="Deactivate this player. Their PIN will stop working at all EGMs, but all their historical session and anomaly data is preserved. You can reactivate them later by editing the status field." />
            </div>
          </div>
        ))}
      </div>

      {showCreate && <CreateModal onClose={() => setShowCreate(false)} onSaved={() => { setShowCreate(false); load(); }} />}
      {editing && <EditModal player={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); load(); }} />}
      {pinChange && <PinModal player={pinChange} onClose={() => setPinChange(null)} onSaved={() => setPinChange(null)} />}
    </div>
  );
}

function SummaryCard({ label, value, accent, warn, info }) {
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

function Modal({ title, children, onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: 'rgba(0,0,0,0.7)' }} onClick={onClose}>
      <div className="rounded border w-full max-w-md" style={{ background: '#12151C', borderColor: '#272E3B' }} onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: '#272E3B' }}>
          <span className="text-sm font-medium" style={{ color: '#E8ECF1' }}>{title}</span>
          <button onClick={onClose} style={{ color: '#6B7A90' }}><X size={16} /></button>
        </div>
        <div className="p-4 space-y-3">{children}</div>
      </div>
    </div>
  );
}

function Field({ label, info, ...props }) {
  return (
    <div>
      <label className="flex items-center text-[11px] uppercase tracking-wider mb-1" style={{ color: '#6B7A90' }}>
        {label}
        {info && <InfoTip description={info} />}
      </label>
      <input {...props} className="w-full px-3 py-2 rounded border text-sm" style={{ background: '#0A0C10', borderColor: '#272E3B', color: '#E8ECF1' }} />
    </div>
  );
}

function CreateModal({ onClose, onSaved }) {
  const [form, setForm] = useState({ name: '', pin: '', account_ref: '', email: '', phone: '', notes: '' });
  const [err, setErr] = useState('');
  const [saving, setSaving] = useState(false);
  const submit = async () => {
    setErr(''); setSaving(true);
    try {
      const payload = Object.fromEntries(Object.entries(form).filter(([, v]) => v));
      await api.post('/players-pin', payload);
      onSaved();
    } catch (e) {
      setErr(e.response?.data?.detail || 'Create failed');
    } finally {
      setSaving(false);
    }
  };
  return (
    <Modal title="Create PIN Player" onClose={onClose}>
      <Field label="Name *" info="Full name as it should appear in reports. Required." value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
      <Field label="PIN (numeric, 4–8 digits) *" info="Numeric only. Player will type this at the EGM to log in. Pick something memorable but not obvious — avoid 1234, birthdays, or sequential digits. Once saved, nobody (not even admins) can read this PIN back — only reset it." type="password" value={form.pin} onChange={(e) => setForm({ ...form, pin: e.target.value })} />
      <Field label="Account Ref" info="Optional external ID (your POS/loyalty system's customer number). Use for cross-referencing between UGG and your other systems." value={form.account_ref} onChange={(e) => setForm({ ...form, account_ref: e.target.value })} />
      <Field label="Email" info="Optional. Not used for login — only for future marketing/alert features." value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
      <Field label="Phone" info="Optional. Not used for login — only for future SMS reward features." value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
      {err && <div className="text-xs" style={{ color: '#FF6B6B' }}>{err}</div>}
      <button data-testid="pin-player-create-submit" disabled={!form.name || !form.pin || saving} onClick={submit} className="w-full py-2 rounded text-sm font-medium" style={{ background: '#00D4AA', color: '#0A0C10', opacity: (!form.name || !form.pin || saving) ? 0.5 : 1 }}>
        {saving ? 'Saving...' : 'Create'}
      </button>
    </Modal>
  );
}

function EditModal({ player, onClose, onSaved }) {
  const [form, setForm] = useState({ name: player.name || '', email: player.email || '', phone: player.phone || '', notes: player.notes || '' });
  const [err, setErr] = useState('');
  const submit = async () => {
    try {
      await api.patch(`/players-pin/${player.id}`, form);
      onSaved();
    } catch (e) { setErr(e.response?.data?.detail || 'Update failed'); }
  };
  return (
    <Modal title={`Edit: ${player.name}`} onClose={onClose}>
      <Field label="Name" info="Player's full name. Changes appear in all future reports; historical reports still show the old name." value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
      <Field label="Email" info="Optional contact email." value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
      <Field label="Phone" info="Optional contact phone number." value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
      {err && <div className="text-xs" style={{ color: '#FF6B6B' }}>{err}</div>}
      <button onClick={submit} className="w-full py-2 rounded text-sm font-medium" style={{ background: '#00D4AA', color: '#0A0C10' }}>Save</button>
    </Modal>
  );
}

function PinModal({ player, onClose, onSaved }) {
  const [pin, setPin] = useState('');
  const [err, setErr] = useState('');
  const [done, setDone] = useState(false);
  const submit = async () => {
    try {
      await api.post(`/players-pin/${player.id}/pin`, { new_pin: pin });
      setDone(true);
      setTimeout(() => onSaved(), 1000);
    } catch (e) { setErr(e.response?.data?.detail || 'PIN change failed'); }
  };
  return (
    <Modal title={`Change PIN: ${player.name}`} onClose={onClose}>
      <Field label="New PIN (4–8 digits)" info="The new PIN takes effect immediately. The old PIN stops working. Tell the player their new PIN in person — never by email or text message." type="password" value={pin} onChange={(e) => setPin(e.target.value)} />
      {err && <div className="text-xs" style={{ color: '#FF6B6B' }}>{err}</div>}
      {done && <div className="text-xs" style={{ color: '#00D4AA' }}>PIN updated.</div>}
      <button disabled={pin.length < 4 || done} onClick={submit} className="w-full py-2 rounded text-sm font-medium" style={{ background: '#00D4AA', color: '#0A0C10', opacity: (pin.length < 4 || done) ? 0.5 : 1 }}>Update PIN</button>
    </Modal>
  );
}
