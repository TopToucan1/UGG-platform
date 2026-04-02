import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Flask, Play, Stop, Check, X, Clock } from '@phosphor-icons/react';

function SeverityDot({ severity }) {
  const c = { critical: '#FF3B30', warning: '#F5A623', info: '#007AFF' };
  return <span className="w-1.5 h-1.5 rounded-full inline-block" style={{ background: c[severity] || '#6B7A90' }} />;
}

export default function EmulatorLabPage() {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState(null);
  const [runResult, setRunResult] = useState(null);
  const [running, setRunning] = useState(false);
  const [pastRuns, setPastRuns] = useState([]);

  useEffect(() => {
    api.get('/emulator/scenarios').then(r => setScenarios(r.data.scenarios || [])).catch(() => {});
    api.get('/emulator/runs?limit=10').then(r => setPastRuns(r.data.runs || [])).catch(() => {});
  }, []);

  const runScenario = async () => {
    if (!selectedScenario || running) return;
    setRunning(true);
    setRunResult(null);
    try {
      const { data } = await api.post('/emulator/run', { scenario_id: selectedScenario.id });
      setRunResult(data);
      setPastRuns(prev => [data, ...prev].slice(0, 10));
    } catch (err) {
      console.error(err);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div data-testid="emulator-lab" className="flex flex-col h-full -m-6">
      {/* Scenario Ribbon */}
      <div className="flex items-center gap-4 px-6 py-3 border-b flex-shrink-0" style={{ background: '#12151C', borderColor: '#272E3B' }}>
        <Flask size={20} style={{ color: '#00D4AA' }} />
        <select
          data-testid="scenario-selector"
          value={selectedScenario?.id || ''}
          onChange={e => setSelectedScenario(scenarios.find(s => s.id === e.target.value))}
          className="px-3 py-2 rounded text-sm outline-none min-w-64"
          style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}
        >
          <option value="">Select Scenario...</option>
          {scenarios.map(s => (
            <option key={s.id} value={s.id}>{s.name} ({s.protocol})</option>
          ))}
        </select>

        <button
          data-testid="run-scenario-btn"
          onClick={runScenario}
          disabled={!selectedScenario || running}
          className="flex items-center gap-2 px-4 py-2 rounded text-sm font-medium disabled:opacity-50"
          style={{ background: '#00D4AA', color: '#0A0C10' }}
        >
          {running ? <Clock size={16} className="animate-spin" /> : <Play size={16} weight="fill" />}
          {running ? 'Running...' : 'Run'}
        </button>

        {runResult && (
          <div className="flex items-center gap-3 ml-auto text-xs font-mono">
            <span style={{ color: '#6B7A90' }}>Events: <span style={{ color: '#E8ECF1' }}>{runResult.event_count}</span></span>
            <span style={{ color: '#6B7A90' }}>Assertions: <span style={{ color: runResult.assertions_passed === runResult.assertions_total ? '#00D4AA' : '#FF3B30' }}>{runResult.assertions_passed}/{runResult.assertions_total}</span></span>
          </div>
        )}
      </div>

      {/* Selected Scenario Info */}
      {selectedScenario && (
        <div className="px-6 py-2 border-b text-xs" style={{ borderColor: '#272E3B', background: '#0A0C10' }}>
          <span style={{ color: '#A3AEBE' }}>{selectedScenario.description}</span>
          <span className="ml-4 font-mono" style={{ color: '#6B7A90' }}>{selectedScenario.device_count} devices | {selectedScenario.duration_seconds}s</span>
        </div>
      )}

      {/* Three-Pane Body */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left - Virtual Devices */}
        <div className="w-64 border-r flex-shrink-0 overflow-y-auto" style={{ background: '#12151C', borderColor: '#272E3B' }}>
          <div className="px-4 py-3 border-b text-[11px] uppercase tracking-wider font-medium" style={{ borderColor: '#272E3B', color: '#6B7A90' }}>
            Virtual Devices
          </div>
          {runResult?.virtual_devices?.map(dev => (
            <div key={dev.id} className="px-4 py-2.5 border-b" style={{ borderColor: '#272E3B20' }}>
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-medium" style={{ color: '#E8ECF1' }}>{dev.ref}</span>
                <span className="w-2 h-2 rounded-full pulse-online" style={{ background: dev.status === 'running' ? '#00D4AA' : '#6B7A90' }} />
              </div>
              <div className="text-[10px] font-mono mt-0.5" style={{ color: '#6B7A90' }}>{dev.protocol} | {dev.id.slice(0, 12)}</div>
            </div>
          )) || (
            <div className="p-4 text-xs text-center" style={{ color: '#6B7A90' }}>Run a scenario to see virtual devices</div>
          )}
        </div>

        {/* Center - Trace Stream */}
        <div className="flex-1 flex flex-col overflow-hidden" style={{ background: '#0A0C10' }}>
          <div className="px-4 py-3 border-b text-[11px] uppercase tracking-wider font-medium" style={{ borderColor: '#272E3B', color: '#6B7A90' }}>
            Trace Stream
          </div>
          <div className="flex-1 overflow-y-auto" data-testid="trace-stream">
            {runResult?.trace_events?.map((evt, i) => (
              <div key={evt.id} className="px-4 py-1.5 border-b text-xs font-mono flex items-center gap-3 hover:bg-white/[0.02]" style={{ borderColor: '#272E3B10' }}>
                <span style={{ color: '#6B7A90' }}>{new Date(evt.timestamp).toLocaleTimeString()}</span>
                <SeverityDot severity={evt.severity} />
                <span style={{ color: '#E8ECF1' }}>{evt.event_type}</span>
                <span className="ml-auto" style={{ color: '#6B7A90' }}>{evt.device_ref}</span>
              </div>
            )) || (
              <div className="flex items-center justify-center h-full text-xs" style={{ color: '#6B7A90' }}>
                <div className="text-center">
                  <Flask size={32} className="mx-auto mb-2" />
                  Run a scenario to see trace events
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right - Assertions */}
        <div className="w-80 border-l flex-shrink-0 overflow-y-auto" style={{ background: '#12151C', borderColor: '#272E3B' }}>
          <div className="px-4 py-3 border-b text-[11px] uppercase tracking-wider font-medium" style={{ borderColor: '#272E3B', color: '#6B7A90' }}>
            Assertions
          </div>
          {runResult?.assertions?.map(a => (
            <div key={a.id} className="px-4 py-3 border-b" style={{ borderColor: '#272E3B20' }}>
              <div className="flex items-start gap-2">
                {a.passed ? <Check size={16} className="flex-shrink-0 mt-0.5" style={{ color: '#00D4AA' }} /> : <X size={16} className="flex-shrink-0 mt-0.5" style={{ color: '#FF3B30' }} />}
                <div>
                  <div className="text-xs" style={{ color: '#E8ECF1' }}>{a.description}</div>
                  <div className="text-[10px] font-mono mt-0.5" style={{ color: '#6B7A90' }}>
                    Expected: {String(a.expected)} | Actual: {String(a.actual)}
                  </div>
                </div>
              </div>
            </div>
          )) || (
            <div className="p-4 text-xs text-center" style={{ color: '#6B7A90' }}>
              Run a scenario to see assertion results
            </div>
          )}

          {/* Past Runs */}
          {pastRuns.length > 0 && (
            <div className="mt-4">
              <div className="px-4 py-2 text-[11px] uppercase tracking-wider font-medium border-t" style={{ borderColor: '#272E3B', color: '#6B7A90' }}>
                Recent Runs
              </div>
              {pastRuns.map(r => (
                <div key={r.id} className="px-4 py-2 border-b text-xs" style={{ borderColor: '#272E3B20' }}>
                  <div className="flex items-center justify-between">
                    <span style={{ color: '#E8ECF1' }}>{r.scenario_name}</span>
                    <span className="font-mono" style={{ color: r.assertions_passed === r.assertions_total ? '#00D4AA' : '#FF3B30' }}>
                      {r.assertions_passed}/{r.assertions_total}
                    </span>
                  </div>
                  <div className="font-mono" style={{ color: '#6B7A90' }}>{new Date(r.started_at).toLocaleString()}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
