import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Cpu, Play, Check, X, Download, Funnel, Plus, FileZip, Package } from '@phosphor-icons/react';

const CAT_C = { 'SAS Serial': '#00B4D8', 'G2S SOAP': '#00D97E', 'Network': '#8B5CF6', 'Offline Buffer': '#FFB800', 'Integration': '#EC4899' };
const TYPE_C = { agent_image: '#00B4D8', firmware: '#00D97E', config: '#FFB800', provisioning: '#8B5CF6', script: '#EC4899' };
const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function HardwarePage() {
  const [tab, setTab] = useState('tests');
  const [tests, setTests] = useState([]);
  const [categories, setCategories] = useState([]);
  const [results, setResults] = useState([]);
  const [catFilter, setCatFilter] = useState('');
  const [running, setRunning] = useState(null);
  const [packages, setPackages] = useState([]);
  const [provForm, setProvForm] = useState({ agent_id: '', site_name: '', devices: '1,2,3' });

  useEffect(() => {
    api.get('/hardware/integration-tests').then(r => { setTests(r.data.tests || []); setCategories(r.data.categories || []); });
    api.get('/hardware/integration-tests/results?limit=20').then(r => setResults(r.data.results || []));
    api.get('/hardware/library').then(r => setPackages(r.data.packages || []));
  }, []);

  const runTest = async (testId) => {
    setRunning(testId);
    const { data } = await api.post('/hardware/integration-tests/run', { test_id: testId });
    setResults(prev => [data, ...prev].slice(0, 20));
    setRunning(null);
  };

  const generateProvisioning = () => {
    const params = new URLSearchParams({ agent_id: provForm.agent_id || `agent-${Date.now().toString(36)}`, site_name: provForm.site_name || 'New Site' });
    window.open(`${API_URL}/api/hardware/library/generate-provisioning`, '_blank');
  };

  const genProvisioningPost = async () => {
    await api.post('/hardware/library/generate-provisioning', { agent_id: provForm.agent_id || undefined, site_name: provForm.site_name, devices: provForm.devices.split(',').map(d => d.trim()).filter(Boolean) });
    api.get('/hardware/library').then(r => setPackages(r.data.packages || []));
  };

  const filtered = catFilter ? tests.filter(t => t.category === catFilter) : tests;

  return (
    <div data-testid="hardware-page" className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-2xl font-bold flex items-center gap-3" style={{ color: '#F0F4FF' }}>
          <Cpu size={24} style={{ color: '#EC4899' }} /> Hardware & Deployment
        </h1>
        <div className="flex gap-1">{['tests', 'library'].map(t => (
          <button key={t} data-testid={`hw-tab-${t}`} onClick={() => setTab(t)} className="px-4 py-2 rounded text-xs font-medium uppercase tracking-wider" style={{ background: tab === t ? 'rgba(236,72,153,0.15)' : 'transparent', color: tab === t ? '#EC4899' : '#4A6080' }}>{t === 'tests' ? 'Integration Tests' : 'Library'}</button>
        ))}</div>
      </div>

      {tab === 'tests' && (
        <div className="grid grid-cols-12 gap-4">
          {/* Test Suite */}
          <div className="col-span-7 space-y-3">
            <div className="flex items-center gap-2">
              <Funnel size={14} style={{ color: '#4A6080' }} />
              <select value={catFilter} onChange={e => setCatFilter(e.target.value)} className="px-3 py-1.5 rounded text-xs outline-none" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }}>
                <option value="">All Categories</option>
                {categories.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
              <span className="text-xs font-mono" style={{ color: '#4A6080' }}>{filtered.length} tests</span>
            </div>
            {filtered.map(t => {
              const lastResult = results.find(r => r.test_id === t.id);
              return (
                <div key={t.id} className="rounded-lg border p-4" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[10px] px-1.5 py-0.5 rounded font-bold" style={{ background: `${CAT_C[t.category] || '#4A6080'}15`, color: CAT_C[t.category] || '#4A6080' }}>{t.id}</span>
                      <span className="text-xs font-semibold" style={{ color: '#F0F4FF' }}>{t.name}</span>
                    </div>
                    <button data-testid={`run-test-${t.id}`} onClick={() => runTest(t.id)} disabled={running === t.id} className="flex items-center gap-1 px-3 py-1.5 rounded text-[10px] font-medium disabled:opacity-50" style={{ background: '#00D97E', color: '#070B14' }}>
                      {running === t.id ? '...' : <><Play size={12} /> Run</>}
                    </button>
                  </div>
                  <p className="text-xs mb-2" style={{ color: '#8BA3CC' }}>{t.description}</p>
                  <div className="flex items-center gap-3 text-[10px] font-mono" style={{ color: '#4A6080' }}>
                    <span>{t.duration_est}</span>
                    <span>Requires: {t.requires.join(', ') || 'none'}</span>
                    {lastResult && <span style={{ color: lastResult.status === 'PASSED' ? '#00D97E' : '#FF3B3B' }}>Last: {lastResult.status} ({lastResult.duration_ms}ms)</span>}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Results */}
          <div className="col-span-5 space-y-2">
            <div className="text-[10px] uppercase tracking-wider font-medium" style={{ color: '#4A6080' }}>Test Results ({results.length})</div>
            {results.map(r => (
              <div key={r.id} className="rounded border p-3" style={{ background: '#0C1322', borderColor: r.status === 'PASSED' ? '#00D97E20' : '#FF3B3B20' }}>
                <div className="flex items-center gap-2 mb-1">
                  {r.status === 'PASSED' ? <Check size={14} style={{ color: '#00D97E' }} /> : <X size={14} style={{ color: '#FF3B3B' }} />}
                  <span className="text-xs font-semibold" style={{ color: '#F0F4FF' }}>{r.test_name}</span>
                  <span className="ml-auto font-mono text-[10px]" style={{ color: '#4A6080' }}>{r.duration_ms}ms</span>
                </div>
                {r.metrics && <div className="flex flex-wrap gap-2 text-[9px] font-mono">{Object.entries(r.metrics).map(([k, v]) => <span key={k} style={{ color: '#4A6080' }}>{k}: <span style={{ color: '#F0F4FF' }}>{v}</span></span>)}</div>}
                {r.error && <div className="text-[10px] mt-1" style={{ color: '#FF3B3B' }}>{r.error}</div>}
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'library' && (
        <div className="space-y-4">
          {/* Provisioning Generator */}
          <div className="rounded-lg border p-4" style={{ background: '#0C1322', borderColor: '#8B5CF630' }}>
            <div className="text-[10px] uppercase tracking-wider mb-3 font-medium" style={{ color: '#8B5CF6' }}>Generate Provisioning Package</div>
            <div className="grid grid-cols-4 gap-3">
              <input value={provForm.agent_id} onChange={e => setProvForm(p => ({ ...p, agent_id: e.target.value }))} placeholder="Agent ID (auto)" className="px-3 py-2 rounded text-xs outline-none font-mono" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} />
              <input value={provForm.site_name} onChange={e => setProvForm(p => ({ ...p, site_name: e.target.value }))} placeholder="Site Name" className="px-3 py-2 rounded text-xs outline-none" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} />
              <input value={provForm.devices} onChange={e => setProvForm(p => ({ ...p, devices: e.target.value }))} placeholder="Device IDs (comma-sep)" className="px-3 py-2 rounded text-xs outline-none font-mono" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} />
              <button onClick={genProvisioningPost} className="flex items-center justify-center gap-2 py-2 rounded text-xs font-medium" style={{ background: '#8B5CF6', color: '#F0F4FF' }}><FileZip size={14} /> Generate ZIP</button>
            </div>
          </div>

          {/* Package Grid */}
          <div className="grid grid-cols-2 gap-3" data-testid="library-grid">
            {packages.map(p => (
              <div key={p.id} className="rounded-lg border p-4" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Package size={16} style={{ color: TYPE_C[p.type] || '#4A6080' }} />
                    <span className="text-xs font-semibold" style={{ color: '#F0F4FF' }}>{p.name}</span>
                  </div>
                  <span className="text-[9px] font-mono px-1.5 py-0.5 rounded" style={{ background: `${TYPE_C[p.type] || '#4A6080'}15`, color: TYPE_C[p.type] || '#4A6080' }}>{p.type}</span>
                </div>
                <p className="text-[10px] mb-2" style={{ color: '#8BA3CC' }}>{p.description}</p>
                <div className="flex items-center justify-between text-[9px] font-mono" style={{ color: '#4A6080' }}>
                  <span>v{p.version} | {p.target_hardware || 'Any'}</span>
                  <span><Download size={10} className="inline mr-0.5" />{p.download_count} downloads</span>
                </div>
                {p.tags?.length > 0 && <div className="flex flex-wrap gap-1 mt-2">{p.tags.map(t => <span key={t} className="text-[8px] px-1.5 py-0.5 rounded" style={{ background: '#111827', color: '#4A6080' }}>{t}</span>)}</div>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
