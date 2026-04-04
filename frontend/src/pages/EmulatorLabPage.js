import { useState, useEffect, useCallback, useRef } from 'react';
import api from '@/lib/api';
import {
  Flask, Play, Check, X, Clock, Plugs, Terminal, Code,
  ArrowRight, ArrowLeft, Power, GameController, CurrencyDollar,
  Door, Warning, Lightning, Eye, FileCsv, FileText, Sparkle,
  Upload, Download, Table
} from '@phosphor-icons/react';
import * as XLSX from 'xlsx';

const STATE_C = { ONLINE: '#00D97E', SYNC: '#FFB800', OPENING: '#FFB800', LOST: '#FF3B3B', CLOSED: '#4A6080', ENABLED: '#00D97E', FAULT: '#FF3B3B', IDLE: '#4A6080', HANDPAY_PENDING: '#FFB800' };
const VERB_ICONS = { INSERT_BILL: CurrencyDollar, INSERT_VOUCHER: FileText, INSERT_COIN: CurrencyDollar, PUSH_PLAY_BUTTON: GameController, PUSH_MAX_BET: GameController, CASH_OUT: CurrencyDollar, REQUEST_HANDPAY: Warning, OPEN_DOOR: Door, CLOSE_DOOR: Door, FORCE_TILT: Lightning, CLEAR_FAULT: Check, SET_CREDITS: CurrencyDollar };

const API_URL = process.env.REACT_APP_BACKEND_URL;

// XML Syntax Highlighter with Find/Find Next/Match Case
function XmlHighlight({ xml, maxLines = 30 }) {
  const [findText, setFindText] = useState('');
  const [matchCase, setMatchCase] = useState(false);
  const [matchCount, setMatchCount] = useState(0);
  const [currentMatch, setCurrentMatch] = useState(0);

  if (!xml) return null;
  const lines = xml.split('\n').slice(0, maxLines);

  // Count matches
  const getMatches = () => {
    if (!findText) return 0;
    const flags = matchCase ? 'g' : 'gi';
    try { return (xml.match(new RegExp(findText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), flags)) || []).length; } catch { return 0; }
  };

  const highlightFind = (text) => {
    if (!findText || !text) return text;
    try {
      const flags = matchCase ? 'g' : 'gi';
      const regex = new RegExp(`(${findText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, flags);
      return text.split(regex).map((part, i) =>
        regex.test(part) ? <mark key={i} style={{ background: '#FFB80050', color: '#FFB800', padding: '0 1px', borderRadius: 2 }}>{part}</mark> : part
      );
    } catch { return text; }
  };

  return (
    <div>
      {/* Find Bar */}
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-t" style={{ background: '#0C1322', border: '1px solid #1A2540', borderBottom: 'none' }}>
        <MagnifyingGlass size={12} style={{ color: '#4A6080' }} />
        <input value={findText} onChange={e => { setFindText(e.target.value); setCurrentMatch(0); }}
          placeholder="Find in XML..." className="flex-1 text-[10px] font-mono outline-none" style={{ background: 'transparent', color: '#F0F4FF' }} />
        <label className="flex items-center gap-1 text-[9px] cursor-pointer" style={{ color: matchCase ? '#00B4D8' : '#4A6080' }}>
          <input type="checkbox" checked={matchCase} onChange={e => setMatchCase(e.target.checked)} className="w-3 h-3" /> Aa
        </label>
        {findText && <span className="text-[9px] font-mono" style={{ color: '#FFB800' }}>{getMatches()} found</span>}
      </div>
      <pre className="text-[10px] font-mono leading-relaxed overflow-x-auto p-3 rounded-b" style={{ background: '#111827', color: '#8BA3CC', border: '1px solid #1A2540', borderTop: 'none' }}>
        {lines.map((line, i) => (
          <div key={i}>
            {line.split(/(<[^>]+>)/g).map((part, j) => {
              const highlighted = findText ? highlightFind(part) : part;
              if (typeof highlighted !== 'string' && findText) return <span key={j}>{highlighted}</span>;
              if (part.startsWith('</')) return <span key={j} style={{ color: '#FF6B6B' }}>{findText ? highlightFind(part) : part}</span>;
              if (part.startsWith('<?')) return <span key={j} style={{ color: '#4A6080' }}>{part}</span>;
              if (part.startsWith('<')) {
                return <span key={j}>{part.split(/(\s+\w+[:=]"[^"]*"|\s+\w+[:=]'[^']*')/g).map((seg, k) => {
                  if (/^\s+\w+[:=]/.test(seg)) {
                    const [attr, ...rest] = seg.split(/[=]/);
                    return <span key={k}><span style={{ color: '#FFB800' }}>{findText ? highlightFind(attr) : attr}</span>=<span style={{ color: '#00D97E' }}>{findText ? highlightFind(rest.join('=')) : rest.join('=')}</span></span>;
                  }
                  if (seg.startsWith('<')) return <span key={k} style={{ color: '#00B4D8' }}>{findText ? highlightFind(seg) : seg}</span>;
                  return <span key={k}>{findText ? highlightFind(seg) : seg}</span>;
                })}</span>;
              }
              return <span key={j}>{findText ? highlightFind(part) : part}</span>;
            })}
          </div>
        ))}
        {xml.split('\n').length > maxLines && <div style={{ color: '#4A6080' }}>... ({xml.split('\n').length - maxLines} more lines)</div>}
      </pre>
    </div>
  );
}

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
  // Device Templates
  const [parsedTemplates, setParsedTemplates] = useState([]);
  const [templateXml, setTemplateXml] = useState('');
  const [parsedResult, setParsedResult] = useState(null);
  // Virtual Scroll Transcripts
  const [txStats, setTxStats] = useState(null);
  const [txRows, setTxRows] = useState([]);
  const [txTotal, setTxTotal] = useState(0);
  const [txSearch, setTxSearch] = useState('');
  const [txSelected, setTxSelected] = useState(null);
  const listRef = useRef(null);
  // Live G2S Connection
  const [liveConns, setLiveConns] = useState([]);
  const [liveUrl, setLiveUrl] = useState('');
  const [liveDeviceId, setLiveDeviceId] = useState('EGM-001');
  const [liveCmdClass, setLiveCmdClass] = useState('cabinet');
  const [liveCmdName, setLiveCmdName] = useState('getDeviceStatus');
  const [liveResult, setLiveResult] = useState(null);
  // Session Recording
  const [recordings, setRecordings] = useState([]);
  const [activeRecording, setActiveRecording] = useState(null);
  const [replaySpeed, setReplaySpeed] = useState(1);
  const [replayResult, setReplayResult] = useState(null);

  useEffect(() => {
    api.get('/emulator-lab/scripts').then(r => setScripts(r.data));
    api.get('/emulator-lab/smart-egm/verbs').then(r => setVerbs(r.data.verbs || []));
    api.get('/emulator-lab/watchables').then(r => setWatchables(r.data.watchables || []));
    api.get('/emulator-lab/scripts/runs?limit=10').then(r => setScriptRuns(r.data.runs || []));
    api.get('/adapters').then(r => setAdapters(r.data.adapters || []));
    api.get('/adapters/traces?limit=50').then(r => setTraces(r.data.traces || []));
    api.get('/emulator-lab/templates/parsed').then(r => setParsedTemplates(r.data.templates || []));
    api.get('/emulator-lab/recordings').then(r => setRecordings(r.data.recordings || []));
    loadTranscriptWindow(0);
  }, []);

  const loadTranscriptWindow = async (offset) => {
    const params = new URLSearchParams({ session_id: sessionId, offset: String(offset), limit: '200' });
    if (txSearch) params.set('search', txSearch);
    if (traceTab !== 'all') params.set('channel', traceTab === 'g2s' ? 'G2S' : traceTab === 'soap' ? 'SOAP' : 'PROTOCOL_TRACE');
    const { data } = await api.get(`/emulator-lab/transcripts/window?${params}`);
    setTxRows(data.rows || []);
    setTxTotal(data.total || 0);
    // Also get stats
    const statsRes = await api.get(`/emulator-lab/transcripts/stats?session_id=${sessionId}`);
    setTxStats(statsRes.data);
  };

  const parseTemplateXml = async () => {
    if (!templateXml.trim()) return;
    try {
      const { data } = await api.post('/emulator-lab/templates/parse-xml-text', { xml: templateXml });
      setParsedResult(data);
      setParsedTemplates(prev => [data, ...prev]);
    } catch (err) {
      setParsedResult({ error: err.response?.data?.detail || err.message });
    }
  };

  const exportBmaExcel = () => {
    if (!scriptResult?.balanced_meters) return;
    const ws = XLSX.utils.json_to_sheet(scriptResult.balanced_meters.map(r => ({
      'Test ID': r.testId, 'Test Name': r.testName, 'Result': r.passed ? 'PASS' : 'FAIL',
      'Left Value': r.leftValue, 'Right Value': r.rightValue, 'Delta': r.delta,
      'Formula': r.formula, 'Details': r.details,
    })));
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Balanced Meters');
    XLSX.writeFile(wb, `balanced_meters_${Date.now()}.xlsx`);
  };

  const seedBulkTranscripts = async (count) => {
    await api.post('/emulator-lab/transcripts/seed-bulk', { session_id: sessionId, count });
    loadTranscriptWindow(0);
  };

  const connectLive = async () => {
    const { data } = await api.post('/emulator-lab/smart-egm/connect-live', { session_id: sessionId, device_id: liveDeviceId, egm_url: liveUrl || undefined });
    setLiveConns(prev => [...prev, data]);
    api.get('/emulator-lab/smart-egm/live-status').then(r => setLiveConns(r.data.connections || []));
  };

  const sendLiveCommand = async () => {
    const { data } = await api.post('/emulator-lab/smart-egm/send-live', { session_id: sessionId, command_class: liveCmdClass, command: liveCmdName });
    setLiveResult(data);
    loadTranscriptWindow(0);
  };

  const exportSession = () => {
    window.open(`${API_URL}/api/emulator-lab/export-session/${sessionId}`, '_blank');
  };

  const startRecording = async () => {
    const { data } = await api.post('/emulator-lab/recording/start', { session_id: sessionId });
    setActiveRecording(data);
    setRecordings(prev => [data, ...prev]);
  };

  const stopRecording = async () => {
    if (!activeRecording) return;
    await api.post(`/emulator-lab/recording/stop/${activeRecording.id}`);
    setActiveRecording(null);
    const { data } = await api.get('/emulator-lab/recordings');
    setRecordings(data.recordings || []);
  };

  const replayRecording = async (recId) => {
    setReplayResult(null);
    const { data } = await api.post(`/emulator-lab/recording/replay/${recId}`, { target_session_id: sessionId, speed: replaySpeed });
    setReplayResult(data);
    loadTranscriptWindow(0);
  };

  const connectProduction = async () => {
    const { data } = await api.post('/emulator-lab/smart-egm/connect-production', { session_id: sessionId, device_id: liveDeviceId, egm_url: liveUrl || undefined, verbose: true });
    setLiveResult(data);
    api.get('/emulator-lab/smart-egm/live-status').then(r => setLiveConns(r.data.connections || []));
  };

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
    { id: 'live', label: 'Live G2S' },
    { id: 'templates', label: 'Templates' },
    { id: 'tar', label: 'TAR Report' },
    { id: 'watchables', label: 'Watchables' },
    { id: 'traces', label: 'Transcripts' },
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
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Sparkle size={16} style={{ color: '#FFB800' }} />
                        <span className="font-heading text-sm font-semibold" style={{ color: '#F0F4FF' }}>Balanced Meters Analysis (Appendix B)</span>
                      </div>
                      <button data-testid="export-bma-excel" onClick={exportBmaExcel} className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[10px] font-medium" style={{ background: 'rgba(0,180,216,0.1)', color: '#00B4D8', border: '1px solid rgba(0,180,216,0.2)' }}>
                        <Download size={12} /> Export Excel
                      </button>
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

        {/* ═══ LIVE G2S CONNECTION ═══ */}
        {activeTab === 'live' && (
          <div className="flex-1 overflow-y-auto p-5 space-y-4" data-testid="live-g2s-panel">
            <h3 className="font-heading text-lg font-semibold" style={{ color: '#F0F4FF' }}>Live G2S SOAP Connection</h3>
            {/* Connect Form */}
            <div className="rounded-lg border p-4 space-y-3" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-[9px] uppercase tracking-wider mb-1" style={{ color: '#4A6080' }}>EGM SOAP Endpoint</label>
                  <input data-testid="live-egm-url" value={liveUrl} onChange={e => setLiveUrl(e.target.value)} placeholder="https://egm-ip:8443/g2s (leave blank for virtual)"
                    className="w-full px-3 py-2 rounded text-xs outline-none font-mono" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} />
                </div>
                <div>
                  <label className="block text-[9px] uppercase tracking-wider mb-1" style={{ color: '#4A6080' }}>Device ID</label>
                  <input value={liveDeviceId} onChange={e => setLiveDeviceId(e.target.value)} className="w-full px-3 py-2 rounded text-xs outline-none font-mono" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} />
                </div>
                <div className="flex items-end">
                  <button data-testid="connect-live-btn" onClick={connectLive} className="w-full flex items-center justify-center gap-2 py-2 rounded text-xs font-medium" style={{ background: '#00D97E', color: '#070B14' }}>
                    <Plugs size={14} /> Connect
                  </button>
                </div>
              </div>
            </div>
            {/* Command Builder */}
            <div className="rounded-lg border p-4 space-y-3" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
              <div className="text-[10px] uppercase tracking-wider font-medium" style={{ color: '#4A6080' }}>Send G2S Command</div>
              <div className="grid grid-cols-4 gap-3">
                <div>
                  <label className="block text-[9px] uppercase tracking-wider mb-1" style={{ color: '#4A6080' }}>Class</label>
                  <select value={liveCmdClass} onChange={e => setLiveCmdClass(e.target.value)} className="w-full px-3 py-2 rounded text-xs outline-none" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }}>
                    {['cabinet', 'communications', 'gamePlay', 'meters', 'noteAcceptor', 'voucher', 'handpay', 'eventHandler', 'bonus', 'player', 'progressive', 'mediaDisplay', 'download', 'GAT'].map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-[9px] uppercase tracking-wider mb-1" style={{ color: '#4A6080' }}>Command</label>
                  <select value={liveCmdName} onChange={e => setLiveCmdName(e.target.value)} className="w-full px-3 py-2 rounded text-xs outline-none" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }}>
                    {['getDeviceStatus', 'setDeviceState', 'commsOnLine', 'commsOnLineAck', 'setCommsState', 'keepAlive', 'getMeterInfo', 'setEventSub', 'getEventSub', 'commitVoucher', 'doVerification'].map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
                <div className="col-span-2 flex items-end gap-2">
                  <button data-testid="send-live-cmd-btn" onClick={sendLiveCommand} className="flex-1 flex items-center justify-center gap-2 py-2 rounded text-xs font-medium" style={{ background: '#00B4D8', color: '#070B14' }}>
                    <ArrowRight size={14} /> Send
                  </button>
                  <button data-testid="connect-production-btn" onClick={connectProduction} className="flex items-center gap-1.5 px-3 py-2 rounded text-xs font-medium" style={{ background: '#00D97E', color: '#070B14' }}>
                    <Plugs size={14} /> Full Startup
                  </button>
                  <button data-testid="export-session-btn" onClick={exportSession} className="flex items-center gap-1.5 px-3 py-2 rounded text-xs font-medium" style={{ background: 'rgba(0,180,216,0.1)', color: '#00B4D8', border: '1px solid rgba(0,180,216,0.2)' }}>
                    <Download size={14} /> ZIP
                  </button>
                </div>
              </div>
            </div>
            {/* Last Result */}
            {liveResult && (
              <div className="rounded-lg border p-4" style={{ background: '#0C1322', borderColor: liveResult.status === 'error' ? '#FF3B3B30' : '#00D97E30' }}>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded" style={{ background: liveResult.status === 'error' ? 'rgba(255,59,59,0.1)' : 'rgba(0,217,126,0.1)', color: liveResult.status === 'error' ? '#FF3B3B' : '#00D97E' }}>{liveResult.status}</span>
                  <span className="font-mono text-xs" style={{ color: '#F0F4FF' }}>{liveResult.class}.{liveResult.command}</span>
                  {liveResult.ack_error && <span className="font-mono text-[10px]" style={{ color: '#FF3B3B' }}>ACK: {liveResult.ack_error}</span>}
                  {liveResult.message_count && <span className="font-mono text-[10px]" style={{ color: '#4A6080' }}>msg #{liveResult.message_count}</span>}
                </div>
                {liveResult.response_commands?.length > 0 && (
                  <div className="space-y-1">{liveResult.response_commands.map((cmd, i) => (
                    <div key={i} className="text-[10px] font-mono px-2 py-1 rounded" style={{ background: '#111827' }}>
                      <span style={{ color: '#00B4D8' }}>{cmd.element}</span>
                      {Object.entries(cmd.attributes || {}).map(([k, v]) => <span key={k} className="ml-2"><span style={{ color: '#FFB800' }}>{k}</span>=<span style={{ color: '#00D97E' }}>"{v}"</span></span>)}
                    </div>
                  ))}</div>
                )}
                {liveResult.error && <div className="text-xs mt-1" style={{ color: '#FF3B3B' }}>{liveResult.error}</div>}
              </div>
            )}
            {/* Startup Steps Result */}
            {liveResult?.startup_steps && (
              <div className="rounded-lg border p-4" style={{ background: '#0C1322', borderColor: '#00D97E30' }}>
                <div className="text-[10px] uppercase tracking-wider mb-2 font-medium" style={{ color: '#4A6080' }}>G2S Startup Sequence ({liveResult.startup_count} steps)</div>
                <div className="space-y-1">
                  {liveResult.startup_steps.map((s, i) => (
                    <div key={i} className="flex items-center gap-2 px-2 py-1 rounded text-[10px] font-mono" style={{ background: '#111827' }}>
                      <span className="w-5 text-right" style={{ color: '#4A6080' }}>{s.step}</span>
                      <span className="w-2 h-2 rounded-full" style={{ background: s.status === 'completed' ? '#00D97E' : '#FF3B3B' }} />
                      <span style={{ color: '#00B4D8' }}>{s.class}</span>
                      <span style={{ color: '#F0F4FF' }}>{s.command}</span>
                      <span className="ml-auto" style={{ color: s.status === 'completed' ? '#00D97E' : '#FF3B3B' }}>{s.status}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Session Recording */}
            <div className="rounded-lg border p-4 space-y-3" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase tracking-wider font-medium" style={{ color: '#4A6080' }}>Session Recording</span>
                {!activeRecording ? (
                  <button data-testid="start-recording-btn" onClick={startRecording} className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[10px] font-medium" style={{ background: '#FF3B3B', color: '#F0F4FF' }}>
                    <span className="w-2 h-2 rounded-full bg-white animate-pulse" /> Start Recording
                  </button>
                ) : (
                  <button data-testid="stop-recording-btn" onClick={stopRecording} className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[10px] font-medium" style={{ background: '#FF3B3B20', color: '#FF3B3B', border: '1px solid #FF3B3B40' }}>
                    <span className="w-2 h-2 rounded-sm" style={{ background: '#FF3B3B' }} /> Stop Recording
                  </button>
                )}
              </div>
              {activeRecording && (
                <div className="flex items-center gap-2 text-[10px] font-mono" style={{ color: '#FF3B3B' }}>
                  <span className="w-2 h-2 rounded-full animate-pulse" style={{ background: '#FF3B3B' }} />
                  Recording: {activeRecording.name} (session: {activeRecording.session_id})
                </div>
              )}
              {/* Replay Controls */}
              {recordings.filter(r => r.status === 'COMPLETED').length > 0 && (
                <div>
                  <div className="text-[9px] uppercase tracking-wider mb-1 font-medium" style={{ color: '#4A6080' }}>Replay</div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-[10px]" style={{ color: '#4A6080' }}>Speed:</span>
                    {[0.5, 1, 2, 5, 0].map(s => (
                      <button key={s} onClick={() => setReplaySpeed(s)} className="px-2 py-0.5 rounded text-[9px] font-mono" style={{ background: replaySpeed === s ? '#00B4D820' : '#111827', color: replaySpeed === s ? '#00B4D8' : '#4A6080', border: '1px solid #1A2540' }}>
                        {s === 0 ? 'Instant' : `${s}x`}
                      </button>
                    ))}
                  </div>
                  {recordings.filter(r => r.status === 'COMPLETED').map(rec => (
                    <div key={rec.id} className="flex items-center gap-2 px-2 py-1.5 rounded mb-1 text-[10px]" style={{ background: '#111827' }}>
                      <span style={{ color: '#F0F4FF' }}>{rec.name}</span>
                      <span className="font-mono" style={{ color: '#4A6080' }}>{rec.event_count} events</span>
                      <span className="font-mono" style={{ color: '#4A6080' }}>{rec.replay_count}x replayed</span>
                      <button data-testid={`replay-${rec.id}`} onClick={() => replayRecording(rec.id)} className="ml-auto px-2 py-0.5 rounded text-[9px] font-medium" style={{ background: '#00B4D820', color: '#00B4D8' }}>
                        <Play size={10} className="inline mr-1" /> Replay
                      </button>
                    </div>
                  ))}
                </div>
              )}
              {replayResult && (
                <div className="text-[10px] font-mono px-2 py-1 rounded" style={{ background: '#111827', color: '#00D97E' }}>
                  Replayed {replayResult.replayed} commands at {replayResult.speed}x speed
                </div>
              )}
            </div>

            {/* Live Connections */}
            {liveConns.length > 0 && (
              <div><div className="text-[10px] uppercase tracking-wider mb-2 font-medium" style={{ color: '#4A6080' }}>Active Connections</div>
              {liveConns.map(c => (
                <div key={c.session_id} className="flex items-center gap-3 px-3 py-2 rounded mb-1 text-xs" style={{ background: '#0C1322', border: '1px solid #1A2540' }}>
                  <span className="w-2 h-2 rounded-full" style={{ background: '#00D97E' }} />
                  <span className="font-mono" style={{ color: '#F0F4FF' }}>{c.device_id}</span>
                  <span className="font-mono" style={{ color: '#4A6080' }}>{c.egm_url || 'virtual'}</span>
                  <span className="font-mono" style={{ color: '#00B4D8' }}>{c.message_count} msgs</span>
                </div>
              ))}</div>
            )}
          </div>
        )}

        {/* ═══ DEVICE TEMPLATES ═══ */}
        {activeTab === 'templates' && (
          <div className="flex-1 overflow-y-auto p-5 space-y-4" data-testid="templates-panel">
            <h3 className="font-heading text-lg font-semibold" style={{ color: '#F0F4FF' }}>Device Template XML Parser</h3>
            <div className="rounded-lg border p-4" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
              <div className="text-[10px] uppercase tracking-wider mb-2 font-medium" style={{ color: '#4A6080' }}>Paste Device Template XML</div>
              <textarea data-testid="template-xml-input" value={templateXml} onChange={e => setTemplateXml(e.target.value)} rows={8}
                className="w-full px-3 py-2 rounded text-xs font-mono outline-none resize-none" style={{ background: '#111827', border: '1px solid #1A2540', color: '#00D97E' }}
                placeholder={'<deviceTemplate version="1.0" manufacturer="ACE" model="Velocity-3">\n  <metadata>...</metadata>\n  <denominations>...</denominations>\n  <devices>...</devices>\n  <gameOutcomes>...</gameOutcomes>\n</deviceTemplate>'} />
              <button data-testid="parse-template-btn" onClick={parseTemplateXml} className="mt-2 flex items-center gap-2 px-4 py-2 rounded text-xs font-medium" style={{ background: '#00B4D8', color: '#070B14' }}>
                <Code size={14} /> Parse Template
              </button>
            </div>
            {parsedResult && !parsedResult.error && (
              <div className="rounded-lg border p-4 space-y-3" style={{ background: '#0C1322', borderColor: '#00D97E30' }}>
                <div className="flex items-center gap-2"><Check size={16} style={{ color: '#00D97E' }} /><span className="font-heading text-sm font-semibold" style={{ color: '#F0F4FF' }}>{parsedResult.manufacturer} {parsedResult.model} v{parsedResult.software_version}</span></div>
                <div className="grid grid-cols-3 gap-3">
                  <div className="rounded p-2" style={{ background: '#111827' }}><div className="text-[9px] uppercase tracking-wider" style={{ color: '#4A6080' }}>Schema</div><div className="font-mono text-xs" style={{ color: '#F0F4FF' }}>{parsedResult.metadata?.g2s_schema_version}</div></div>
                  <div className="rounded p-2" style={{ background: '#111827' }}><div className="text-[9px] uppercase tracking-wider" style={{ color: '#4A6080' }}>Serial</div><div className="font-mono text-xs" style={{ color: '#F0F4FF' }}>{parsedResult.metadata?.serial_number}</div></div>
                  <div className="rounded p-2" style={{ background: '#111827' }}><div className="text-[9px] uppercase tracking-wider" style={{ color: '#4A6080' }}>Signature</div><div className="font-mono text-xs truncate" style={{ color: '#F0F4FF' }}>{parsedResult.metadata?.software_signature}</div></div>
                </div>
                <div><div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: '#4A6080' }}>Denominations</div><div className="flex gap-1.5">{parsedResult.denominations?.map(d => <span key={d.value} className="font-mono text-[10px] px-2 py-0.5 rounded" style={{ background: '#111827', color: '#FFB800' }}>{d.display}</span>)}</div></div>
                <div><div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: '#4A6080' }}>G2S Classes ({parsedResult.devices?.length})</div><div className="flex flex-wrap gap-1">{parsedResult.devices?.map(d => <span key={d.class} className="font-mono text-[9px] px-2 py-0.5 rounded" style={{ background: d.host_enabled ? 'rgba(0,217,126,0.1)' : '#111827', color: d.host_enabled ? '#00D97E' : '#4A6080', border: `1px solid ${d.host_enabled ? '#00D97E30' : '#1A2540'}` }}>{d.class}</span>)}</div></div>
                <div><div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: '#4A6080' }}>Win Levels</div><div className="space-y-1">{parsedResult.win_levels?.map(wl => <div key={wl.id} className="flex items-center gap-3 px-2 py-1 rounded text-[10px] font-mono" style={{ background: '#111827' }}><span style={{ color: '#F0F4FF' }}>{wl.name}</span><span style={{ color: '#4A6080' }}>{(wl.probability * 100).toFixed(1)}%</span><span style={{ color: wl.multiplier > 0 ? '#FFB800' : '#4A6080' }}>{wl.multiplier}x</span></div>)}</div></div>
              </div>
            )}
            {parsedResult?.error && <div className="rounded p-3 text-xs" style={{ background: 'rgba(255,59,59,0.05)', color: '#FF3B3B', border: '1px solid #FF3B3B30' }}>{parsedResult.error}</div>}
            {parsedTemplates.length > 0 && (
              <div><div className="text-[10px] uppercase tracking-wider mb-2 font-medium" style={{ color: '#4A6080' }}>Parsed Templates ({parsedTemplates.length})</div>
              <div className="space-y-1">{parsedTemplates.map(t => <div key={t.id} className="flex items-center gap-3 px-3 py-2 rounded text-xs" style={{ background: '#0C1322', border: '1px solid #1A2540' }}><span style={{ color: '#F0F4FF' }}>{t.manufacturer} {t.model}</span><span className="font-mono" style={{ color: '#4A6080' }}>v{t.software_version}</span><span className="font-mono" style={{ color: '#00B4D8' }}>{t.devices?.length || 0} classes</span><span className="font-mono" style={{ color: '#FFB800' }}>{t.denominations?.length || 0} denoms</span></div>)}</div></div>
            )}
          </div>
        )}

        {/* ═══ VIRTUAL SCROLL TRANSCRIPTS ═══ */}
        {activeTab === 'traces' && (
          <div className="flex-1 flex flex-col overflow-hidden" data-testid="transcript-panel">
            <div className="flex items-center gap-2 px-4 py-2 border-b" style={{ borderColor: '#1A2540', background: '#0C1322' }}>
              {['g2s', 'soap', 'protocol'].map(t => (
                <button key={t} data-testid={`tx-tab-${t}`} onClick={() => { setTraceTab(t); setTimeout(() => loadTranscriptWindow(0), 100); }}
                  className="px-2 py-1 rounded text-[9px] font-medium uppercase tracking-wider"
                  style={{ background: traceTab === t ? 'rgba(0,180,216,0.15)' : 'transparent', color: traceTab === t ? '#00B4D8' : '#4A6080' }}>
                  {t === 'g2s' ? 'G2S Messages' : t === 'soap' ? 'SOAP' : 'Protocol'}
                </button>
              ))}
              <div className="flex-1" />
              <input value={txSearch} onChange={e => setTxSearch(e.target.value)} onKeyDown={e => e.key === 'Enter' && loadTranscriptWindow(0)} placeholder="Search..."
                className="px-2 py-1 rounded text-[10px] outline-none w-40" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} />
              <span className="text-[9px] font-mono" style={{ color: '#4A6080' }}>{txTotal.toLocaleString()} rows</span>
              {txStats && <span className="text-[9px] font-mono" style={{ color: txStats.error_count > 0 ? '#FF3B3B' : '#4A6080' }}>{txStats.error_count} errors</span>}
              <button onClick={() => seedBulkTranscripts(10000)} className="text-[9px] px-2 py-1 rounded" style={{ background: '#1A2540', color: '#4A6080' }}>+10K</button>
            </div>
            <div className="flex-1 overflow-hidden" data-testid="virtual-transcript-list">
              {txRows.length > 0 ? (
                <div className="h-full overflow-y-auto" style={{ background: '#070B14' }}>
                  {txRows.map((t, index) => {
                    const isErr = t.state === 'Error' || t.state === 'Special Error';
                    const isExpanded = txSelected === (t.id || index);
                    return (
                      <div key={t.id || index} data-testid={`tx-row-${index}`}
                        onClick={() => setTxSelected(isExpanded ? null : (t.id || index))}
                        className="border-b cursor-pointer hover:bg-white/[0.02] transition-colors"
                        style={{ borderColor: '#1A254010', background: isErr ? 'rgba(255,59,59,0.03)' : isExpanded ? 'rgba(0,180,216,0.03)' : 'transparent' }}>
                        <div className="flex items-center gap-2 px-4 py-1 text-[10px] font-mono" style={{ height: 32 }}>
                          <span className="w-14 flex-shrink-0" style={{ color: '#4A6080' }}>{t.occurred_at ? new Date(t.occurred_at).toLocaleTimeString() : ''}</span>
                          {t.direction === 'TX' ? <ArrowRight size={10} style={{ color: '#00B4D8' }} /> : <ArrowLeft size={10} style={{ color: '#00D97E' }} />}
                          <span className="w-5 flex-shrink-0" style={{ color: t.direction === 'TX' ? '#00B4D8' : '#00D97E' }}>{t.direction}</span>
                          <span className="px-1 rounded flex-shrink-0" style={{ background: '#1A2540', color: '#00B4D8' }}>{t.channel}</span>
                          <span className="flex-shrink-0" style={{ color: '#8BA3CC' }}>{t.command_class}</span>
                          <span className="truncate" style={{ color: '#F0F4FF' }}>{t.command_name}</span>
                          {isErr && <span className="px-1 rounded flex-shrink-0" style={{ background: 'rgba(255,59,59,0.15)', color: '#FF3B3B' }}>{t.state}</span>}
                          {t.error_code && <span className="flex-shrink-0" style={{ color: '#FF3B3B' }}>{t.error_code}</span>}
                        </div>
                        {isExpanded && t.payload_xml && (
                          <div className="px-4 pb-2" onClick={e => e.stopPropagation()}>
                            <XmlHighlight xml={t.payload_xml} maxLines={25} />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="flex items-center justify-center h-full text-xs" style={{ color: '#4A6080' }}>
                  <div className="text-center"><Flask size={32} className="mx-auto mb-2" /><div>Run a script or seed transcripts to see data</div><button onClick={() => seedBulkTranscripts(5000)} className="mt-2 px-3 py-1.5 rounded text-[10px]" style={{ background: '#1A2540', color: '#00B4D8' }}>Seed 5K Transcripts</button></div>
                </div>
              )}
            </div>
            {txTotal > txRows.length && (
              <div className="flex items-center justify-center gap-3 px-4 py-2 border-t" style={{ borderColor: '#1A2540', background: '#0C1322' }}>
                <button onClick={() => loadTranscriptWindow(Math.max(0, (txRows[0]?._offset || 0) - 200))} className="px-3 py-1 rounded text-[10px] font-mono" style={{ background: '#1A2540', color: '#F0F4FF' }}>Prev Page</button>
                <span className="text-[9px] font-mono" style={{ color: '#4A6080' }}>Showing {txRows.length} of {txTotal.toLocaleString()}</span>
                <button onClick={() => loadTranscriptWindow((txRows.length))} className="px-3 py-1 rounded text-[10px] font-mono" style={{ background: '#1A2540', color: '#F0F4FF' }}>Next Page</button>
              </div>
            )}
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
