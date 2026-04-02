import { useState, useEffect, useCallback, useRef } from 'react';
import api from '@/lib/api';
import { Plugs, Plus, CheckCircle, Clock, ArrowRight, Trash, FloppyDisk, RocketLaunch, ArrowsClockwise, Check, X, CaretRight, Warning } from '@phosphor-icons/react';

const SOURCE_FIELDS = ['device_id', 'event_code', 'timestamp', 'meter_value', 'error_code', 'player_id', 'game_id', 'denomination', 'bet_amount', 'win_amount', 'door_status', 'voucher_barcode'];
const CANONICAL_FIELDS = ['event_id', 'tenant_id', 'site_id', 'device_id', 'event_type', 'occurred_at', 'payload', 'severity', 'source_protocol', 'integrity_hash', 'correlation_id', 'session_id', 'schema_version'];

function MappingLine({ sourceIdx, targetIdx, containerRef }) {
  const [coords, setCoords] = useState(null);
  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current.getBoundingClientRect();
    const srcEl = containerRef.current.querySelector(`[data-source-idx="${sourceIdx}"]`);
    const tgtEl = containerRef.current.querySelector(`[data-target-idx="${targetIdx}"]`);
    if (srcEl && tgtEl) {
      const sr = srcEl.getBoundingClientRect();
      const tr = tgtEl.getBoundingClientRect();
      setCoords({
        x1: sr.right - container.left, y1: sr.top + sr.height / 2 - container.top,
        x2: tr.left - container.left, y2: tr.top + tr.height / 2 - container.top,
      });
    }
  }, [sourceIdx, targetIdx, containerRef]);
  if (!coords) return null;
  return (
    <line x1={coords.x1} y1={coords.y1} x2={coords.x2} y2={coords.y2} stroke="#00D4AA" strokeWidth="2" strokeDasharray="4,4" opacity="0.6" />
  );
}

export default function ConnectorBuilderPage() {
  const [connectors, setConnectors] = useState([]);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newType, setNewType] = useState('rest_poll');
  const [mappings, setMappings] = useState([]);
  const [dragSource, setDragSource] = useState(null);
  const [saving, setSaving] = useState(false);
  const [activePanel, setActivePanel] = useState('mapping');
  const [deployments, setDeployments] = useState([]);
  const [showDeploy, setShowDeploy] = useState(false);
  const [deployStrategy, setDeployStrategy] = useState('canary');
  const [canaryPercent, setCanaryPercent] = useState(5);
  const canvasRef = useRef(null);

  useEffect(() => {
    api.get('/connectors').then(r => setConnectors(r.data.connectors || [])).catch(() => {});
  }, []);

  const selectConnector = useCallback(async (c) => {
    setSelected(c);
    setActivePanel('mapping');
    try {
      const [detRes, depRes] = await Promise.all([
        api.get(`/connectors/${c.id}`),
        api.get(`/connectors/${c.id}/deployments`),
      ]);
      setDetail(detRes.data);
      setMappings(detRes.data.mappings || []);
      setDeployments(depRes.data.deployments || []);
    } catch (err) { console.error(err); }
  }, []);

  const createConnector = async () => {
    try {
      const { data } = await api.post('/connectors', { name: newName, type: newType });
      setConnectors([data, ...connectors]);
      setShowCreate(false);
      setNewName('');
    } catch (err) { console.error(err); }
  };

  const approveManifest = async (connId, manId) => {
    await api.post(`/connectors/${connId}/manifests/${manId}/approve`);
    selectConnector(selected);
  };

  // --- Drag & Drop ---
  const handleDragStart = (field) => setDragSource(field);

  const handleDropOnTarget = (targetField) => {
    if (!dragSource) return;
    const exists = mappings.find(m => m.source_field === dragSource && m.canonical_field === targetField);
    if (!exists) {
      setMappings(prev => [...prev, {
        id: `map-${Date.now()}`,
        source_field: dragSource,
        canonical_field: targetField,
        connector_id: selected?.id,
      }]);
    }
    setDragSource(null);
  };

  const removeMapping = (id) => setMappings(prev => prev.filter(m => m.id !== id));

  const saveMappings = async () => {
    if (!selected) return;
    setSaving(true);
    try {
      await api.post(`/connectors/${selected.id}/mappings`, { mappings });
    } catch (err) { console.error(err); }
    setSaving(false);
  };

  // --- Deployment ---
  const startDeploy = async () => {
    if (!selected) return;
    try {
      const manifest = detail?.manifests?.find(m => m.status === 'approved');
      const { data } = await api.post(`/connectors/${selected.id}/deploy`, {
        manifest_id: manifest?.id,
        strategy: deployStrategy,
        canary_percent: canaryPercent,
      });
      setDeployments(prev => [data, ...prev]);
      setShowDeploy(false);
    } catch (err) { console.error(err); }
  };

  const approveDeploy = async (depId) => {
    await api.post(`/connectors/${selected.id}/deployments/${depId}/approve`);
    refreshDeployments();
  };

  const startDeployPhase = async (depId) => {
    await api.post(`/connectors/${selected.id}/deployments/${depId}/start`);
    refreshDeployments();
  };

  const promoteDeploy = async (depId) => {
    await api.post(`/connectors/${selected.id}/deployments/${depId}/promote`);
    refreshDeployments();
  };

  const rollbackDeploy = async (depId) => {
    await api.post(`/connectors/${selected.id}/deployments/${depId}/rollback`);
    refreshDeployments();
  };

  const refreshDeployments = async () => {
    if (!selected) return;
    const { data } = await api.get(`/connectors/${selected.id}/deployments`);
    setDeployments(data.deployments || []);
  };

  const mappedSources = mappings.map(m => m.source_field);
  const mappedTargets = mappings.map(m => m.canonical_field);

  return (
    <div data-testid="connector-builder" className="flex gap-0 h-full -m-6">
      {/* Left — Connector List */}
      <div className="w-64 border-r flex flex-col flex-shrink-0 overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }}>
        <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: '#272E3B' }}>
          <h2 className="font-heading text-sm font-semibold" style={{ color: '#E8ECF1' }}>Connectors</h2>
          <button data-testid="create-connector-btn" onClick={() => setShowCreate(true)} className="p-1 rounded" style={{ color: '#00D4AA' }}><Plus size={16} /></button>
        </div>
        {showCreate && (
          <div className="p-3 border-b space-y-2" style={{ borderColor: '#272E3B' }}>
            <input value={newName} onChange={e => setNewName(e.target.value)} placeholder="Connector name" className="w-full px-3 py-2 rounded text-xs outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }} />
            <select value={newType} onChange={e => setNewType(e.target.value)} className="w-full px-3 py-2 rounded text-xs outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}>
              {['rest_poll', 'rest_webhook', 'db_poll', 'log_tail', 'file_drop', 'sdk_stream', 'message_bus'].map(t => <option key={t} value={t}>{t}</option>)}
            </select>
            <div className="flex gap-2">
              <button onClick={createConnector} className="flex-1 px-3 py-1.5 rounded text-xs font-medium" style={{ background: '#00D4AA', color: '#0A0C10' }}>Create</button>
              <button onClick={() => setShowCreate(false)} className="px-3 py-1.5 rounded text-xs" style={{ color: '#6B7A90' }}>Cancel</button>
            </div>
          </div>
        )}
        <div className="flex-1 overflow-y-auto">
          {connectors.map(c => (
            <button key={c.id} data-testid={`connector-item-${c.name.replace(/\s+/g, '-').toLowerCase()}`}
              onClick={() => selectConnector(c)} className="w-full text-left px-4 py-3 border-b transition-colors"
              style={{ borderColor: '#272E3B20', background: selected?.id === c.id ? 'rgba(0,212,170,0.05)' : 'transparent' }}>
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium" style={{ color: '#E8ECF1' }}>{c.name}</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded" style={{ background: c.status === 'active' ? 'rgba(0,212,170,0.1)' : 'rgba(245,166,35,0.1)', color: c.status === 'active' ? '#00D4AA' : '#F5A623' }}>{c.status}</span>
              </div>
              <div className="text-[10px] mt-1 font-mono" style={{ color: '#6B7A90' }}>{c.type} v{c.version}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Center — Mapping / Deploy panel */}
      <div className="flex-1 flex flex-col overflow-hidden" style={{ background: '#0A0C10' }}>
        {/* Panel Tabs */}
        <div className="flex items-center border-b px-4" style={{ borderColor: '#272E3B', background: '#12151C' }}>
          {[{ id: 'mapping', label: 'Field Mapping' }, { id: 'deploy', label: 'Deployments' }].map(t => (
            <button key={t.id} data-testid={`panel-tab-${t.id}`} onClick={() => setActivePanel(t.id)}
              className="px-4 py-2.5 text-xs font-medium uppercase tracking-wider transition-colors"
              style={{ color: activePanel === t.id ? '#00D4AA' : '#6B7A90', borderBottom: activePanel === t.id ? '2px solid #00D4AA' : '2px solid transparent' }}>
              {t.label}
            </button>
          ))}
          {selected && activePanel === 'mapping' && (
            <div className="ml-auto flex items-center gap-2">
              <span className="text-[10px] font-mono" style={{ color: '#6B7A90' }}>{mappings.length} mappings</span>
              <button data-testid="save-mappings-btn" onClick={saveMappings} disabled={saving}
                className="flex items-center gap-1 px-3 py-1.5 rounded text-xs font-medium" style={{ background: '#00D4AA', color: '#0A0C10' }}>
                <FloppyDisk size={14} /> {saving ? 'Saving...' : 'Save'}
              </button>
            </div>
          )}
          {selected && activePanel === 'deploy' && (
            <button data-testid="new-deploy-btn" onClick={() => setShowDeploy(true)} className="ml-auto flex items-center gap-1 px-3 py-1.5 rounded text-xs font-medium" style={{ background: '#00D4AA', color: '#0A0C10' }}>
              <RocketLaunch size={14} /> New Deployment
            </button>
          )}
        </div>

        {!selected ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <Plugs size={48} className="mx-auto mb-3" style={{ color: '#272E3B' }} />
              <div className="text-sm" style={{ color: '#6B7A90' }}>Select a connector</div>
            </div>
          </div>
        ) : activePanel === 'mapping' ? (
          /* --- DRAG & DROP MAPPING CANVAS --- */
          <div className="flex-1 p-6 overflow-auto dot-grid-bg relative" ref={canvasRef}>
            <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 0 }}>
              {mappings.map(m => (
                <MappingLine key={m.id} sourceIdx={SOURCE_FIELDS.indexOf(m.source_field)} targetIdx={CANONICAL_FIELDS.indexOf(m.canonical_field)} containerRef={canvasRef} />
              ))}
            </svg>
            <div className="relative z-10 flex items-start justify-center gap-16">
              {/* Source fields */}
              <div className="w-56">
                <div className="text-[11px] uppercase tracking-wider mb-3 font-medium" style={{ color: '#6B7A90' }}>Source Fields (drag)</div>
                <div className="space-y-1.5">
                  {SOURCE_FIELDS.map((f, i) => {
                    const isMapped = mappedSources.includes(f);
                    return (
                      <div key={f} data-source-idx={i} draggable onDragStart={() => handleDragStart(f)}
                        className="px-3 py-2 rounded border text-xs font-mono cursor-grab active:cursor-grabbing transition-all"
                        style={{ background: isMapped ? 'rgba(0,212,170,0.08)' : '#12151C', borderColor: isMapped ? '#00D4AA40' : '#272E3B', color: isMapped ? '#00D4AA' : '#E8ECF1' }}>
                        <div className="flex items-center justify-between">
                          <span>{f}</span>
                          {isMapped && <Check size={12} style={{ color: '#00D4AA' }} />}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Center — Active Mappings */}
              <div className="w-48 pt-8">
                <div className="text-[11px] uppercase tracking-wider mb-3 font-medium text-center" style={{ color: '#6B7A90' }}>Active Mappings</div>
                {mappings.length === 0 ? (
                  <div className="text-center text-[10px] py-6" style={{ color: '#6B7A90' }}>
                    Drag source fields onto canonical targets to create mappings
                  </div>
                ) : (
                  <div className="space-y-1">
                    {mappings.map(m => (
                      <div key={m.id} className="flex items-center gap-1 px-2 py-1.5 rounded border text-[10px] font-mono group" style={{ background: '#12151C', borderColor: '#272E3B' }}>
                        <span style={{ color: '#E8ECF1' }}>{m.source_field}</span>
                        <ArrowRight size={10} style={{ color: '#00D4AA' }} />
                        <span style={{ color: '#00D4AA' }}>{m.canonical_field}</span>
                        <button onClick={() => removeMapping(m.id)} className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity" style={{ color: '#FF3B30' }}>
                          <Trash size={12} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Canonical fields (drop targets) */}
              <div className="w-56">
                <div className="text-[11px] uppercase tracking-wider mb-3 font-medium" style={{ color: '#6B7A90' }}>Canonical Fields (drop)</div>
                <div className="space-y-1.5">
                  {CANONICAL_FIELDS.map((f, i) => {
                    const isMapped = mappedTargets.includes(f);
                    return (
                      <div key={f} data-target-idx={i}
                        onDragOver={e => e.preventDefault()}
                        onDrop={() => handleDropOnTarget(f)}
                        className="px-3 py-2 rounded border text-xs font-mono transition-all"
                        style={{ background: isMapped ? 'rgba(0,212,170,0.08)' : '#12151C', borderColor: isMapped ? '#00D4AA40' : dragSource ? '#00D4AA60' : '#00D4AA20', color: '#00D4AA' }}>
                        <div className="flex items-center justify-between">
                          <span>{f}</span>
                          {isMapped && <Check size={12} />}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* --- DEPLOYMENTS PANEL --- */
          <div className="flex-1 overflow-y-auto p-6 space-y-4" data-testid="deployments-panel">
            {/* New Deployment Form */}
            {showDeploy && (
              <div className="rounded border p-4 space-y-3" style={{ background: '#12151C', borderColor: '#00D4AA40' }}>
                <h3 className="font-heading text-sm font-semibold" style={{ color: '#E8ECF1' }}>New Deployment</h3>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] uppercase tracking-wider mb-1" style={{ color: '#6B7A90' }}>Strategy</label>
                    <select data-testid="deploy-strategy" value={deployStrategy} onChange={e => setDeployStrategy(e.target.value)} className="w-full px-3 py-2 rounded text-xs outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}>
                      <option value="canary">Canary (Progressive)</option>
                      <option value="full">Full Rollout</option>
                    </select>
                  </div>
                  {deployStrategy === 'canary' && (
                    <div>
                      <label className="block text-[10px] uppercase tracking-wider mb-1" style={{ color: '#6B7A90' }}>Canary %</label>
                      <input data-testid="canary-percent" type="number" min={1} max={50} value={canaryPercent} onChange={e => setCanaryPercent(parseInt(e.target.value) || 5)}
                        className="w-full px-3 py-2 rounded text-xs outline-none font-mono" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }} />
                    </div>
                  )}
                </div>
                <div className="flex gap-2">
                  <button data-testid="start-deploy-btn" onClick={startDeploy} className="flex items-center gap-1 px-4 py-2 rounded text-xs font-medium" style={{ background: '#00D4AA', color: '#0A0C10' }}>
                    <RocketLaunch size={14} /> Create Deployment
                  </button>
                  <button onClick={() => setShowDeploy(false)} className="px-4 py-2 rounded text-xs" style={{ color: '#6B7A90' }}>Cancel</button>
                </div>
              </div>
            )}

            {/* Deployment List */}
            {deployments.map(dep => (
              <div key={dep.id} data-testid={`deployment-${dep.id}`} className="rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <span className="text-sm font-medium" style={{ color: '#E8ECF1' }}>{dep.connector_name} v{dep.version}</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded ml-2 capitalize" style={{
                      background: dep.status === 'completed' ? 'rgba(0,212,170,0.1)' : dep.status === 'rolled_back' ? 'rgba(255,59,48,0.1)' : dep.status === 'in_progress' ? 'rgba(0,122,255,0.1)' : 'rgba(245,166,35,0.1)',
                      color: dep.status === 'completed' ? '#00D4AA' : dep.status === 'rolled_back' ? '#FF3B30' : dep.status === 'in_progress' ? '#007AFF' : '#F5A623',
                    }}>{dep.status.replace(/_/g, ' ')}</span>
                  </div>
                  <span className="text-[10px] font-mono" style={{ color: '#6B7A90' }}>{dep.strategy} | {dep.affected_devices} devices</span>
                </div>

                {/* Phase Progress */}
                {dep.phases && (
                  <div className="flex items-center gap-1 mb-3">
                    {dep.phases.map((phase, pi) => (
                      <div key={pi} className="flex items-center gap-1">
                        {pi > 0 && <CaretRight size={10} style={{ color: '#272E3B' }} />}
                        <span className="text-[10px] font-mono px-2 py-1 rounded" style={{
                          background: phase.status === 'completed' ? 'rgba(0,212,170,0.15)' : phase.status === 'active' ? 'rgba(0,122,255,0.15)' : '#1A1E2A',
                          color: phase.status === 'completed' ? '#00D4AA' : phase.status === 'active' ? '#007AFF' : '#6B7A90',
                          border: `1px solid ${phase.status === 'active' ? '#007AFF40' : '#272E3B'}`,
                        }}>
                          {phase.name} ({phase.percent}%)
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Health Checks */}
                {dep.health_checks?.length > 0 && (
                  <div className="mb-3 space-y-1">
                    {dep.health_checks.slice(-2).map((hc, hi) => (
                      <div key={hi} className="flex items-center gap-3 text-[10px] font-mono px-3 py-1.5 rounded" style={{ background: '#1A1E2A' }}>
                        <span className="w-1.5 h-1.5 rounded-full" style={{ background: hc.status === 'healthy' ? '#00D4AA' : '#F5A623' }} />
                        <span style={{ color: '#6B7A90' }}>{hc.phase}</span>
                        <span style={{ color: '#E8ECF1' }}>err:{hc.error_rate}%</span>
                        <span style={{ color: '#E8ECF1' }}>lat:{hc.latency_ms}ms</span>
                        <span style={{ color: '#E8ECF1' }}>{hc.events_processed} events</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-2">
                  {dep.status === 'pending_approval' && (
                    <button data-testid={`approve-deploy-${dep.id}`} onClick={() => approveDeploy(dep.id)} className="flex items-center gap-1 px-3 py-1.5 rounded text-xs font-medium" style={{ background: 'rgba(0,212,170,0.1)', color: '#00D4AA' }}>
                      <CheckCircle size={14} /> Approve
                    </button>
                  )}
                  {dep.status === 'approved' && (
                    <button data-testid={`start-deploy-phase-${dep.id}`} onClick={() => startDeployPhase(dep.id)} className="flex items-center gap-1 px-3 py-1.5 rounded text-xs font-medium" style={{ background: 'rgba(0,122,255,0.1)', color: '#007AFF' }}>
                      <RocketLaunch size={14} /> Start
                    </button>
                  )}
                  {dep.status === 'in_progress' && (
                    <>
                      <button data-testid={`promote-deploy-${dep.id}`} onClick={() => promoteDeploy(dep.id)} className="flex items-center gap-1 px-3 py-1.5 rounded text-xs font-medium" style={{ background: 'rgba(0,212,170,0.1)', color: '#00D4AA' }}>
                        <CaretRight size={14} /> Promote
                      </button>
                      <button data-testid={`rollback-deploy-${dep.id}`} onClick={() => rollbackDeploy(dep.id)} className="flex items-center gap-1 px-3 py-1.5 rounded text-xs font-medium" style={{ background: 'rgba(255,59,48,0.1)', color: '#FF3B30' }}>
                        <ArrowsClockwise size={14} /> Rollback
                      </button>
                    </>
                  )}
                </div>

                <div className="text-[10px] font-mono mt-2" style={{ color: '#6B7A90' }}>
                  Created {new Date(dep.created_at).toLocaleString()} by {dep.created_by}
                </div>
              </div>
            ))}
            {deployments.length === 0 && (
              <div className="text-center py-12">
                <RocketLaunch size={40} className="mx-auto mb-3" style={{ color: '#272E3B' }} />
                <div className="text-sm" style={{ color: '#6B7A90' }}>No deployments yet — create one to get started</div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Right — Preview & Validation */}
      <div className="w-72 border-l flex flex-col flex-shrink-0 overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }}>
        <div className="px-4 py-3 border-b" style={{ borderColor: '#272E3B' }}>
          <h2 className="font-heading text-sm font-semibold" style={{ color: '#E8ECF1' }}>Preview & Validation</h2>
        </div>
        {detail ? (
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            <div>
              <div className="text-[11px] uppercase tracking-wider mb-2 font-medium" style={{ color: '#6B7A90' }}>Connector</div>
              <div className="rounded border p-3 text-xs space-y-1.5" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Type</span><span className="font-mono" style={{ color: '#E8ECF1' }}>{detail.type}</span></div>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Version</span><span className="font-mono" style={{ color: '#E8ECF1' }}>{detail.version}</span></div>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Devices</span><span className="font-mono" style={{ color: '#E8ECF1' }}>{detail.device_count}</span></div>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Mappings</span><span className="font-mono" style={{ color: '#00D4AA' }}>{mappings.length}</span></div>
              </div>
            </div>
            <div>
              <div className="text-[11px] uppercase tracking-wider mb-2 font-medium" style={{ color: '#6B7A90' }}>Mapping Coverage</div>
              <div className="rounded border p-3" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
                <div className="flex justify-between text-xs mb-1"><span style={{ color: '#6B7A90' }}>Coverage</span><span className="font-mono" style={{ color: '#00D4AA' }}>{Math.round((mappings.length / CANONICAL_FIELDS.length) * 100)}%</span></div>
                <div className="h-1.5 rounded-full overflow-hidden" style={{ background: '#272E3B' }}>
                  <div className="h-full rounded-full transition-all duration-300" style={{ width: `${(mappings.length / CANONICAL_FIELDS.length) * 100}%`, background: '#00D4AA' }} />
                </div>
                <div className="text-[10px] font-mono mt-2" style={{ color: '#6B7A90' }}>
                  {mappings.length}/{CANONICAL_FIELDS.length} canonical fields mapped
                </div>
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
                  <div className="font-mono" style={{ color: '#6B7A90' }}>v{m.version} | {m.field_mappings} fields</div>
                  {m.status === 'draft' && (
                    <button data-testid={`approve-manifest-${m.id}`} onClick={() => approveManifest(detail.id, m.id)}
                      className="mt-2 px-3 py-1 rounded text-xs font-medium flex items-center gap-1" style={{ background: 'rgba(0,212,170,0.1)', color: '#00D4AA' }}>
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
              <Clock size={28} className="mx-auto mb-2" />
              Select a connector
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
