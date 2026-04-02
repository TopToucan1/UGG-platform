import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Plugs, Plus, CheckCircle, Clock, ArrowsLeftRight } from '@phosphor-icons/react';

export default function ConnectorBuilderPage() {
  const [connectors, setConnectors] = useState([]);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newType, setNewType] = useState('rest_poll');

  useEffect(() => {
    api.get('/connectors').then(r => setConnectors(r.data.connectors || [])).catch(() => {});
  }, []);

  const selectConnector = async (c) => {
    setSelected(c);
    try {
      const { data } = await api.get(`/connectors/${c.id}`);
      setDetail(data);
    } catch (err) { console.error(err); }
  };

  const createConnector = async () => {
    try {
      const { data } = await api.post('/connectors', { name: newName, type: newType });
      setConnectors([data, ...connectors]);
      setShowCreate(false);
      setNewName('');
    } catch (err) { console.error(err); }
  };

  const approveManifest = async (connId, manId) => {
    try {
      await api.post(`/connectors/${connId}/manifests/${manId}/approve`);
      selectConnector(selected);
    } catch (err) { console.error(err); }
  };

  // Canonical event fields for the mapping canvas
  const canonicalFields = [
    'event_id', 'tenant_id', 'site_id', 'device_id', 'event_type',
    'occurred_at', 'payload', 'severity', 'source_protocol', 'integrity_hash',
    'correlation_id', 'session_id', 'schema_version'
  ];

  return (
    <div data-testid="connector-builder" className="flex gap-0 h-full -m-6">
      {/* Left - Evidence Explorer / Connector List */}
      <div className="w-72 border-r flex flex-col flex-shrink-0 overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }}>
        <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: '#272E3B' }}>
          <h2 className="font-heading text-base font-semibold" style={{ color: '#E8ECF1' }}>Connectors</h2>
          <button data-testid="create-connector-btn" onClick={() => setShowCreate(true)} className="p-1 rounded" style={{ color: '#00D4AA' }}>
            <Plus size={18} />
          </button>
        </div>

        {showCreate && (
          <div className="p-3 border-b space-y-2" style={{ borderColor: '#272E3B' }}>
            <input value={newName} onChange={e => setNewName(e.target.value)} placeholder="Connector name" className="w-full px-3 py-2 rounded text-xs outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }} />
            <select value={newType} onChange={e => setNewType(e.target.value)} className="w-full px-3 py-2 rounded text-xs outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}>
              <option value="rest_poll">REST Poll</option>
              <option value="rest_webhook">REST Webhook</option>
              <option value="db_poll">DB Poll</option>
              <option value="log_tail">Log Tail</option>
              <option value="file_drop">File Drop</option>
              <option value="sdk_stream">SDK Stream</option>
              <option value="message_bus">Message Bus</option>
            </select>
            <div className="flex gap-2">
              <button onClick={createConnector} className="flex-1 px-3 py-1.5 rounded text-xs font-medium" style={{ background: '#00D4AA', color: '#0A0C10' }}>Create</button>
              <button onClick={() => setShowCreate(false)} className="px-3 py-1.5 rounded text-xs" style={{ color: '#6B7A90' }}>Cancel</button>
            </div>
          </div>
        )}

        <div className="flex-1 overflow-y-auto">
          {connectors.map(c => (
            <button
              key={c.id}
              data-testid={`connector-item-${c.name.replace(/\s+/g, '-').toLowerCase()}`}
              onClick={() => selectConnector(c)}
              className="w-full text-left px-4 py-3 border-b transition-colors"
              style={{ borderColor: '#272E3B20', background: selected?.id === c.id ? 'rgba(0,212,170,0.05)' : 'transparent' }}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium" style={{ color: '#E8ECF1' }}>{c.name}</span>
                <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${c.status === 'active' ? '' : ''}`} style={{ background: c.status === 'active' ? 'rgba(0,212,170,0.1)' : 'rgba(245,166,35,0.1)', color: c.status === 'active' ? '#00D4AA' : '#F5A623' }}>{c.status}</span>
              </div>
              <div className="text-xs mt-1 font-mono" style={{ color: '#6B7A90' }}>{c.type} v{c.version}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Center - Mapping Canvas */}
      <div className="flex-1 flex flex-col overflow-hidden dot-grid-bg" style={{ background: '#0A0C10' }}>
        <div className="px-4 py-3 border-b" style={{ borderColor: '#272E3B', background: '#12151C' }}>
          <h2 className="font-heading text-base font-semibold" style={{ color: '#E8ECF1' }}>
            {selected ? `Mapping Canvas - ${selected.name}` : 'Select a connector'}
          </h2>
        </div>
        {selected ? (
          <div className="flex-1 p-6 flex items-start justify-center gap-12 overflow-auto">
            {/* Source fields */}
            <div className="w-64">
              <div className="text-[11px] uppercase tracking-wider mb-3 font-medium" style={{ color: '#6B7A90' }}>Source Fields</div>
              <div className="space-y-1.5">
                {['device_id', 'event_code', 'timestamp', 'meter_value', 'error_code', 'player_id', 'game_id', 'denomination', 'bet_amount', 'win_amount', 'door_status', 'voucher_barcode'].map(f => (
                  <div key={f} className="px-3 py-2 rounded border text-xs font-mono cursor-grab" style={{ background: '#12151C', borderColor: '#272E3B', color: '#E8ECF1' }}>
                    {f}
                  </div>
                ))}
              </div>
            </div>

            {/* Mapping arrows */}
            <div className="flex flex-col items-center justify-center pt-8">
              <ArrowsLeftRight size={24} style={{ color: '#00D4AA' }} />
              <div className="text-[10px] mt-2 uppercase tracking-wider" style={{ color: '#6B7A90' }}>Field Mapping</div>
            </div>

            {/* Canonical fields */}
            <div className="w-64">
              <div className="text-[11px] uppercase tracking-wider mb-3 font-medium" style={{ color: '#6B7A90' }}>Canonical Fields</div>
              <div className="space-y-1.5">
                {canonicalFields.map(f => (
                  <div key={f} className="px-3 py-2 rounded border text-xs font-mono" style={{ background: '#12151C', borderColor: '#00D4AA30', color: '#00D4AA' }}>
                    {f}
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <Plugs size={48} className="mx-auto mb-3" style={{ color: '#272E3B' }} />
              <div className="text-sm" style={{ color: '#6B7A90' }}>Select a connector to view its mapping canvas</div>
            </div>
          </div>
        )}
      </div>

      {/* Right - Preview & Validation */}
      <div className="w-80 border-l flex flex-col flex-shrink-0 overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }}>
        <div className="px-4 py-3 border-b" style={{ borderColor: '#272E3B' }}>
          <h2 className="font-heading text-base font-semibold" style={{ color: '#E8ECF1' }}>Preview & Validation</h2>
        </div>
        {detail ? (
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            <div>
              <div className="text-[11px] uppercase tracking-wider mb-2 font-medium" style={{ color: '#6B7A90' }}>Connector Info</div>
              <div className="rounded border p-3 text-xs space-y-2" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Type</span><span className="font-mono" style={{ color: '#E8ECF1' }}>{detail.type}</span></div>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Version</span><span className="font-mono" style={{ color: '#E8ECF1' }}>{detail.version}</span></div>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Devices</span><span className="font-mono" style={{ color: '#E8ECF1' }}>{detail.device_count}</span></div>
              </div>
            </div>
            <div>
              <div className="text-[11px] uppercase tracking-wider mb-2 font-medium" style={{ color: '#6B7A90' }}>Manifests</div>
              {detail.manifests?.map(m => (
                <div key={m.id} className="rounded border p-3 mb-2 text-xs" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium" style={{ color: '#E8ECF1' }}>{m.name}</span>
                    <span className="font-mono" style={{ color: m.status === 'approved' ? '#00D4AA' : '#F5A623' }}>{m.status}</span>
                  </div>
                  <div className="font-mono" style={{ color: '#6B7A90' }}>v{m.version} | {m.field_mappings} fields | {m.command_bindings} commands</div>
                  {m.status === 'draft' && (
                    <button
                      data-testid={`approve-manifest-${m.id}`}
                      onClick={() => approveManifest(detail.id, m.id)}
                      className="mt-2 px-3 py-1 rounded text-xs font-medium flex items-center gap-1"
                      style={{ background: 'rgba(0,212,170,0.1)', color: '#00D4AA' }}
                    >
                      <CheckCircle size={14} /> Approve
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center p-4">
            <div className="text-center text-xs" style={{ color: '#6B7A90' }}>
              <Clock size={32} className="mx-auto mb-2" />
              Select a connector to see validation results
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
