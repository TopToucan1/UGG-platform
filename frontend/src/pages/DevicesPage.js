import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import { useSearchParams } from 'react-router-dom';
import { MagnifyingGlass, Funnel, CaretRight, X, Lightning, Terminal, Plugs, ListMagnifyingGlass, CircleWavyCheck } from '@phosphor-icons/react';

function StatusBadge({ status }) {
  const c = { online: '#00D4AA', offline: '#FF3B30', error: '#FF3B30', maintenance: '#F5A623' };
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`w-2 h-2 rounded-full ${status === 'online' ? 'pulse-online' : ''}`} style={{ background: c[status] || '#6B7A90' }} />
      <span className="text-xs font-mono capitalize" style={{ color: c[status] || '#6B7A90' }}>{status}</span>
    </span>
  );
}

function CapBadge({ label, supported }) {
  return (
    <span className="text-[10px] font-mono px-2 py-0.5 rounded" style={{
      background: supported ? 'rgba(0,212,170,0.1)' : 'rgba(107,122,144,0.1)',
      color: supported ? '#00D4AA' : '#6B7A90'
    }}>
      {label}
    </span>
  );
}

export default function DevicesPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [devices, setDevices] = useState([]);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [protocolFilter, setProtocolFilter] = useState('');
  const [mfrFilter, setMfrFilter] = useState('');
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [deviceEvents, setDeviceEvents] = useState([]);
  const [deviceCommands, setDeviceCommands] = useState([]);
  const [deviceMeters, setDeviceMeters] = useState([]);

  const fetchDevices = useCallback(async () => {
    const params = new URLSearchParams();
    if (search) params.set('search', search);
    if (statusFilter) params.set('status', statusFilter);
    if (protocolFilter) params.set('protocol', protocolFilter);
    if (mfrFilter) params.set('manufacturer', mfrFilter);
    params.set('limit', '100');
    const { data } = await api.get(`/devices?${params.toString()}`);
    setDevices(data.devices || []);
    setTotal(data.total || 0);
  }, [search, statusFilter, protocolFilter, mfrFilter]);

  useEffect(() => {
    fetchDevices();
    api.get('/devices/filters').then(r => setFilters(r.data)).catch(() => {});
  }, [fetchDevices]);

  useEffect(() => {
    const selId = searchParams.get('selected');
    if (selId && devices.length) {
      const d = devices.find(x => x.id === selId);
      if (d) selectDevice(d);
    }
  }, [searchParams, devices]);

  const selectDevice = async (d) => {
    setSelected(d);
    setActiveTab('overview');
    try {
      const [detRes, evtRes, cmdRes, mtrRes] = await Promise.all([
        api.get(`/devices/${d.id}`),
        api.get(`/devices/${d.id}/events?limit=20`),
        api.get(`/devices/${d.id}/commands?limit=20`),
        api.get(`/devices/${d.id}/meters?limit=5`),
      ]);
      setDetail(detRes.data);
      setDeviceEvents(evtRes.data.events || []);
      setDeviceCommands(cmdRes.data.commands || []);
      setDeviceMeters(mtrRes.data.meters || []);
    } catch (err) {
      console.error(err);
    }
  };

  const sendCommand = async (cmdType) => {
    if (!selected) return;
    try {
      await api.post(`/devices/${selected.id}/command`, { command_type: cmdType });
      const { data } = await api.get(`/devices/${selected.id}/commands?limit=20`);
      setDeviceCommands(data.commands || []);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div data-testid="device-management" className="flex gap-0 h-full -m-6">
      {/* Filter Rail */}
      <div className="w-60 border-r p-4 space-y-4 flex-shrink-0 overflow-y-auto" style={{ background: '#12151C', borderColor: '#272E3B' }}>
        <h2 className="font-heading text-base font-semibold flex items-center gap-2" style={{ color: '#E8ECF1' }}>
          <Funnel size={16} /> Filters
        </h2>
        <div>
          <label className="block text-[11px] uppercase tracking-wider mb-1.5 font-medium" style={{ color: '#6B7A90' }}>Search</label>
          <div className="relative">
            <MagnifyingGlass size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2" style={{ color: '#6B7A90' }} />
            <input
              data-testid="device-search"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Device ID, manufacturer..."
              className="w-full pl-8 pr-3 py-2 rounded text-xs outline-none"
              style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}
            />
          </div>
        </div>
        <div>
          <label className="block text-[11px] uppercase tracking-wider mb-1.5 font-medium" style={{ color: '#6B7A90' }}>Status</label>
          <select data-testid="device-status-filter" value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-full px-3 py-2 rounded text-xs outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}>
            <option value="">All</option>
            {filters?.statuses?.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-[11px] uppercase tracking-wider mb-1.5 font-medium" style={{ color: '#6B7A90' }}>Protocol</label>
          <select data-testid="device-protocol-filter" value={protocolFilter} onChange={e => setProtocolFilter(e.target.value)} className="w-full px-3 py-2 rounded text-xs outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}>
            <option value="">All</option>
            {filters?.protocols?.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-[11px] uppercase tracking-wider mb-1.5 font-medium" style={{ color: '#6B7A90' }}>Manufacturer</label>
          <select data-testid="device-mfr-filter" value={mfrFilter} onChange={e => setMfrFilter(e.target.value)} className="w-full px-3 py-2 rounded text-xs outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}>
            <option value="">All</option>
            {filters?.manufacturers?.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
        </div>
        <div className="pt-2 border-t" style={{ borderColor: '#272E3B' }}>
          <span className="text-xs font-mono" style={{ color: '#6B7A90' }}>{total} devices</span>
        </div>
      </div>

      {/* Device List */}
      <div className={`flex-1 overflow-y-auto ${selected ? '' : ''}`} style={{ background: '#0A0C10' }}>
        <div className="sticky top-0 z-10 border-b" style={{ background: '#12151C', borderColor: '#272E3B' }}>
          <div className="grid grid-cols-12 gap-2 px-4 py-2 text-[11px] uppercase tracking-wider font-medium" style={{ color: '#6B7A90' }}>
            <div className="col-span-1">Status</div>
            <div className="col-span-2">Device Ref</div>
            <div className="col-span-2">Manufacturer</div>
            <div className="col-span-2">Model</div>
            <div className="col-span-1">Protocol</div>
            <div className="col-span-2">Last Seen</div>
            <div className="col-span-2">Actions</div>
          </div>
        </div>
        {devices.map(d => (
          <button
            key={d.id}
            data-testid={`device-row-${d.external_ref}`}
            onClick={() => { selectDevice(d); setSearchParams({ selected: d.id }); }}
            className="w-full grid grid-cols-12 gap-2 px-4 py-2.5 border-b text-left transition-colors text-sm group"
            style={{ borderColor: '#272E3B20', background: selected?.id === d.id ? 'rgba(0,212,170,0.05)' : 'transparent' }}
          >
            <div className="col-span-1"><StatusBadge status={d.status} /></div>
            <div className="col-span-2 font-mono font-medium" style={{ color: '#E8ECF1' }}>{d.external_ref}</div>
            <div className="col-span-2" style={{ color: '#A3AEBE' }}>{d.manufacturer}</div>
            <div className="col-span-2" style={{ color: '#A3AEBE' }}>{d.model}</div>
            <div className="col-span-1 font-mono text-xs uppercase" style={{ color: '#6B7A90' }}>{d.protocol_family}</div>
            <div className="col-span-2 font-mono text-xs" style={{ color: '#6B7A90' }}>
              {d.last_seen_at ? new Date(d.last_seen_at).toLocaleString() : '--'}
            </div>
            <div className="col-span-2 flex items-center opacity-0 group-hover:opacity-100 transition-opacity">
              <CaretRight size={14} style={{ color: '#00D4AA' }} />
            </div>
          </button>
        ))}
      </div>

      {/* Detail Drawer */}
      {selected && (
        <div className="w-[480px] border-l overflow-y-auto flex-shrink-0" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="device-detail-drawer">
          <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: '#272E3B' }}>
            <div>
              <h3 className="font-heading text-lg font-semibold" style={{ color: '#E8ECF1' }}>{selected.external_ref}</h3>
              <span className="text-xs" style={{ color: '#6B7A90' }}>{selected.manufacturer} {selected.model}</span>
            </div>
            <button data-testid="close-drawer-btn" onClick={() => { setSelected(null); setSearchParams({}); }} style={{ color: '#6B7A90' }}>
              <X size={18} />
            </button>
          </div>

          {/* Tabs */}
          <div className="flex border-b" style={{ borderColor: '#272E3B' }}>
            {['overview', 'events', 'commands', 'connector', 'audit'].map(tab => (
              <button
                key={tab}
                data-testid={`device-tab-${tab}`}
                onClick={() => setActiveTab(tab)}
                className="px-4 py-2.5 text-xs font-medium uppercase tracking-wider transition-colors"
                style={{
                  color: activeTab === tab ? '#00D4AA' : '#6B7A90',
                  borderBottom: activeTab === tab ? '2px solid #00D4AA' : '2px solid transparent',
                }}
              >
                {tab}
              </button>
            ))}
          </div>

          <div className="p-4">
            {activeTab === 'overview' && detail && (
              <div className="space-y-4" data-testid="device-overview-tab">
                <div className="flex items-center gap-3">
                  <StatusBadge status={detail.status} />
                  <span className="text-xs font-mono" style={{ color: '#6B7A90' }}>
                    {detail.protocol_family} {detail.protocol_version}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded p-3 border" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
                    <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: '#6B7A90' }}>Serial</div>
                    <div className="font-mono text-xs" style={{ color: '#E8ECF1' }}>{detail.serial_number}</div>
                  </div>
                  <div className="rounded p-3 border" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
                    <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: '#6B7A90' }}>Firmware</div>
                    <div className="font-mono text-xs" style={{ color: '#E8ECF1' }}>{detail.firmware_version}</div>
                  </div>
                  <div className="rounded p-3 border" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
                    <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: '#6B7A90' }}>Game</div>
                    <div className="text-xs" style={{ color: '#E8ECF1' }}>{detail.metadata?.game_title}</div>
                  </div>
                  <div className="rounded p-3 border" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
                    <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: '#6B7A90' }}>Denom</div>
                    <div className="font-mono text-xs" style={{ color: '#E8ECF1' }}>${detail.metadata?.denomination}</div>
                  </div>
                </div>
                {detail.capabilities && (
                  <div>
                    <div className="text-[10px] uppercase tracking-wider mb-2" style={{ color: '#6B7A90' }}>Capabilities</div>
                    <div className="flex flex-wrap gap-1.5">
                      <CapBadge label="Messaging" supported={detail.capabilities.supports_messaging} />
                      <CapBadge label="Remote Disable" supported={detail.capabilities.supports_remote_disable} />
                      <CapBadge label="Meters" supported={detail.capabilities.supports_meter_readback} />
                      <CapBadge label="Player Track" supported={detail.capabilities.supports_player_tracking} />
                      <CapBadge label="Voucher" supported={detail.capabilities.supports_voucher} />
                      <CapBadge label="Progressive" supported={detail.capabilities.supports_progressive} />
                      <CapBadge label="Bonus" supported={detail.capabilities.supports_bonus} />
                      <CapBadge label="Health" supported={detail.capabilities.supports_health_telemetry} />
                    </div>
                  </div>
                )}
                {deviceMeters.length > 0 && (
                  <div>
                    <div className="text-[10px] uppercase tracking-wider mb-2" style={{ color: '#6B7A90' }}>Latest Meters</div>
                    <div className="rounded border p-3 font-mono text-xs space-y-1" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
                      <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Coin In</span><span style={{ color: '#E8ECF1' }}>{deviceMeters[0].coin_in?.toLocaleString()}</span></div>
                      <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Coin Out</span><span style={{ color: '#E8ECF1' }}>{deviceMeters[0].coin_out?.toLocaleString()}</span></div>
                      <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Games</span><span style={{ color: '#E8ECF1' }}>{deviceMeters[0].games_played?.toLocaleString()}</span></div>
                    </div>
                  </div>
                )}
                <div className="flex gap-2">
                  <button data-testid="cmd-disable-btn" onClick={() => sendCommand('device.disable')} className="px-3 py-1.5 rounded text-xs font-medium" style={{ background: 'rgba(255,59,48,0.1)', color: '#FF3B30', border: '1px solid rgba(255,59,48,0.2)' }}>Disable</button>
                  <button data-testid="cmd-enable-btn" onClick={() => sendCommand('device.enable')} className="px-3 py-1.5 rounded text-xs font-medium" style={{ background: 'rgba(0,212,170,0.1)', color: '#00D4AA', border: '1px solid rgba(0,212,170,0.2)' }}>Enable</button>
                  <button data-testid="cmd-message-btn" onClick={() => sendCommand('device.send_message')} className="px-3 py-1.5 rounded text-xs font-medium" style={{ background: 'rgba(0,122,255,0.1)', color: '#007AFF', border: '1px solid rgba(0,122,255,0.2)' }}>Send Message</button>
                </div>
              </div>
            )}

            {activeTab === 'events' && (
              <div className="space-y-1" data-testid="device-events-tab">
                {deviceEvents.map(evt => (
                  <div key={evt.id} className="px-3 py-2 rounded border text-xs" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-medium" style={{ color: '#E8ECF1' }}>{evt.event_type}</span>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded" style={{ background: evt.severity === 'critical' ? 'rgba(255,59,48,0.1)' : evt.severity === 'warning' ? 'rgba(245,166,35,0.1)' : 'rgba(0,122,255,0.1)', color: evt.severity === 'critical' ? '#FF3B30' : evt.severity === 'warning' ? '#F5A623' : '#007AFF' }}>{evt.severity}</span>
                    </div>
                    <div className="font-mono mt-1" style={{ color: '#6B7A90' }}>{new Date(evt.occurred_at).toLocaleString()}</div>
                  </div>
                ))}
                {deviceEvents.length === 0 && <div className="text-xs text-center py-8" style={{ color: '#6B7A90' }}>No events found</div>}
              </div>
            )}

            {activeTab === 'commands' && (
              <div className="space-y-1" data-testid="device-commands-tab">
                {deviceCommands.map(cmd => (
                  <div key={cmd.id} className="px-3 py-2 rounded border text-xs" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-medium" style={{ color: '#E8ECF1' }}>{cmd.command_type}</span>
                      <span className="font-mono capitalize" style={{ color: cmd.status === 'completed' ? '#00D4AA' : cmd.status === 'failed' ? '#FF3B30' : '#F5A623' }}>{cmd.status}</span>
                    </div>
                    <div className="font-mono mt-1" style={{ color: '#6B7A90' }}>{new Date(cmd.issued_at).toLocaleString()}</div>
                  </div>
                ))}
                {deviceCommands.length === 0 && <div className="text-xs text-center py-8" style={{ color: '#6B7A90' }}>No commands found</div>}
              </div>
            )}

            {activeTab === 'connector' && detail && (
              <div className="space-y-3" data-testid="device-connector-tab">
                <div className="rounded border p-3" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
                  <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: '#6B7A90' }}>Connector ID</div>
                  <div className="font-mono text-xs" style={{ color: '#E8ECF1' }}>{detail.connector_id}</div>
                </div>
                <div className="rounded border p-3" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
                  <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: '#6B7A90' }}>Protocol</div>
                  <div className="font-mono text-xs" style={{ color: '#E8ECF1' }}>{detail.protocol_family} {detail.protocol_version}</div>
                </div>
              </div>
            )}

            {activeTab === 'audit' && (
              <div className="text-xs text-center py-8" style={{ color: '#6B7A90' }} data-testid="device-audit-tab">
                <ListMagnifyingGlass size={32} className="mx-auto mb-2" />
                Audit trail for this device
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
