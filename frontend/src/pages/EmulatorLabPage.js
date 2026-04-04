import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import {
  Flask, Play, Check, X, Clock, Plugs, Terminal, Code,
  ArrowRight, ArrowLeft, Power, GameController, CurrencyDollar,
  Door, Warning, Lightning, Eye, FileCsv, FileText, Sparkle
} from '@phosphor-icons/react';

const STATE_C = { ONLINE: '#00D97E', SYNC: '#FFB800', OPENING: '#FFB800', LOST: '#FF3B3B', CLOSED: '#4A6080', ENABLED: '#00D97E', FAULT: '#FF3B3B', IDLE: '#4A6080', HANDPAY_PENDING: '#FFB800' };
const VERB_ICONS = { INSERT_BILL: CurrencyDollar, INSERT_VOUCHER: FileText, INSERT_COIN: CurrencyDollar, PUSH_PLAY_BUTTON: GameController, PUSH_MAX_BET: GameController, CASH_OUT: CurrencyDollar, REQUEST_HANDPAY: Warning, OPEN_DOOR: Door, CLOSE_DOOR: Door, FORCE_TILT: Lightning, CLEAR_FAULT: Check, SET_CREDITS: CurrencyDollar };

export default function EmulatorLabPage() {
  const [activeTab, setActiveTab] = useState('scripts');
  // Scripts
  const [scripts, setScripts] = useState({ system_scripts: [], custom_scripts: [] });
  const [selectedScript, setSelectedScript] = useState(null);
  const [scriptResult, setScriptResult] = useState(null);
  const [running, setRunning] = useState(false);
  const [scriptRuns, setScriptRuns] = useState([]);
  // SmartEGM
  const [verbs, setVerbs] = useState([]);
  const [egmState, setEgmState] = useState(null);
  const [sessionId, setSessionId] = useState('session-' + Date.now().toString(36));
  // TAR
  const [tarReport, setTarReport] = useState(null);
  // Watchables
  const [watchables, setWatchables] = useState([]);
  // Adapters
  const [adapters, setAdapters] = useState([]);
  const [traces, setTraces] = useState([]);
  const [traceTab, setTraceTab] = useState('g2s');

  useEffect(() => {
    api.get('/emulator-lab/scripts').then(r => setScripts(r.data));
    api.get('/emulator-lab/smart-egm/verbs').then(r => setVerbs(r.data.verbs || []));
    api.get('/emulator-lab/watchables').then(r => setWatchables(r.data.watchables || []));
    api.get('/emulator-lab/scripts/runs?limit=10').then(r => setScriptRuns(r.data.runs || []));
    api.get('/adapters').then(r => setAdapters(r.data.adapters || []));
    api.get('/adapters/traces?limit=50').then(r => setTraces(r.data.traces || []));
  }, []);

  const runScript = async () => {
    if (!selectedScript || running) return;
    setRunning(true); setScriptResult(null);
    try {
      const { data } = await api.post('/emulator-lab/scripts/run', { script_id: selectedScript.id, session_id: sessionId });
      setScriptResult(data);
      setEgmState(data.egm_final_state);
      setScriptRuns(prev => [data, ...prev].slice(0, 10));
    } catch (err) { console.error(err); }
    setRunning(false);
  };

  const executeVerb = async (verb, params = {}) => {
    try {
      const { data } = await api.post('/emulator-lab/smart-egm/execute-verb', { session_id: sessionId, verb, params });
      setEgmState(data.egm_state);
    } catch (err) { console.error(err); }
  };

  const generateTar = async () => {
    const { data } = await api.post('/emulator-lab/tar/generate', { session_id: sessionId });
    setTarReport(data);
  };

  const toggleWatchable = async (id, active) => {
    if (active) await api.post(`/emulator-lab/watchables/${id}/deactivate`);
    else await api.post(`/emulator-lab/watchables/${id}/activate`);
    const { data } = await api.get('/emulator-lab/watchables');
    setWatchables(data.watchables || []);
  };

  const allScripts = [...(scripts.system_scripts || []), ...(scripts.custom_scripts || [])];
  const tabs = [
    { id: 'scripts', label: 'Script Runner' },
    { id: 'egm', label: 'SmartEGM' },
    { id: 'tar', label: 'TAR Report' },
    { id: 'watchables', label: 'Watchables' },
    { id: 'traces', label: 'Protocol Trace' },
  ];

  return (
    <div data-testid="emulator-lab-v2" className="flex gap-0 h-full -m-6">
      {/* Left — Script Library + Controls */}
      <div className="w-64 border-r flex flex-col flex-shrink-0 overflow-hidden" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
        <div className="px-4 py-3 border-b" style={{ borderColor: '#1A2540' }}>
          <h2 className="font-heading text-sm font-semibold flex items-center gap-2" style={{ color: '#F0F4FF' }}>
            <Flask size={16} style={{ color: '#00B4D8' }} /> Emulator Lab
          </h2>
        </div>
        {/* Tab selector */}
        <div className="flex flex-wrap gap-1 px-2 py-2 border-b" style={{ borderColor: '#1A2540' }}>
          {tabs.map(t => (
            <button key={t.id} data-testid={`lab-tab-${t.id}`} onClick={() => setActiveTab(t.id)}
              className="px-2 py-1 rounded text-[9px] font-medium uppercase tracking-wider transition-colors"
              style={{ background: activeTab === t.id ? 'rgba(0,180,216,0.15)' : 'transparent', color: activeTab === t.id ? '#00B4D8' : '#4A6080' }}>
              {t.label}
            </button>
          ))}
        </div>
        {/* Script Library */}
        <div className="px-3 py-2 text-[9px] uppercase tracking-widest font-medium" style={{ color: '#4A6080' }}>Script Library</div>
        <div className="flex-1 overflow-y-auto px-2">
          {allScripts.map(s => (
            <button key={s.id} data-testid={`script-${s.id}`} onClick={() => setSelectedScript(s)}
              className="w-full text-left px-3 py-2 rounded mb-0.5 transition-colors"
              style={{ background: selectedScript?.id === s.id ? 'rgba(0,180,216,0.1)' : 'transparent', color: selectedScript?.id === s.id ? '#00B4D8' : '#8BA3CC' }}>
              <div className="text-xs font-medium">{s.name}</div>
              <div className="text-[9px] font-mono" style={{ color: '#4A6080' }}>{s.category} | v{s.version} | {s.steps?.length || 0} steps</div>
            </button>
          ))}
        </div>
        {/* EGM State */}
        {egmState && (
          <div className="px-3 py-2 border-t space-y-1" style={{ borderColor: '#1A2540' }}>
            <div className="text-[9px] uppercase tracking-widest font-medium flex items-center gap-1" style={{ color: '#4A6080' }}>
              EGM State <span className="w-2 h-2 rounded-full" style={{ background: STATE_C[egmState.state] || '#4A6080' }} />
            </div>
            <div className="text-[10px] font-mono" style={{ color: '#F0F4FF' }}>Credits: {egmState.credits?.toLocaleString()}</div>
            <div className="text-[10px] font-mono" style={{ color: '#00D97E' }}>In: {egmState.coin_in?.toLocaleString()}</div>
            <div className="text-[10px] font-mono" style={{ color: '#FF3B3B' }}>Out: {egmState.coin_out?.toLocaleString()}</div>
            <div className="text-[10px] font-mono" style={{ color: '#4A6080' }}>Games: {egmState.games_played}</div>
          </div>
        )}
      </div>

      {/* Center — Active Tab Content */}
      <div className="flex-1 flex flex-col overflow-hidden" style={{ background: '#070B14' }}>
        {/* ═══ SCRIPT RUNNER ═══ */}
        {activeTab === 'scripts' && (
          <div className="flex-1 overflow-y-auto p-5 space-y-4" data-testid="script-runner">
            {selectedScript ? (
              <>
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-heading text-lg font-semibold" style={{ color: '#F0F4FF' }}>{selectedScript.name}</h3>
                    <span className="text-xs" style={{ color: '#4A6080' }}>{selectedScript.description}</span>
                  </div>
                  <button data-testid="run-script-btn" onClick={runScript} disabled={running}
                    className="flex items-center gap-2 px-5 py-2.5 rounded text-sm font-semibold disabled:opacity-50"
                    style={{ background: running ? '#1A2540' : '#00D97E', color: '#070B14' }}>
                    {running ? <Clock size={16} className="animate-spin" /> : <Play size={16} weight="fill" />} {running ? 'Running...' : 'Run Script'}
                  </button>
                </div>
                {/* Step List */}
                <div className="space-y-1" data-testid="step-list">
                  {selectedScript.steps?.map((step, i) => {
                    const result = scriptResult?.step_results?.[i];
                    const statusColor = result?.status === 'passed' ? '#00D97E' : result?.status === 'failed' ? '#FF3B3B' : '#4A6080';
                    return (
                      <div key={i} className="flex items-center gap-3 px-3 py-2 rounded" style={{ background: result?.status === 'failed' ? 'rgba(255,59,59,0.05)' : '#0C1322', border: `1px solid ${result?.status === 'failed' ? '#FF3B3B30' : '#1A2540'}` }}>
                        <span className="font-mono text-[10px] w-6 text-right" style={{ color: '#4A6080' }}>{i + 1}</span>
                        <span className="w-2 h-2 rounded-full" style={{ background: statusColor }} />
                        <span className="font-mono text-[10px] px-1.5 py-0.5 rounded" style={{ background: '#1A2540', color: '#00B4D8' }}>{step.verb}</span>
                        <span className="text-xs flex-1 truncate" style={{ color: '#8BA3CC' }}>
                          {step.params?.text || step.params?.message || step.params?.verb || step.params?.name || JSON.stringify(step.params).slice(0, 60)}
                        </span>
                        {result && <span className="text-[9px] font-mono" style={{ color: statusColor }}>{result.status}</span>}
                      </div>
                    );
                  })}
                </div>
                {/* Balanced Meters Results */}
                {scriptResult?.balanced_meters && (
                  <div className="rounded-lg border p-4" style={{ background: '#0C1322', borderColor: '#1A2540' }} data-testid="bma-results">
                    <div className="flex items-center gap-2 mb-3">
                      <Sparkle size={16} style={{ color: '#FFB800' }} />
                      <span className="font-heading text-sm font-semibold" style={{ color: '#F0F4FF' }}>Balanced Meters Analysis (Appendix B)</span>
                    </div>
                    <div className="space-y-1">
                      {scriptResult.balanced_meters.map(bm => (
                        <div key={bm.testId} className="flex items-center gap-3 px-3 py-2 rounded" style={{ background: '#111827' }}>
                          {bm.passed ? <Check size={16} style={{ color: '#00D97E' }} /> : <X size={16} style={{ color: '#FF3B3B' }} />}
                          <span className="font-mono text-xs w-12" style={{ color: bm.passed ? '#00D97E' : '#FF3B3B' }}>{bm.testId}</span>
                          <span className="text-xs flex-1" style={{ color: '#F0F4FF' }}>{bm.testName}</span>
                          <span className="font-mono text-[10px]" style={{ color: '#4A6080' }}>{bm.formula}</span>
                          {!bm.passed && <span className="font-mono text-[10px]" style={{ color: '#FF3B3B' }}>delta: {bm.delta}</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center"><div className="text-center">
                <Flask size={48} className="mx-auto mb-3" style={{ color: '#1A2540' }} />
                <div className="text-sm" style={{ color: '#4A6080' }}>Select a script from the library</div>
              </div></div>
            )}
          </div>
        )}

        {/* ═══ SMART EGM ═══ */}
        {activeTab === 'egm' && (
          <div className="flex-1 overflow-y-auto p-5 space-y-4" data-testid="smart-egm-panel">
            <h3 className="font-heading text-lg font-semibold" style={{ color: '#F0F4FF' }}>SmartEGM — 12 Player Verbs</h3>
            <div className="grid grid-cols-4 gap-2" data-testid="verb-buttons">
              {verbs.map(v => {
                const Icon = VERB_ICONS[v.id] || GameController;
                return (
                  <button key={v.id} data-testid={`verb-${v.id}`} onClick={() => executeVerb(v.id, v.id === 'INSERT_BILL' ? { denomination: 2000 } : v.id === 'PUSH_PLAY_BUTTON' ? { wager: 500 } : {})}
                    className="flex flex-col items-center gap-1.5 px-3 py-3 rounded-lg text-center transition-all hover:-translate-y-[1px]"
                    style={{ background: '#0C1322', border: '1px solid #1A2540', color: '#F0F4FF' }}>
                    <Icon size={20} style={{ color: '#00B4D8' }} />
                    <span className="text-[10px] font-medium">{v.label}</span>
                    <span className="text-[8px] font-mono" style={{ color: '#4A6080' }}>{v.state_req}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* ═══ TAR REPORT ═══ */}
        {activeTab === 'tar' && (
          <div className="flex-1 overflow-y-auto p-5 space-y-4" data-testid="tar-panel">
            <div className="flex items-center justify-between">
              <h3 className="font-heading text-lg font-semibold" style={{ color: '#F0F4FF' }}>Transcript Analysis Report</h3>
              <button data-testid="generate-tar-btn" onClick={generateTar} className="flex items-center gap-2 px-4 py-2 rounded text-xs font-medium" style={{ background: '#00B4D8', color: '#070B14' }}>
                <FileText size={14} /> Generate TAR
              </button>
            </div>
            {tarReport && (
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono px-3 py-1 rounded font-bold" style={{ background: tarReport.overall_status === 'GREEN' ? 'rgba(0,217,126,0.15)' : tarReport.overall_status === 'YELLOW' ? 'rgba(255,184,0,0.15)' : 'rgba(255,59,59,0.15)', color: tarReport.overall_status === 'GREEN' ? '#00D97E' : tarReport.overall_status === 'YELLOW' ? '#FFB800' : '#FF3B3B' }}>
                    {tarReport.overall_status}
                  </span>
                  <span className="text-xs font-mono" style={{ color: '#4A6080' }}>{tarReport.total_messages} messages | Session: {tarReport.session_id}</span>
                </div>
                {/* 7 Sections */}
                {[
                  { key: 'comms_sessions', title: '1. Comms Sessions', color: '#00B4D8' },
                  { key: 'session_summaries', title: '2. Session Summary', color: '#00D97E' },
                  { key: 'command_stats', title: '3. Device Commands', color: '#FFB800' },
                  { key: 'event_log', title: '4. Event Log', color: '#8B5CF6' },
                  { key: 'ack_errors', title: '5. G2S ACK Errors', color: '#FF3B3B' },
                  { key: 'balanced_meters', title: '6. Balanced Meters', color: '#EC4899' },
                  { key: 'coverage_map', title: '7. Coverage Map', color: '#06B6D4' },
                ].map(section => {
                  const data = tarReport.sections?.[section.key];
                  return (
                    <div key={section.key} className="rounded-lg border p-3" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
                      <div className="text-[10px] uppercase tracking-wider font-semibold mb-2" style={{ color: section.color }}>{section.title}</div>
                      {Array.isArray(data) ? (
                        <div className="text-[10px] font-mono" style={{ color: '#8BA3CC' }}>
                          {data.length} items
                          {data.slice(0, 5).map((item, i) => (
                            <div key={i} className="flex items-center gap-2 mt-1 px-2 py-1 rounded" style={{ background: '#111827' }}>
                              {item.is_red && <span className="w-1.5 h-1.5 rounded-full" style={{ background: '#FF3B3B' }} />}
                              {item.status && <span style={{ color: item.status === 'RED' ? '#FF3B3B' : item.status === 'YELLOW' ? '#FFB800' : '#00D97E' }}>{item.status}</span>}
                              {item.class && <span style={{ color: '#00B4D8' }}>{item.class}</span>}
                              {item.command && <span>{item.command}</span>}
                              {item.event && <span>{item.event}</span>}
                              {item.exercised !== undefined && <span style={{ color: item.exercised ? '#00D97E' : '#FFB800' }}>{item.class}: {item.exercised ? 'Covered' : 'Not Covered'}</span>}
                              {item.testId && <span>{item.passed ? '✓' : '✗'} {item.testName}</span>}
                            </div>
                          ))}
                        </div>
                      ) : data ? (
                        <div className="text-[10px] font-mono" style={{ color: '#8BA3CC' }}>{JSON.stringify(data).slice(0, 200)}</div>
                      ) : (
                        <div className="text-[10px]" style={{ color: '#4A6080' }}>No data</div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* ═══ WATCHABLES ═══ */}
        {activeTab === 'watchables' && (
          <div className="flex-1 overflow-y-auto p-5 space-y-4" data-testid="watchables-panel">
            <h3 className="font-heading text-lg font-semibold" style={{ color: '#F0F4FF' }}>Watchables — XPath Engine</h3>
            <div className="space-y-2">
              {watchables.map(w => (
                <div key={w.id} className="flex items-center gap-3 px-4 py-3 rounded-lg" style={{ background: '#0C1322', border: `1px solid ${w.is_active ? '#00B4D830' : '#1A2540'}` }}>
                  <button onClick={() => toggleWatchable(w.id, w.is_active)} className="w-8 h-4 rounded-full flex items-center transition-colors"
                    style={{ background: w.is_active ? '#00D97E' : '#1A2540', justifyContent: w.is_active ? 'flex-end' : 'flex-start', padding: '2px' }}>
                    <span className="w-3 h-3 rounded-full" style={{ background: '#F0F4FF' }} />
                  </button>
                  <Eye size={16} style={{ color: w.is_active ? '#00B4D8' : '#4A6080' }} />
                  <div className="flex-1">
                    <div className="text-xs font-medium" style={{ color: '#F0F4FF' }}>{w.name}</div>
                    <div className="font-mono text-[10px]" style={{ color: '#4A6080' }}>{w.expression}</div>
                  </div>
                  <span className="text-[10px]" style={{ color: '#8BA3CC' }}>{w.triggers_on}</span>
                  <span className="font-mono text-[10px] px-2 py-0.5 rounded" style={{ background: '#111827', color: w.match_count > 0 ? '#FFB800' : '#4A6080' }}>{w.match_count} matches</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ═══ PROTOCOL TRACE ═══ */}
        {activeTab === 'traces' && (
          <div className="flex-1 flex flex-col overflow-hidden" data-testid="trace-panel">
            <div className="flex items-center border-b px-4" style={{ borderColor: '#1A2540', background: '#0C1322' }}>
              {['g2s', 'soap', 'protocol'].map(t => (
                <button key={t} data-testid={`trace-tab-${t}`} onClick={() => setTraceTab(t)}
                  className="flex items-center gap-1 px-3 py-2 text-[10px] font-medium uppercase tracking-wider"
                  style={{ color: traceTab === t ? '#00B4D8' : '#4A6080', borderBottom: traceTab === t ? '2px solid #00B4D8' : '2px solid transparent' }}>
                  {t === 'g2s' ? 'G2S Messages' : t === 'soap' ? 'SOAP Transport' : 'Protocol Trace'}
                </button>
              ))}
              <span className="ml-auto text-[9px] font-mono" style={{ color: '#4A6080' }}>{traces.length} traces | {adapters.length} adapters</span>
            </div>
            <div className="flex-1 overflow-y-auto">
              {traces.filter(t => !traceTab || t.channel === traceTab).map((t, i) => (
                <div key={t.id || i} className="px-4 py-1.5 border-b text-[10px] font-mono hover:bg-white/[0.02]" style={{ borderColor: '#1A254010' }}>
                  <div className="flex items-center gap-2">
                    <span style={{ color: '#4A6080' }}>{t.timestamp ? new Date(t.timestamp).toLocaleTimeString() : ''}</span>
                    {t.direction === 'out' ? <ArrowRight size={10} style={{ color: '#00B4D8' }} /> : <ArrowLeft size={10} style={{ color: '#00D97E' }} />}
                    <span className="px-1 rounded" style={{ background: '#1A2540', color: '#00B4D8' }}>{t.protocol}</span>
                    {t.command && <span style={{ color: '#F0F4FF' }}>{t.command}</span>}
                    {t.annotation && <span style={{ color: '#8BA3CC' }}>{t.annotation}</span>}
                  </div>
                  {traceTab === 'protocol' && t.hex && (
                    <div className="mt-1 px-2 py-1 rounded" style={{ background: '#111827' }}>
                      <span style={{ color: '#00D97E' }}>{t.hex.match(/.{1,2}/g)?.join(' ')}</span>
                    </div>
                  )}
                  {(traceTab === 'soap' || traceTab === 'g2s') && t.xml && (
                    <div className="mt-1 px-2 py-1 rounded overflow-x-auto" style={{ background: '#111827' }}>
                      <span style={{ color: '#00D97E' }}>{t.xml.slice(0, 300)}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Right — Results + Past Runs */}
      <div className="w-72 border-l flex-shrink-0 overflow-y-auto" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
        <div className="px-4 py-2 text-[9px] uppercase tracking-widest font-medium" style={{ color: '#4A6080' }}>Past Runs</div>
        {scriptRuns.map(r => (
          <div key={r.id} className="px-4 py-2 border-b text-xs" style={{ borderColor: '#1A254020' }}>
            <div className="flex items-center justify-between">
              <span style={{ color: '#F0F4FF' }}>{r.script_name}</span>
              <span className="font-mono text-[10px]" style={{ color: r.status === 'COMPLETED' ? '#00D97E' : '#FF3B3B' }}>{r.status}</span>
            </div>
            <div className="font-mono text-[10px]" style={{ color: '#4A6080' }}>{r.steps_done}/{r.step_count} steps</div>
          </div>
        ))}
        {/* Connected Adapters */}
        <div className="px-4 py-2 text-[9px] uppercase tracking-widest font-medium border-t" style={{ color: '#4A6080', borderColor: '#1A2540' }}>
          <Plugs size={10} className="inline mr-1" /> Adapters ({adapters.length})
        </div>
        {adapters.map(a => (
          <div key={a.adapter_id} className="px-4 py-2 border-b flex items-center gap-2" style={{ borderColor: '#1A254020' }}>
            <span className="w-2 h-2 rounded-full" style={{ background: STATE_C[a.state] || '#4A6080' }} />
            <span className="text-[10px] font-mono" style={{ color: '#F0F4FF' }}>{a.device_id}</span>
            <span className="text-[9px] font-mono" style={{ color: '#4A6080' }}>{a.protocol}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
