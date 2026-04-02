import { useState } from 'react';
import api from '@/lib/api';
import { Robot, PaperPlaneTilt, Sparkle, Database, FileCode, Plugs } from '@phosphor-icons/react';

export default function AIStudioPage() {
  const [activeMode, setActiveMode] = useState('chat');
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  // Discovery
  const [sourceType, setSourceType] = useState('rest_api');
  const [description, setDescription] = useState('');
  const [sampleData, setSampleData] = useState('');
  const [discoveryResult, setDiscoveryResult] = useState(null);
  const [discoveryLoading, setDiscoveryLoading] = useState(false);
  // Generate
  const [genName, setGenName] = useState('');
  const [genType, setGenType] = useState('rest_poll');
  const [genDesc, setGenDesc] = useState('');
  const [genResult, setGenResult] = useState(null);
  const [genLoading, setGenLoading] = useState(false);

  const sendChat = async () => {
    if (!chatInput.trim() || chatLoading) return;
    const msg = chatInput.trim();
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', content: msg }]);
    setChatLoading(true);
    try {
      const { data } = await api.post('/ai-studio/chat', { message: msg, context: chatMessages.map(m => `${m.role}: ${m.content}`).join('\n') });
      setChatMessages(prev => [...prev, { role: 'ai', content: data.ai_response }]);
    } catch (err) {
      setChatMessages(prev => [...prev, { role: 'ai', content: 'Error: ' + (err.response?.data?.detail || err.message) }]);
    } finally {
      setChatLoading(false);
    }
  };

  const runDiscovery = async () => {
    setDiscoveryLoading(true);
    try {
      const { data } = await api.post('/ai-studio/discover', { source_type: sourceType, description, sample_data: sampleData });
      setDiscoveryResult(data.ai_result);
    } catch (err) {
      setDiscoveryResult({ error: err.response?.data?.detail || err.message });
    } finally {
      setDiscoveryLoading(false);
    }
  };

  const runGenerate = async () => {
    setGenLoading(true);
    try {
      const { data } = await api.post('/ai-studio/generate-connector', { name: genName, source_type: genType, description: genDesc });
      setGenResult(data.generated);
    } catch (err) {
      setGenResult({ error: err.response?.data?.detail || err.message });
    } finally {
      setGenLoading(false);
    }
  };

  const modes = [
    { id: 'chat', label: 'Chat', icon: Robot },
    { id: 'discover', label: 'Discovery', icon: Database },
    { id: 'generate', label: 'Generate', icon: FileCode },
  ];

  return (
    <div data-testid="ai-studio" className="flex gap-0 h-full -m-6">
      {/* Mode Selector */}
      <div className="w-56 border-r flex-shrink-0 flex flex-col" style={{ background: '#12151C', borderColor: '#272E3B' }}>
        <div className="px-4 py-3 border-b" style={{ borderColor: '#272E3B' }}>
          <h2 className="font-heading text-base font-semibold flex items-center gap-2" style={{ color: '#E8ECF1' }}>
            <Sparkle size={18} style={{ color: '#00D4AA' }} /> AI Studio
          </h2>
        </div>
        <div className="p-2 space-y-1">
          {modes.map(m => (
            <button
              key={m.id}
              data-testid={`ai-mode-${m.id}`}
              onClick={() => setActiveMode(m.id)}
              className="w-full flex items-center gap-2 px-3 py-2.5 rounded text-sm transition-colors"
              style={{ background: activeMode === m.id ? 'rgba(0,212,170,0.1)' : 'transparent', color: activeMode === m.id ? '#00D4AA' : '#A3AEBE' }}
            >
              <m.icon size={18} /> {m.label}
            </button>
          ))}
        </div>
        <div className="mt-auto p-4 border-t" style={{ borderColor: '#272E3B' }}>
          <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: '#6B7A90' }}>Powered by</div>
          <div className="text-xs font-mono" style={{ color: '#00D4AA' }}>Gemini 3 Flash</div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden" style={{ background: '#0A0C10' }}>
        {activeMode === 'chat' && (
          <>
            <div className="flex-1 overflow-y-auto p-6 space-y-4" data-testid="ai-chat-area">
              {chatMessages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <Robot size={48} style={{ color: '#272E3B' }} />
                  <h3 className="font-heading text-lg font-semibold mt-4" style={{ color: '#E8ECF1' }}>UGG AI Assistant</h3>
                  <p className="text-sm mt-2 max-w-md" style={{ color: '#6B7A90' }}>
                    Ask about gaming protocols, connector development, event mapping, or emulator test design.
                  </p>
                </div>
              )}
              {chatMessages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className="max-w-2xl rounded-lg px-4 py-3 text-sm" style={{
                    background: msg.role === 'user' ? 'rgba(0,212,170,0.1)' : '#12151C',
                    border: `1px solid ${msg.role === 'user' ? 'rgba(0,212,170,0.2)' : '#272E3B'}`,
                    color: '#E8ECF1',
                  }}>
                    <pre className="whitespace-pre-wrap font-sans">{msg.content}</pre>
                  </div>
                </div>
              ))}
              {chatLoading && (
                <div className="flex justify-start">
                  <div className="rounded-lg px-4 py-3 text-sm" style={{ background: '#12151C', border: '1px solid #272E3B' }}>
                    <div className="flex items-center gap-2" style={{ color: '#00D4AA' }}>
                      <Sparkle size={16} className="animate-spin" /> Thinking...
                    </div>
                  </div>
                </div>
              )}
            </div>
            <div className="p-4 border-t" style={{ borderColor: '#272E3B', background: '#12151C' }}>
              <div className="flex gap-2">
                <input
                  data-testid="ai-chat-input"
                  value={chatInput}
                  onChange={e => setChatInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && sendChat()}
                  placeholder="Ask about SAS protocols, event mapping, connector design..."
                  className="flex-1 px-4 py-2.5 rounded text-sm outline-none"
                  style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}
                />
                <button data-testid="ai-chat-send" onClick={sendChat} disabled={chatLoading} className="px-4 py-2.5 rounded font-medium text-sm" style={{ background: '#00D4AA', color: '#0A0C10' }}>
                  <PaperPlaneTilt size={18} />
                </button>
              </div>
            </div>
          </>
        )}

        {activeMode === 'discover' && (
          <div className="flex-1 overflow-y-auto p-6" data-testid="ai-discovery-area">
            <h3 className="font-heading text-lg font-semibold mb-4" style={{ color: '#E8ECF1' }}>Source Discovery</h3>
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-[11px] uppercase tracking-wider mb-1.5" style={{ color: '#6B7A90' }}>Source Type</label>
                  <select data-testid="discovery-source-type" value={sourceType} onChange={e => setSourceType(e.target.value)} className="w-full px-3 py-2.5 rounded text-sm outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}>
                    <option value="rest_api">REST API</option>
                    <option value="database">Database</option>
                    <option value="log_file">Log File</option>
                    <option value="serial_port">Serial Port (SAS)</option>
                    <option value="xml_stream">XML Stream (G2S)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[11px] uppercase tracking-wider mb-1.5" style={{ color: '#6B7A90' }}>Description</label>
                  <textarea data-testid="discovery-description" value={description} onChange={e => setDescription(e.target.value)} rows={3} placeholder="Describe the source system..." className="w-full px-3 py-2.5 rounded text-sm outline-none resize-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }} />
                </div>
                <div>
                  <label className="block text-[11px] uppercase tracking-wider mb-1.5" style={{ color: '#6B7A90' }}>Sample Data</label>
                  <textarea data-testid="discovery-sample-data" value={sampleData} onChange={e => setSampleData(e.target.value)} rows={6} placeholder='{"device_id": "EGM-001", "event": "game_end", ...}' className="w-full px-3 py-2.5 rounded text-sm outline-none resize-none font-mono" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }} />
                </div>
                <button data-testid="run-discovery-btn" onClick={runDiscovery} disabled={discoveryLoading} className="px-6 py-2.5 rounded text-sm font-medium" style={{ background: '#00D4AA', color: '#0A0C10' }}>
                  {discoveryLoading ? 'Analyzing...' : 'Run Discovery'}
                </button>
              </div>
              <div>
                <div className="text-[11px] uppercase tracking-wider mb-2" style={{ color: '#6B7A90' }}>AI Analysis</div>
                <div className="rounded border p-4 h-96 overflow-y-auto" style={{ background: '#12151C', borderColor: '#272E3B' }}>
                  {discoveryResult ? (
                    <pre className="text-xs font-mono whitespace-pre-wrap" style={{ color: '#E8ECF1' }}>
                      {JSON.stringify(discoveryResult, null, 2)}
                    </pre>
                  ) : (
                    <div className="flex items-center justify-center h-full text-xs" style={{ color: '#6B7A90' }}>
                      Run discovery to see AI analysis
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeMode === 'generate' && (
          <div className="flex-1 overflow-y-auto p-6" data-testid="ai-generate-area">
            <h3 className="font-heading text-lg font-semibold mb-4" style={{ color: '#E8ECF1' }}>Generate Connector</h3>
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-[11px] uppercase tracking-wider mb-1.5" style={{ color: '#6B7A90' }}>Connector Name</label>
                  <input data-testid="gen-name" value={genName} onChange={e => setGenName(e.target.value)} className="w-full px-3 py-2.5 rounded text-sm outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }} placeholder="My Custom Connector" />
                </div>
                <div>
                  <label className="block text-[11px] uppercase tracking-wider mb-1.5" style={{ color: '#6B7A90' }}>Connector Type</label>
                  <select data-testid="gen-type" value={genType} onChange={e => setGenType(e.target.value)} className="w-full px-3 py-2.5 rounded text-sm outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}>
                    <option value="rest_poll">REST Poll</option>
                    <option value="rest_webhook">REST Webhook</option>
                    <option value="db_poll">DB Poll</option>
                    <option value="log_tail">Log Tail</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[11px] uppercase tracking-wider mb-1.5" style={{ color: '#6B7A90' }}>Description</label>
                  <textarea data-testid="gen-desc" value={genDesc} onChange={e => setGenDesc(e.target.value)} rows={4} className="w-full px-3 py-2.5 rounded text-sm outline-none resize-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }} placeholder="Describe what this connector does..." />
                </div>
                <button data-testid="run-generate-btn" onClick={runGenerate} disabled={genLoading} className="px-6 py-2.5 rounded text-sm font-medium flex items-center gap-2" style={{ background: '#00D4AA', color: '#0A0C10' }}>
                  <Plugs size={16} /> {genLoading ? 'Generating...' : 'Generate Connector'}
                </button>
                {genResult && (
                  <div className="text-xs px-3 py-2 rounded" style={{ background: 'rgba(245,166,35,0.1)', color: '#F5A623', border: '1px solid rgba(245,166,35,0.2)' }}>
                    AI-generated connector requires human review and approval before production deployment
                  </div>
                )}
              </div>
              <div>
                <div className="text-[11px] uppercase tracking-wider mb-2" style={{ color: '#6B7A90' }}>Generated Output</div>
                <div className="rounded border p-4 h-96 overflow-y-auto" style={{ background: '#12151C', borderColor: '#272E3B' }}>
                  {genResult ? (
                    <pre className="text-xs font-mono whitespace-pre-wrap" style={{ color: '#E8ECF1' }}>
                      {JSON.stringify(genResult, null, 2)}
                    </pre>
                  ) : (
                    <div className="flex items-center justify-center h-full text-xs" style={{ color: '#6B7A90' }}>
                      Configure and generate to see output
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
