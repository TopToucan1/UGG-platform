import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { MagnifyingGlass, Check, X, Warning, ShieldCheck, CaretRight, Funnel } from '@phosphor-icons/react';

const STATUS_C = { GREEN: '#00D97E', YELLOW: '#FFB800', RED: '#FF3B3B' };

export default function AnalyzerPage() {
  const [results, setResults] = useState([]);
  const [currentResult, setCurrentResult] = useState(null);
  const [sessionId, setSessionId] = useState('live-test');
  const [running, setRunning] = useState(false);

  useEffect(() => { api.get('/analyzer/results?limit=10').then(r => setResults(r.data.results || [])).catch(() => {}); }, []);

  const runAnalyzer = async () => {
    setRunning(true);
    try {
      const { data } = await api.post('/analyzer/run', { session_id: sessionId });
      setCurrentResult(data);
      setResults(prev => [data, ...prev].slice(0, 10));
    } catch (err) { console.error(err); }
    setRunning(false);
  };

  return (
    <div data-testid="analyzer-page" className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-2xl font-bold flex items-center gap-3" style={{ color: '#F0F4FF' }}>
          <MagnifyingGlass size={24} style={{ color: '#00B4D8' }} /> Advanced Transcript Analyzer
        </h1>
        <div className="flex items-center gap-3">
          <input value={sessionId} onChange={e => setSessionId(e.target.value)} placeholder="Session ID" className="px-3 py-2 rounded text-xs outline-none font-mono w-48" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} />
          <button data-testid="run-analyzer-btn" onClick={runAnalyzer} disabled={running} className="px-5 py-2 rounded text-sm font-semibold" style={{ background: '#00B4D8', color: '#070B14' }}>
            {running ? 'Analyzing...' : 'Run Analysis'}
          </button>
        </div>
      </div>

      {currentResult && (
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <span className="text-lg font-mono font-bold px-4 py-1.5 rounded" style={{ background: `${STATUS_C[currentResult.overall_status]}20`, color: STATUS_C[currentResult.overall_status] }}>{currentResult.overall_status}</span>
            <span className="text-xs font-mono" style={{ color: '#4A6080' }}>{currentResult.total_messages} messages | {currentResult.comms_session_count} sessions | {currentResult.rules_evaluated} rules | {currentResult.total_violations} violations ({currentResult.total_errors} errors, {currentResult.total_warnings} warnings)</span>
          </div>

          <div className="space-y-2" data-testid="session-results">
            {currentResult.sessions?.map((s, i) => (
              <div key={i} className="rounded-lg border p-4" style={{ background: '#0C1322', borderColor: `${STATUS_C[s.status]}30` }}>
                <div className="flex items-center gap-3 mb-2">
                  <span className={`w-3 h-3 rounded-full ${s.status === 'RED' ? 'animate-pulse' : ''}`} style={{ background: STATUS_C[s.status] }} />
                  <span className="font-heading text-sm font-semibold" style={{ color: '#F0F4FF' }}>Comms Session {s.session_index}</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded" style={{ background: `${STATUS_C[s.status]}15`, color: STATUS_C[s.status] }}>{s.status}</span>
                  <span className="text-xs font-mono" style={{ color: '#4A6080' }}>{s.message_count} msgs | {s.error_count} err | {s.warning_count} warn</span>
                  {!s.is_complete && <span className="text-[10px] font-mono px-2 py-0.5 rounded" style={{ background: 'rgba(255,59,59,0.1)', color: '#FF3B3B' }}>INCOMPLETE</span>}
                </div>
                {s.violations?.length > 0 && (
                  <div className="space-y-1 ml-6">
                    {s.violations.map((v, vi) => (
                      <div key={vi} className="flex items-center gap-2 px-3 py-2 rounded text-xs" style={{ background: '#111827', borderLeft: `3px solid ${v.severity === 'ERROR' ? '#FF3B3B' : '#FFB800'}` }}>
                        {v.severity === 'ERROR' ? <X size={14} style={{ color: '#FF3B3B' }} /> : <Warning size={14} style={{ color: '#FFB800' }} />}
                        <span className="font-mono" style={{ color: v.severity === 'ERROR' ? '#FF3B3B' : '#FFB800' }}>{v.rule_id}</span>
                        <span style={{ color: '#F0F4FF' }}>{v.detail}</span>
                        <span className="ml-auto text-[10px] font-mono" style={{ color: '#4A6080' }}>{v.g2s_class}</span>
                      </div>
                    ))}
                  </div>
                )}
                {s.violations?.length === 0 && <div className="ml-6 text-xs flex items-center gap-1" style={{ color: '#00D97E' }}><Check size={14} /> All rules passed</div>}
              </div>
            ))}
          </div>
        </div>
      )}

      {results.length > 0 && !currentResult && (
        <div><div className="text-[10px] uppercase tracking-wider mb-2 font-medium" style={{ color: '#4A6080' }}>Past Analyses</div>
        {results.map((r, i) => (
          <div key={i} className="flex items-center gap-3 px-4 py-2 rounded mb-1 text-xs cursor-pointer hover:bg-white/[0.02]" style={{ background: '#0C1322', border: '1px solid #1A2540' }} onClick={() => setCurrentResult(r)}>
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: STATUS_C[r.overall_status] }} />
            <span style={{ color: '#F0F4FF' }}>{r.session_id}</span>
            <span className="font-mono" style={{ color: '#4A6080' }}>{r.total_violations} violations</span>
            <span className="font-mono" style={{ color: '#4A6080' }}>{r.analyzed_at?.slice(0, 16)}</span>
          </div>
        ))}</div>
      )}
    </div>
  );
}
