import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import { ShieldCheck, Play, CaretDown, CaretRight, Check, X, Clock, FileText, Download, Warning, Trophy, Certificate } from '@phosphor-icons/react';

const TIER_COLORS = { bronze: '#CD7F32', silver: '#C0C0C0', gold: '#FFD700', platinum: '#B9F2FF' };
const STATUS_C = { passed: '#00D97E', failed: '#FF3B3B', skipped: '#4A6080', running: '#00B4D8' };

function ProgressRing({ value, size = 100, strokeWidth = 8 }) {
  const r = (size - strokeWidth) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (value / 100) * circ;
  const color = value >= 95 ? '#00D97E' : value >= 80 ? '#FFB800' : '#FF3B3B';
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size}><circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#1A2540" strokeWidth={strokeWidth} />
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={strokeWidth} strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round" transform={`rotate(-90 ${size/2} ${size/2})`} style={{ transition: 'stroke-dashoffset 0.8s ease' }} /></svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-mono text-2xl font-black" style={{ color }}>{value}%</span>
        <span className="text-[8px] uppercase tracking-widest" style={{ color: '#4A6080' }}>pass rate</span>
      </div>
    </div>
  );
}

export default function CertificationPage() {
  const [classes, setClasses] = useState([]);
  const [tiers, setTiers] = useState({});
  const [devices, setDevices] = useState([]);
  const [runs, setRuns] = useState([]);
  const [selectedDevice, setSelectedDevice] = useState('');
  const [selectedTier, setSelectedTier] = useState('bronze');
  const [currentRun, setCurrentRun] = useState(null);
  const [running, setRunning] = useState(false);
  const [expandedClass, setExpandedClass] = useState(null);
  const [selectedRun, setSelectedRun] = useState(null);

  useEffect(() => {
    api.get('/certification/classes').then(r => setClasses(r.data.classes || []));
    api.get('/certification/tiers').then(r => setTiers(r.data.tiers || {}));
    api.get('/certification/runs?limit=10').then(r => setRuns(r.data.runs || []));
    api.get('/devices?limit=20').then(r => setDevices(r.data.devices || []));
  }, []);

  const runCertification = async () => {
    setRunning(true);
    setCurrentRun(null);
    try {
      const { data } = await api.post('/certification/run', { device_id: selectedDevice || devices[0]?.id, tier: selectedTier });
      setCurrentRun(data);
      setRuns(prev => [{ ...data, class_results: undefined }, ...prev]);
    } catch (err) { console.error(err); }
    setRunning(false);
  };

  const loadRun = async (runId) => {
    const { data } = await api.get(`/certification/runs/${runId}`);
    setCurrentRun(data);
    setSelectedRun(runId);
  };

  const tierConfig = tiers[selectedTier] || {};
  const tierClasses = tierConfig.classes || [];

  return (
    <div data-testid="certification-suite" className="flex gap-0 h-full -m-6">
      {/* Left — Config + Past Runs */}
      <div className="w-72 border-r flex flex-col flex-shrink-0 overflow-hidden" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
        <div className="px-4 py-3 border-b" style={{ borderColor: '#1A2540' }}>
          <h2 className="font-heading text-sm font-semibold flex items-center gap-2" style={{ color: '#F0F4FF' }}>
            <ShieldCheck size={16} style={{ color: '#00B4D8' }} /> Certification Suite
          </h2>
        </div>
        {/* Config */}
        <div className="p-4 space-y-3 border-b" style={{ borderColor: '#1A2540' }}>
          <div>
            <label className="block text-[10px] uppercase tracking-wider mb-1" style={{ color: '#4A6080' }}>Target Device</label>
            <select data-testid="cert-device-select" value={selectedDevice} onChange={e => setSelectedDevice(e.target.value)}
              className="w-full px-3 py-2 rounded text-xs outline-none" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }}>
              <option value="">Auto-select first device</option>
              {devices.map(d => <option key={d.id} value={d.id}>{d.external_ref} — {d.manufacturer} {d.model}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-[10px] uppercase tracking-wider mb-1.5" style={{ color: '#4A6080' }}>Certification Tier</label>
            <div className="space-y-1.5">
              {Object.entries(tiers).map(([key, tier]) => (
                <button key={key} data-testid={`tier-${key}`} onClick={() => setSelectedTier(key)}
                  className="w-full flex items-center gap-2 px-3 py-2 rounded text-xs transition-colors text-left"
                  style={{ background: selectedTier === key ? `${TIER_COLORS[key]}15` : '#111827', border: `1px solid ${selectedTier === key ? TIER_COLORS[key] + '40' : '#1A2540'}`, color: '#F0F4FF' }}>
                  <Trophy size={14} weight="fill" style={{ color: TIER_COLORS[key] }} />
                  <div className="flex-1">
                    <div className="font-semibold">{tier.label}</div>
                    <div className="text-[9px] font-mono" style={{ color: '#4A6080' }}>{tier.class_count} classes | {tier.total_tests} tests | {tier.min_pass_rate}% min</div>
                  </div>
                </button>
              ))}
            </div>
          </div>
          <button data-testid="run-certification-btn" onClick={runCertification} disabled={running}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded text-sm font-semibold disabled:opacity-50 transition-colors"
            style={{ background: running ? '#1A2540' : '#00D97E', color: '#070B14' }}>
            {running ? <Clock size={16} className="animate-spin" /> : <Play size={16} weight="fill" />}
            {running ? 'Running Tests...' : 'Run All Tests'}
          </button>
        </div>
        {/* Past Runs */}
        <div className="flex-1 overflow-y-auto">
          <div className="px-4 py-2 text-[10px] uppercase tracking-wider font-medium" style={{ color: '#4A6080' }}>Past Runs</div>
          {runs.map(r => (
            <button key={r.id} data-testid={`past-run-${r.id}`} onClick={() => loadRun(r.id)}
              className="w-full text-left px-4 py-2.5 border-b transition-colors" style={{ borderColor: '#1A254020', background: selectedRun === r.id ? 'rgba(0,180,216,0.06)' : 'transparent' }}>
              <div className="flex items-center gap-2">
                <Trophy size={12} weight="fill" style={{ color: TIER_COLORS[r.tier] || '#4A6080' }} />
                <span className="text-xs font-medium" style={{ color: '#F0F4FF' }}>{r.tier_label}</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded" style={{ background: r.status === 'PASSED' ? 'rgba(0,217,126,0.1)' : 'rgba(255,59,59,0.1)', color: r.status === 'PASSED' ? '#00D97E' : '#FF3B3B' }}>{r.status}</span>
              </div>
              <div className="text-[10px] font-mono mt-0.5" style={{ color: '#4A6080' }}>
                {r.device_ref || 'Unknown'} | {r.pass_rate}% | {new Date(r.started_at).toLocaleDateString()}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Center — Test Results */}
      <div className="flex-1 flex flex-col overflow-hidden" style={{ background: '#070B14' }}>
        {!currentRun ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <ShieldCheck size={56} className="mx-auto mb-4" style={{ color: '#1A2540' }} />
              <h3 className="font-heading text-lg font-semibold" style={{ color: '#F0F4FF' }}>G2S Certification Test Suite</h3>
              <p className="text-xs mt-2 max-w-md" style={{ color: '#4A6080' }}>
                Select a device and tier, then click "Run All Tests" to execute the 14-class automated compliance test suite.
              </p>
            </div>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto p-6 space-y-4" data-testid="cert-results">
            {/* Header with Progress Ring */}
            <div className="flex items-center gap-6">
              <ProgressRing value={currentRun.pass_rate} size={110} />
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <Trophy size={20} weight="fill" style={{ color: TIER_COLORS[currentRun.tier] }} />
                  <span className="font-heading text-xl font-bold" style={{ color: '#F0F4FF' }}>{currentRun.tier_label} Certification</span>
                  <span className="text-sm font-mono px-2 py-0.5 rounded" style={{ background: currentRun.status === 'PASSED' ? 'rgba(0,217,126,0.1)' : 'rgba(255,59,59,0.1)', color: currentRun.status === 'PASSED' ? '#00D97E' : '#FF3B3B' }}>
                    {currentRun.status}
                  </span>
                </div>
                <div className="text-xs" style={{ color: '#8BA3CC' }}>
                  {currentRun.device_ref || currentRun.device_id} — {currentRun.manufacturer} {currentRun.model}
                </div>
                <div className="flex items-center gap-4 mt-2 text-[10px] font-mono" style={{ color: '#4A6080' }}>
                  <span style={{ color: '#00D97E' }}>{currentRun.total_passed} passed</span>
                  <span style={{ color: '#FF3B3B' }}>{currentRun.total_failed} failed</span>
                  <span>{currentRun.total_skipped} skipped</span>
                  <span>Min: {currentRun.min_pass_rate}%</span>
                </div>
              </div>
              {currentRun.status === 'PASSED' && currentRun.certificate_id && (
                <div className="ml-auto flex gap-2">
                  <button data-testid="export-cert-btn" className="flex items-center gap-2 px-4 py-2 rounded text-xs font-medium" style={{ background: 'rgba(0,180,216,0.1)', color: '#00B4D8', border: '1px solid rgba(0,180,216,0.2)' }}>
                    <Certificate size={14} /> View Certificate
                  </button>
                  <button className="flex items-center gap-2 px-4 py-2 rounded text-xs font-medium" style={{ background: 'rgba(0,217,126,0.1)', color: '#00D97E', border: '1px solid rgba(0,217,126,0.2)' }}>
                    <Download size={14} /> Export PDF
                  </button>
                </div>
              )}
            </div>

            {/* Class Accordion */}
            <div className="space-y-1" data-testid="class-accordion">
              {currentRun.class_results?.map(cls => {
                const isExpanded = expandedClass === cls.class_id;
                const clsTests = currentRun._allTests?.[cls.class_id]; // We'll need to track per test
                return (
                  <div key={cls.class_id} className="rounded overflow-hidden" style={{ border: '1px solid #1A2540' }}>
                    <button data-testid={`class-row-${cls.class_id}`}
                      onClick={() => setExpandedClass(isExpanded ? null : cls.class_id)}
                      className="w-full flex items-center gap-3 px-4 py-3 text-left transition-colors"
                      style={{ background: isExpanded ? '#111827' : '#0C1322' }}>
                      {isExpanded ? <CaretDown size={14} style={{ color: '#4A6080' }} /> : <CaretRight size={14} style={{ color: '#4A6080' }} />}
                      <span className="w-3 h-3 rounded-full" style={{ background: STATUS_C[cls.status] }} />
                      <span className="text-xs font-semibold flex-1" style={{ color: cls.included ? '#F0F4FF' : '#4A6080' }}>{cls.class_name}</span>
                      <span className="font-mono text-[10px]" style={{ color: '#4A6080' }}>{cls.test_count} tests</span>
                      {cls.included && (
                        <>
                          <span className="font-mono text-[10px]" style={{ color: '#00D97E' }}>{cls.passed} pass</span>
                          {cls.failed > 0 && <span className="font-mono text-[10px]" style={{ color: '#FF3B3B' }}>{cls.failed} fail</span>}
                        </>
                      )}
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded capitalize" style={{ background: `${STATUS_C[cls.status]}15`, color: STATUS_C[cls.status] }}>
                        {cls.status}
                      </span>
                    </button>
                    {isExpanded && cls.included && (
                      <div className="border-t" style={{ borderColor: '#1A2540', background: '#070B14' }}>
                        {Array.from({ length: cls.test_count }).map((_, i) => {
                          const passed = i < cls.passed;
                          const status = passed ? 'passed' : (i < cls.passed + cls.failed ? 'failed' : 'skipped');
                          return (
                            <div key={i} className="flex items-center gap-3 px-6 py-2 border-b text-xs" style={{ borderColor: '#1A254020' }}>
                              {status === 'passed' ? <Check size={14} style={{ color: '#00D97E' }} /> : status === 'failed' ? <X size={14} style={{ color: '#FF3B3B' }} /> : <span className="w-3.5" />}
                              <span className="font-mono" style={{ color: status === 'passed' ? '#8BA3CC' : status === 'failed' ? '#FF3B3B' : '#4A6080' }}>
                                {cls.class_name} Test {i + 1}
                              </span>
                              <span className="ml-auto text-[10px] font-mono" style={{ color: '#4A6080' }}>
                                {status === 'failed' && `Expected valid ${cls.class_id}Status response`}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
