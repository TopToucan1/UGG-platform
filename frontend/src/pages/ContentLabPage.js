import { useState, useEffect, useCallback, useRef } from 'react';
import api from '@/lib/api';
import {
  FileCode, Upload, MagnifyingGlass, Cube, Tag, CheckCircle,
  Warning, ArrowRight, Sparkle, Database, Clock, RocketLaunch,
  FileMagnifyingGlass, HexagonIcon as HexIcon, Rows
} from '@phosphor-icons/react';
import InfoTip from '@/components/InfoTip';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const CAT_COLORS = { slot: '#00D4AA', bonus: '#F5A623', player_tracking: '#007AFF', financial: '#FF3B30', system: '#8B5CF6' };
const CONF_COLOR = (c) => c >= 0.8 ? '#00D4AA' : c >= 0.6 ? '#F5A623' : '#FF3B30';

export default function ContentLabPage() {
  const [activeTab, setActiveTab] = useState('analyzer');
  // Analyzer state
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [hexData, setHexData] = useState(null);
  const [hexOffset, setHexOffset] = useState(0);
  const fileInputRef = useRef(null);
  const hexFileRef = useRef(null);
  const [lastFile, setLastFile] = useState(null);
  // Registry state
  const [content, setContent] = useState([]);
  const [contentTotal, setContentTotal] = useState(0);
  const [contentStats, setContentStats] = useState(null);
  const [analyses, setAnalyses] = useState([]);
  const [selectedContent, setSelectedContent] = useState(null);
  // Register form
  const [showRegister, setShowRegister] = useState(false);
  const [regForm, setRegForm] = useState({ name: '', content_type: 'swf', version: '1.0.0', game_title: '', manufacturer: '' });

  const fetchRegistry = useCallback(async () => {
    const [cRes, sRes, aRes] = await Promise.all([
      api.get('/content-registry?limit=50'),
      api.get('/content-registry/stats'),
      api.get('/swf-analyzer/analyses?limit=20'),
    ]);
    setContent(cRes.data.content || []);
    setContentTotal(cRes.data.total || 0);
    setContentStats(sRes.data);
    setAnalyses(aRes.data.analyses || []);
  }, []);

  useEffect(() => { fetchRegistry(); }, [fetchRegistry]);

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setAnalyzing(true);
    setAnalysis(null);
    setHexData(null);
    setLastFile(file);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await api.post('/swf-analyzer/analyze', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      setAnalysis(data);
      fetchRegistry();
    } catch (err) {
      setAnalysis({ error: err.response?.data?.detail || err.message });
    }
    setAnalyzing(false);
  };

  const handleHexUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLastFile(file);
    loadHex(file, 0);
  };

  const loadHex = async (file, offset) => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post(`/swf-analyzer/hex-dump?offset=${offset}&length=512`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
    setHexData(data);
    setHexOffset(offset);
  };

  const registerFromAnalysis = async () => {
    if (!analysis || analysis.error) return;
    try {
      await api.post('/content-registry/register', {
        name: analysis.filename,
        content_type: 'swf',
        version: `SWF v${analysis.swf_version}`,
        game_title: regForm.game_title || analysis.filename,
        manufacturer: regForm.manufacturer,
        file_size: analysis.file_size,
        checksum: '',
        swf_version: analysis.swf_version,
        analysis_id: analysis.id,
        identifiers_count: analysis.identifiers_count,
        categories: Object.keys(analysis.categories || {}),
      });
      fetchRegistry();
      setShowRegister(false);
    } catch (err) { console.error(err); }
  };

  const registerManual = async () => {
    await api.post('/content-registry/register', regForm);
    fetchRegistry();
    setShowRegister(false);
    setRegForm({ name: '', content_type: 'swf', version: '1.0.0', game_title: '', manufacturer: '' });
  };

  const tabs = [
    { id: 'analyzer', label: 'SWF Analyzer', icon: FileMagnifyingGlass, tip: 'Upload a SWF (Flash) game file and the analyzer will decompress it, extract strings and identifiers, and suggest canonical event mappings.' },
    { id: 'hex', label: 'Binary Inspector', icon: Cube, tip: 'Raw hex/ASCII viewer for any binary file — useful for protocol dumps, firmware images, or verifying a file header.' },
    { id: 'registry', label: 'Content Registry', icon: Database, tip: 'The master list of all content packages (games, firmware, config) known to the platform, along with which devices each is deployed to.' },
  ];

  return (
    <div data-testid="content-lab" className="flex gap-0 h-full -m-6">
      {/* Left — Mode + History */}
      <div className="w-60 border-r flex flex-col flex-shrink-0 overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }}>
        <div className="px-4 py-3 border-b" style={{ borderColor: '#272E3B' }}>
          <h2 className="font-heading text-sm font-semibold flex items-center gap-2" style={{ color: '#E8ECF1' }}>
            <Cube size={16} style={{ color: '#00D4AA' }} /> EGM Content Lab
            <InfoTip label="EGM Content Lab" description="Tools for inspecting and registering game content (SWF files, binaries, firmware) that runs on EGMs. Lets you see what's inside a game package and track which versions are deployed where." />
          </h2>
        </div>
        <div className="p-2 space-y-0.5">
          {tabs.map(t => (
            <div key={t.id} className="flex items-center">
              <button data-testid={`lab-tab-${t.id}`} onClick={() => setActiveTab(t.id)}
                className="flex-1 flex items-center gap-2 px-3 py-2.5 rounded text-xs transition-colors"
                style={{ background: activeTab === t.id ? 'rgba(0,212,170,0.1)' : 'transparent', color: activeTab === t.id ? '#00D4AA' : '#A3AEBE' }}>
                <t.icon size={16} /> {t.label}
              </button>
              <InfoTip label={t.label} description={t.tip} />
            </div>
          ))}
        </div>

        {/* Stats */}
        {contentStats && (
          <div className="px-4 py-3 border-t space-y-2" style={{ borderColor: '#272E3B' }}>
            <div className="text-[10px] uppercase tracking-wider font-medium flex items-center" style={{ color: '#6B7A90' }}>Registry Stats<InfoTip description="At-a-glance totals for the content registry: how many packages are tracked, how many have been analyzed, and a breakdown by content type." /></div>
            <div className="flex justify-between text-xs"><span className="flex items-center" style={{ color: '#6B7A90' }}>Content Packages<InfoTip description="Total count of registered content packages across all types (SWF, HTML5, firmware, config)." /></span><span className="font-mono" style={{ color: '#E8ECF1' }}>{contentStats.total_content}</span></div>
            <div className="flex justify-between text-xs"><span className="flex items-center" style={{ color: '#6B7A90' }}>Analyses Run<InfoTip description="How many times the SWF analyzer has been run — each unique upload counts as one analysis." /></span><span className="font-mono" style={{ color: '#00D4AA' }}>{contentStats.total_analyses}</span></div>
            {Object.entries(contentStats.by_type || {}).map(([k, v]) => (
              <div key={k} className="flex justify-between text-xs"><span style={{ color: '#6B7A90' }}>{k.toUpperCase()}</span><span className="font-mono" style={{ color: '#E8ECF1' }}>{v}</span></div>
            ))}
          </div>
        )}

        {/* Recent Analyses */}
        <div className="flex-1 overflow-y-auto border-t" style={{ borderColor: '#272E3B' }}>
          <div className="px-4 py-2 text-[10px] uppercase tracking-wider font-medium flex items-center" style={{ color: '#6B7A90' }}>Recent Analyses<InfoTip description="The last files you analyzed. Each entry shows the filename, SWF version, number of string identifiers extracted, and size in bytes." /></div>
          {analyses.map(a => (
            <div key={a.id} className="px-4 py-2 border-b text-xs" style={{ borderColor: '#272E3B10' }}>
              <div className="font-medium truncate" style={{ color: '#E8ECF1' }}>{a.filename}</div>
              <div className="font-mono text-[10px]" style={{ color: '#6B7A90' }}>SWF v{a.swf_version} | {a.identifiers_count} idents | {a.file_size}B</div>
            </div>
          ))}
        </div>
      </div>

      {/* Center — Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden" style={{ background: '#0A0C10' }}>
        {/* === SWF ANALYZER === */}
        {activeTab === 'analyzer' && (
          <div className="flex-1 overflow-y-auto p-6 space-y-4" data-testid="swf-analyzer-panel">
            {/* Upload Area */}
            <div className="rounded border border-dashed p-8 text-center cursor-pointer transition-colors hover:border-[#00D4AA]"
              style={{ borderColor: '#272E3B', background: '#12151C' }}
              onClick={() => fileInputRef.current?.click()}>
              <input ref={fileInputRef} type="file" accept=".swf,.crdownload" className="hidden" onChange={handleFileUpload} data-testid="swf-file-input" />
              <Upload size={32} className="mx-auto mb-3" style={{ color: analyzing ? '#F5A623' : '#00D4AA' }} />
              <div className="text-sm font-medium" style={{ color: '#E8ECF1' }}>
                {analyzing ? 'Analyzing SWF file...' : 'Drop or click to upload SWF file'}
              </div>
              <div className="text-xs mt-1" style={{ color: '#6B7A90' }}>Supports .swf and .crdownload files from EGM systems</div>
            </div>

            {/* Analysis Results */}
            {analysis && !analysis.error && (
              <div className="space-y-4">
                {/* Header */}
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-heading text-lg font-semibold" style={{ color: '#E8ECF1' }}>{analysis.filename}</h3>
                    <div className="text-xs font-mono mt-0.5" style={{ color: '#6B7A90' }}>
                      SWF v{analysis.swf_version} | {analysis.compressed ? 'Compressed' : 'Raw'} | {analysis.file_size?.toLocaleString()} bytes → {analysis.uncompressed_size?.toLocaleString()} bytes | {analysis.total_strings} strings
                    </div>
                  </div>
                  <div className="flex items-center">
                    <button data-testid="register-from-analysis-btn" onClick={() => setShowRegister(true)}
                      className="flex items-center gap-2 px-4 py-2 rounded text-xs font-medium" style={{ background: '#00D4AA', color: '#0A0C10' }}>
                      <Database size={14} /> Register to Content Registry
                    </button>
                    <InfoTip label="Register to Registry" description="Save this analyzed SWF as a content package in the registry so it can be tracked across devices and deployments." />
                  </div>
                </div>

                {/* Categories */}
                <div className="flex flex-wrap gap-2">
                  {Object.keys(analysis.categories || {}).map(cat => (
                    <span key={cat} className="text-[10px] font-mono px-2 py-1 rounded flex items-center gap-1"
                      style={{ background: `${CAT_COLORS[cat] || '#6B7A90'}15`, color: CAT_COLORS[cat] || '#6B7A90', border: `1px solid ${CAT_COLORS[cat] || '#6B7A90'}30` }}>
                      <Tag size={10} /> {cat}
                    </span>
                  ))}
                </div>

                {/* Suggested Mappings (the key feature) */}
                {analysis.suggested_mappings?.length > 0 && (
                  <div className="rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
                    <div className="flex items-center gap-2 mb-3">
                      <Sparkle size={16} style={{ color: '#00D4AA' }} />
                      <span className="text-[11px] uppercase tracking-wider font-medium flex items-center" style={{ color: '#6B7A90' }}>Auto-Suggested Event Mappings ({analysis.suggested_mappings.length})<InfoTip description="The analyzer looked at strings inside the SWF and proposed which source symbols should map to which canonical events/fields. Confidence is how sure it is — anything under 80% should be reviewed." /></span>
                    </div>
                    <div className="space-y-1.5">
                      {analysis.suggested_mappings.map((m, i) => (
                        <div key={i} className="flex items-center gap-3 px-3 py-2 rounded" style={{ background: '#1A1E2A' }}>
                          <span className="font-mono text-xs min-w-[140px]" style={{ color: '#E8ECF1' }}>{m.source}</span>
                          <ArrowRight size={12} style={{ color: '#00D4AA' }} />
                          <span className="font-mono text-xs" style={{ color: '#00D4AA' }}>{m.canonical_event}</span>
                          <span className="font-mono text-[10px]" style={{ color: '#6B7A90' }}>{m.canonical_field}</span>
                          <span className="ml-auto font-mono text-[10px] px-1.5 py-0.5 rounded" style={{ background: `${CONF_COLOR(m.confidence)}15`, color: CONF_COLOR(m.confidence) }}>
                            {Math.round(m.confidence * 100)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Copyrights & Fonts */}
                <div className="grid grid-cols-2 gap-4">
                  {analysis.copyrights?.length > 0 && (
                    <div className="rounded border p-3" style={{ background: '#12151C', borderColor: '#272E3B' }}>
                      <div className="text-[10px] uppercase tracking-wider mb-2 font-medium" style={{ color: '#6B7A90' }}>Copyright / Attribution</div>
                      {analysis.copyrights.map((c, i) => <div key={i} className="text-xs" style={{ color: '#A3AEBE' }}>{c}</div>)}
                    </div>
                  )}
                  {analysis.fonts?.length > 0 && (
                    <div className="rounded border p-3" style={{ background: '#12151C', borderColor: '#272E3B' }}>
                      <div className="text-[10px] uppercase tracking-wider mb-2 font-medium" style={{ color: '#6B7A90' }}>Embedded Fonts</div>
                      <div className="flex flex-wrap gap-1">{analysis.fonts.map((f, i) => <span key={i} className="text-[10px] font-mono px-1.5 py-0.5 rounded" style={{ background: '#1A1E2A', color: '#A3AEBE' }}>{f}</span>)}</div>
                    </div>
                  )}
                </div>

                {/* ActionScript Patterns */}
                {analysis.actionscript_patterns?.length > 0 && (
                  <div className="rounded border p-3" style={{ background: '#12151C', borderColor: '#272E3B' }}>
                    <div className="text-[10px] uppercase tracking-wider mb-2 font-medium" style={{ color: '#6B7A90' }}>ActionScript Patterns</div>
                    <div className="flex flex-wrap gap-1.5">
                      {analysis.actionscript_patterns.map((p, i) => (
                        <span key={i} className="font-mono text-[10px] px-2 py-1 rounded" style={{ background: '#1A1E2A', color: '#F5A623', border: '1px solid #272E3B' }}>{p}</span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Category Details */}
                {Object.entries(analysis.categories || {}).map(([cat, strings]) => (
                  <div key={cat} className="rounded border p-3" style={{ background: '#12151C', borderColor: '#272E3B' }}>
                    <div className="text-[10px] uppercase tracking-wider mb-2 font-medium" style={{ color: CAT_COLORS[cat] || '#6B7A90' }}>{cat} identifiers</div>
                    <div className="flex flex-wrap gap-1">
                      {strings.map((s, i) => <span key={i} className="font-mono text-[10px] px-1.5 py-0.5 rounded" style={{ background: '#1A1E2A', color: '#A3AEBE' }}>{s}</span>)}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {analysis?.error && (
              <div className="rounded border p-4" style={{ background: 'rgba(255,59,48,0.05)', borderColor: 'rgba(255,59,48,0.2)' }}>
                <div className="flex items-center gap-2 text-sm" style={{ color: '#FF3B30' }}><Warning size={16} /> {analysis.error}</div>
              </div>
            )}
          </div>
        )}

        {/* === BINARY INSPECTOR === */}
        {activeTab === 'hex' && (
          <div className="flex-1 overflow-y-auto p-6 space-y-4" data-testid="binary-inspector-panel">
            <div className="rounded border border-dashed p-6 text-center cursor-pointer transition-colors hover:border-[#00D4AA]"
              style={{ borderColor: '#272E3B', background: '#12151C' }}
              onClick={() => hexFileRef.current?.click()}>
              <input ref={hexFileRef} type="file" className="hidden" onChange={handleHexUpload} data-testid="hex-file-input" />
              <Cube size={28} className="mx-auto mb-2" style={{ color: '#007AFF' }} />
              <div className="text-sm font-medium" style={{ color: '#E8ECF1' }}>Upload any binary file for hex inspection</div>
              <div className="text-xs mt-1" style={{ color: '#6B7A90' }}>SWF, protocol dumps, raw frames, firmware images</div>
            </div>

            {hexData && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono" style={{ color: '#6B7A90' }}>Total: {hexData.total_size?.toLocaleString()} bytes | Showing offset 0x{hexOffset.toString(16).padStart(8, '0')}</span>
                  <div className="flex gap-2">
                    <button disabled={hexOffset === 0} onClick={() => lastFile && loadHex(lastFile, Math.max(0, hexOffset - 512))}
                      className="px-3 py-1 rounded text-xs font-mono disabled:opacity-30" style={{ background: '#1A1E2A', color: '#E8ECF1', border: '1px solid #272E3B' }}>Prev</button>
                    <button disabled={hexOffset + 512 >= (hexData.total_size || 0)} onClick={() => lastFile && loadHex(lastFile, hexOffset + 512)}
                      className="px-3 py-1 rounded text-xs font-mono disabled:opacity-30" style={{ background: '#1A1E2A', color: '#E8ECF1', border: '1px solid #272E3B' }}>Next</button>
                  </div>
                </div>
                <div className="rounded border overflow-hidden font-mono text-[11px]" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="hex-view">
                  <div className="grid gap-0" style={{ gridTemplateColumns: '80px 1fr 1fr' }}>
                    <div className="px-3 py-1 border-b" style={{ background: '#1A1E2A', borderColor: '#272E3B', color: '#6B7A90' }}>Offset</div>
                    <div className="px-3 py-1 border-b" style={{ background: '#1A1E2A', borderColor: '#272E3B', color: '#6B7A90' }}>Hex</div>
                    <div className="px-3 py-1 border-b" style={{ background: '#1A1E2A', borderColor: '#272E3B', color: '#6B7A90' }}>ASCII</div>
                    {hexData.hex_dump?.map((row, i) => (
                      <div key={i} className="contents">
                        <div className="px-3 py-0.5 border-b" style={{ borderColor: '#272E3B10', color: '#6B7A90' }}>{row.offset}</div>
                        <div className="px-3 py-0.5 border-b" style={{ borderColor: '#272E3B10', color: '#00D4AA' }}>{row.hex}</div>
                        <div className="px-3 py-0.5 border-b" style={{ borderColor: '#272E3B10', color: '#F5A623' }}>{row.ascii}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* === CONTENT REGISTRY === */}
        {activeTab === 'registry' && (
          <div className="flex-1 overflow-y-auto p-6 space-y-4" data-testid="content-registry-panel">
            <div className="flex items-center justify-between">
              <h3 className="font-heading text-lg font-semibold flex items-center" style={{ color: '#E8ECF1' }}>EGM Content Registry<InfoTip label="EGM Content Registry" description="Master list of every content package known to the platform — games, firmware, config bundles. Tracks version, manufacturer, deployment status, and which devices run it." /></h3>
              <div className="flex gap-2 items-center">
                <span className="text-xs font-mono" style={{ color: '#6B7A90' }}>{contentTotal} packages</span>
                <button data-testid="register-content-btn" onClick={() => setShowRegister(true)} className="flex items-center gap-1 px-3 py-1.5 rounded text-xs font-medium" style={{ background: '#00D4AA', color: '#0A0C10' }}>
                  <Database size={14} /> Register Content
                </button>
                <InfoTip label="Register Content" description="Manually add a new content package to the registry (e.g. when you don't have the file to analyze but need to track it)." />
              </div>
            </div>

            {showRegister && (
              <div className="rounded border p-4 space-y-3" style={{ background: '#12151C', borderColor: '#00D4AA40' }}>
                <h4 className="text-sm font-semibold" style={{ color: '#E8ECF1' }}>Register Content Package</h4>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block text-[10px] uppercase tracking-wider mb-1 flex items-center" style={{ color: '#6B7A90' }}>Name<InfoTip description="Friendly name shown in the registry list. Usually 'Game Title vX.Y' format." /></label>
                    <input value={regForm.name} onChange={e => setRegForm(p => ({ ...p, name: e.target.value }))} className="w-full px-3 py-2 rounded text-xs outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }} placeholder="Buffalo Gold v2.1" />
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase tracking-wider mb-1 flex items-center" style={{ color: '#6B7A90' }}>Game Title<InfoTip description="The public name of the game (e.g. 'Buffalo Gold'). Multiple content versions can share one title." /></label>
                    <input value={regForm.game_title} onChange={e => setRegForm(p => ({ ...p, game_title: e.target.value }))} className="w-full px-3 py-2 rounded text-xs outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }} placeholder="Buffalo Gold" />
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase tracking-wider mb-1 flex items-center" style={{ color: '#6B7A90' }}>Manufacturer<InfoTip description="Game maker (Aristocrat, IGT, Scientific Games, Konami, etc.)." /></label>
                    <input value={regForm.manufacturer} onChange={e => setRegForm(p => ({ ...p, manufacturer: e.target.value }))} className="w-full px-3 py-2 rounded text-xs outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }} placeholder="Aristocrat" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] uppercase tracking-wider mb-1 flex items-center" style={{ color: '#6B7A90' }}>Content Type<InfoTip description="Format of the package. SWF = legacy Flash game binary. HTML5 = modern web-based game. Firmware = EGM system software. Config = device configuration bundle." /></label>
                    <select value={regForm.content_type} onChange={e => setRegForm(p => ({ ...p, content_type: e.target.value }))} className="w-full px-3 py-2 rounded text-xs outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}>
                      <option value="swf">SWF (Flash)</option><option value="html5">HTML5</option><option value="firmware">Firmware</option><option value="config">Configuration</option><option value="other">Other</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase tracking-wider mb-1 flex items-center" style={{ color: '#6B7A90' }}>Version<InfoTip description="Build number / release string from the vendor. Used to differentiate builds of the same game." /></label>
                    <input value={regForm.version} onChange={e => setRegForm(p => ({ ...p, version: e.target.value }))} className="w-full px-3 py-2 rounded text-xs outline-none font-mono" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }} />
                  </div>
                </div>
                <div className="flex gap-2">
                  {analysis && !analysis.error ? (
                    <button onClick={registerFromAnalysis} className="px-4 py-2 rounded text-xs font-medium" style={{ background: '#00D4AA', color: '#0A0C10' }}>Register from Analysis</button>
                  ) : (
                    <button onClick={registerManual} className="px-4 py-2 rounded text-xs font-medium" style={{ background: '#00D4AA', color: '#0A0C10' }}>Register</button>
                  )}
                  <button onClick={() => setShowRegister(false)} className="px-4 py-2 rounded text-xs" style={{ color: '#6B7A90' }}>Cancel</button>
                </div>
              </div>
            )}

            {/* Content List */}
            <div className="rounded border overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }}>
              <div className="grid grid-cols-12 gap-2 px-4 py-2 text-[10px] uppercase tracking-wider font-medium border-b" style={{ color: '#6B7A90', borderColor: '#272E3B' }}>
                <div className="col-span-3 flex items-center">Name<InfoTip description="Friendly name of the package." /></div><div className="col-span-2 flex items-center">Game<InfoTip description="Game title this package belongs to." /></div><div className="col-span-2 flex items-center">Manufacturer<InfoTip description="Vendor who produced the content." /></div>
                <div className="col-span-1 flex items-center">Type<InfoTip description="Format (SWF, HTML5, firmware, config)." /></div><div className="col-span-1 flex items-center">Version<InfoTip description="Vendor version string." /></div><div className="col-span-1 flex items-center">Status<InfoTip description="'deployed' means at least one device is running this package. 'pending' means registered but not rolled out yet." /></div><div className="col-span-2 flex items-center">Registered<InfoTip description="When this package was added to the registry." /></div>
              </div>
              <div className="max-h-96 overflow-y-auto">
                {content.map(c => (
                  <button key={c.id} data-testid={`content-row-${c.id}`} onClick={() => setSelectedContent(c)}
                    className="w-full grid grid-cols-12 gap-2 px-4 py-2.5 border-b text-xs text-left hover:bg-white/[0.02] transition-colors" style={{ borderColor: '#272E3B10' }}>
                    <div className="col-span-3 font-medium truncate" style={{ color: '#E8ECF1' }}>{c.name}</div>
                    <div className="col-span-2 truncate" style={{ color: '#A3AEBE' }}>{c.game_title}</div>
                    <div className="col-span-2" style={{ color: '#A3AEBE' }}>{c.manufacturer}</div>
                    <div className="col-span-1 font-mono uppercase text-[10px]" style={{ color: '#6B7A90' }}>{c.content_type}</div>
                    <div className="col-span-1 font-mono" style={{ color: '#6B7A90' }}>{c.version}</div>
                    <div className="col-span-1"><span className="text-[10px] font-mono px-1.5 py-0.5 rounded capitalize" style={{ background: c.status === 'deployed' ? 'rgba(0,212,170,0.1)' : 'rgba(245,166,35,0.1)', color: c.status === 'deployed' ? '#00D4AA' : '#F5A623' }}>{c.status}</span></div>
                    <div className="col-span-2 font-mono text-[10px]" style={{ color: '#6B7A90' }}>{new Date(c.registered_at).toLocaleString()}</div>
                  </button>
                ))}
                {content.length === 0 && (
                  <div className="p-8 text-center text-xs" style={{ color: '#6B7A90' }}>
                    <Database size={32} className="mx-auto mb-2" style={{ color: '#272E3B' }} />
                    No content registered yet — analyze an SWF file and register it
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Right — Detail Panel */}
      <div className="w-72 border-l flex flex-col flex-shrink-0 overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }}>
        <div className="px-4 py-3 border-b" style={{ borderColor: '#272E3B' }}>
          <h2 className="font-heading text-sm font-semibold flex items-center" style={{ color: '#E8ECF1' }}>Details<InfoTip label="Details" description="Breakdown of the currently-selected analysis or content package — file info, version, content categories, and deployment stats." /></h2>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {analysis && !analysis.error && activeTab === 'analyzer' ? (
            <>
              <div className="rounded border p-3 text-xs space-y-1.5" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>File</span><span className="font-mono truncate ml-2" style={{ color: '#E8ECF1' }}>{analysis.filename}</span></div>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>SWF Version</span><span className="font-mono" style={{ color: '#E8ECF1' }}>{analysis.swf_version}</span></div>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Compressed</span><span className="font-mono" style={{ color: analysis.compressed ? '#00D4AA' : '#6B7A90' }}>{analysis.compressed ? 'Yes (zlib)' : 'No'}</span></div>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>File Size</span><span className="font-mono" style={{ color: '#E8ECF1' }}>{analysis.file_size?.toLocaleString()}B</span></div>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Uncompressed</span><span className="font-mono" style={{ color: '#E8ECF1' }}>{analysis.uncompressed_size?.toLocaleString()}B</span></div>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Strings Found</span><span className="font-mono" style={{ color: '#E8ECF1' }}>{analysis.total_strings}</span></div>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Identifiers</span><span className="font-mono" style={{ color: '#00D4AA' }}>{analysis.identifiers_count}</span></div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-wider mb-2 font-medium" style={{ color: '#6B7A90' }}>Content Categories</div>
                <div className="space-y-1">
                  {Object.keys(analysis.categories || {}).map(cat => (
                    <div key={cat} className="flex items-center gap-2 text-xs">
                      <span className="w-2 h-2 rounded-full" style={{ background: CAT_COLORS[cat] || '#6B7A90' }} />
                      <span className="capitalize" style={{ color: '#E8ECF1' }}>{cat}</span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : selectedContent && activeTab === 'registry' ? (
            <>
              <div className="rounded border p-3 text-xs space-y-1.5" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
                <div className="text-sm font-medium mb-2" style={{ color: '#E8ECF1' }}>{selectedContent.name}</div>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Game</span><span style={{ color: '#E8ECF1' }}>{selectedContent.game_title}</span></div>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Manufacturer</span><span style={{ color: '#E8ECF1' }}>{selectedContent.manufacturer}</span></div>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Type</span><span className="font-mono uppercase" style={{ color: '#E8ECF1' }}>{selectedContent.content_type}</span></div>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Version</span><span className="font-mono" style={{ color: '#E8ECF1' }}>{selectedContent.version}</span></div>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Status</span><span className="font-mono capitalize" style={{ color: selectedContent.status === 'deployed' ? '#00D4AA' : '#F5A623' }}>{selectedContent.status}</span></div>
                <div className="flex justify-between"><span style={{ color: '#6B7A90' }}>Devices</span><span className="font-mono" style={{ color: '#E8ECF1' }}>{selectedContent.deployed_device_count || 0}</span></div>
              </div>
              {selectedContent.categories?.length > 0 && (
                <div>
                  <div className="text-[10px] uppercase tracking-wider mb-2 font-medium" style={{ color: '#6B7A90' }}>Categories</div>
                  <div className="flex flex-wrap gap-1">{selectedContent.categories.map(c => <span key={c} className="text-[9px] px-1.5 py-0.5 rounded capitalize" style={{ background: `${CAT_COLORS[c] || '#6B7A90'}15`, color: CAT_COLORS[c] || '#6B7A90' }}>{c}</span>)}</div>
                </div>
              )}
            </>
          ) : (
            <div className="text-center text-xs py-8" style={{ color: '#6B7A90' }}>
              <FileCode size={28} className="mx-auto mb-2" style={{ color: '#272E3B' }} />
              Upload a file to see analysis details
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
