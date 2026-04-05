import { useState } from 'react';
import api from '@/lib/api';
import { Robot, PaperPlaneTilt, Sparkle, Database, FileCode, Plugs } from '@phosphor-icons/react';
import InfoTip from '@/components/InfoTip';

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
    { id: 'chat', label: 'Chat', icon: Robot, tip: 'Free-form chat with the UGG AI assistant. Ask about SAS/G2S protocols, how meters work, what a canonical field should be, etc.' },
    { id: 'discover', label: 'Discovery', icon: Database, tip: 'Point the AI at an unknown data source (sample JSON, XML, log, etc.) and it will try to identify fields and suggest mappings.' },
    { id: 'generate', label: 'Generate', icon: FileCode, tip: 'Describe a connector in plain language and the AI will scaffold a config you can review and deploy.' },
  ];

  return (
    <div data-testid="ai-studio" className="flex gap-0 h-full -m-6">
      {/* Mode Selector */}
      <div className="w-56 border-r flex-shrink-0 flex flex-col" style={{ background: '#12151C', borderColor: '#272E3B' }}>
        <div className="px-4 py-3 border-b" style={{ borderColor: '#272E3B' }}>
          <h2 className="font-heading text-base font-semibold flex items-center gap-2" style={{ color: '#E8ECF1' }}>
            <Sparkle size={18} style={{ color: '#00D4AA' }} /> AI Studio
            <InfoTip label="AI Studio" description="A built-in AI assistant for connector engineering. Chat with it about protocols, use Discovery to reverse-engineer a new data source, or use Generate to scaffold a new connector from a description." />
          </h2>
        </div>
        <div className="p-2 space-y-1">
          {modes.map(m => (
            <div key={m.id} className="flex items-center">
              <button
                data-testid={`ai-mode-${m.id}`}
                onClick={() => setActiveMode(m.id)}
                className="flex-1 flex items-center gap-2 px-3 py-2.5 rounded text-sm transition-colors"
                style={{ background: activeMode === m.id ? 'rgba(0,212,170,0.1)' : 'transparent', color: activeMode === m.id ? '#00D4AA' : '#A3AEBE' }}
              >
                <m.icon size={18} /> {m.label}
              </button>
              <InfoTip label={m.label} description={m.tip} />
            </div>
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
                <InfoTip label="Send" description="Send your message to the assistant. It has context about UGG's connector framework, SAS, G2S, and canonical events." />
              </div>
            </div>
          </>
        )}

        {activeMode === 'discover' && (
          <div className="flex-1 overflow-y-auto p-6" data-testid="ai-discovery-area">
            <h3 className="font-heading text-lg font-semibold mb-4 flex items-center" style={{ color: '#E8ECF1' }}>Source Discovery<InfoTip label="Source Discovery" description="Give the AI a sample of unknown data from a source system and it will analyze the shape, identify candidate fields, and suggest canonical mappings." /></h3>
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-[11px] uppercase tracking-wider mb-1.5 flex items-center" style={{ color: '#6B7A90' }}>Source Type<InfoTip description="Kind of system the data is coming from. SAS = Slot Accounting System (serial protocol on older EGMs). G2S = Game-to-System (XML over HTTPS on newer EGMs)." /></label>
                  <select data-testid="discovery-source-type" value={sourceType} onChange={e => setSourceType(e.target.value)} className="w-full px-3 py-2.5 rounded text-sm outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}>
                    <option value="rest_api">REST API</option>
                    <option value="database">Database</option>
                    <option value="log_file">Log File</option>
                    <option value="serial_port">Serial Port (SAS)</option>
                    <option value="xml_stream">XML Stream (G2S)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[11px] uppercase tracking-wider mb-1.5 flex items-center" style={{ color: '#6B7A90' }}>Description<InfoTip description="Plain-English description of the source system. The AI uses this to guide its analysis (e.g. 'Legacy Bally CMS event log, tab-delimited')." /></label>
                  <textarea data-testid="discovery-description" value={description} onChange={e => setDescription(e.target.value)} rows={3} placeholder="Describe the source system..." className="w-full px-3 py-2.5 rounded text-sm outline-none resize-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }} />
                </div>
                <div>
                  <label className="block text-[11px] uppercase tracking-wider mb-1.5 flex items-center" style={{ color: '#6B7A90' }}>Sample Data<InfoTip description="Paste a few representative rows/records from the source. The AI looks at this to infer field names, types and semantics." /></label>
                  <textarea data-testid="discovery-sample-data" value={sampleData} onChange={e => setSampleData(e.target.value)} rows={6} placeholder='{"device_id": "EGM-001", "event": "game_end", ...}' className="w-full px-3 py-2.5 rounded text-sm outline-none resize-none font-mono" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }} />
                </div>
                <div className="flex items-center">
                  <button data-testid="run-discovery-btn" onClick={runDiscovery} disabled={discoveryLoading} className="px-6 py-2.5 rounded text-sm font-medium" style={{ background: '#00D4AA', color: '#0A0C10' }}>
                    {discoveryLoading ? 'Analyzing...' : 'Run Discovery'}
                  </button>
                  <InfoTip label="Run Discovery" description="Send the sample data and description to the AI for analysis. Results appear on the right." />
                </div>
              </div>
              <div>
                <div className="text-[11px] uppercase tracking-wider mb-2 flex items-center" style={{ color: '#6B7A90' }}>AI Analysis<InfoTip description="Raw JSON output from the AI — detected fields, inferred types, and suggested canonical mappings." /></div>
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
            <h3 className="font-heading text-lg font-semibold mb-4 flex items-center" style={{ color: '#E8ECF1' }}>Generate Connector<InfoTip label="Generate Connector" description="Describe what you want and the AI will produce a connector config scaffold. Always review and approve before deploying to devices." /></h3>
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-[11px] uppercase tracking-wider mb-1.5 flex items-center" style={{ color: '#6B7A90' }}>Connector Name<InfoTip description="Friendly name for the new connector (shown in the connector list)." /></label>
                  <input data-testid="gen-name" value={genName} onChange={e => setGenName(e.target.value)} className="w-full px-3 py-2.5 rounded text-sm outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }} placeholder="My Custom Connector" />
                </div>
                <div>
                  <label className="block text-[11px] uppercase tracking-wider mb-1.5 flex items-center" style={{ color: '#6B7A90' }}>Connector Type<InfoTip description="How the connector gets data: REST Poll (calls an HTTP endpoint on a schedule), REST Webhook (receives pushed HTTP calls), DB Poll (queries a database on a schedule), or Log Tail (watches a log file)." /></label>
                  <select data-testid="gen-type" value={genType} onChange={e => setGenType(e.target.value)} className="w-full px-3 py-2.5 rounded text-sm outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}>
                    <option value="rest_poll">REST Poll</option>
                    <option value="rest_webhook">REST Webhook</option>
                    <option value="db_poll">DB Poll</option>
                    <option value="log_tail">Log Tail</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[11px] uppercase tracking-wider mb-1.5 flex items-center" style={{ color: '#6B7A90' }}>Description<InfoTip description="Tell the AI what this connector should do — which endpoint/file/DB, what events it should pull, any auth details." /></label>
                  <textarea data-testid="gen-desc" value={genDesc} onChange={e => setGenDesc(e.target.value)} rows={4} className="w-full px-3 py-2.5 rounded text-sm outline-none resize-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }} placeholder="Describe what this connector does..." />
                </div>
                <div className="flex items-center">
                  <button data-testid="run-generate-btn" onClick={runGenerate} disabled={genLoading} className="px-6 py-2.5 rounded text-sm font-medium flex items-center gap-2" style={{ background: '#00D4AA', color: '#0A0C10' }}>
                    <Plugs size={16} /> {genLoading ? 'Generating...' : 'Generate Connector'}
                  </button>
                  <InfoTip label="Generate Connector" description="Ask the AI to produce a draft connector definition. The result is a starting point — humans still review and approve before anything deploys." />
                </div>
                {genResult && (
                  <div className="text-xs px-3 py-2 rounded" style={{ background: 'rgba(245,166,35,0.1)', color: '#F5A623', border: '1px solid rgba(245,166,35,0.2)' }}>
                    AI-generated connector requires human review and approval before production deployment
                  </div>
                )}
              </div>
              <div>
                <div className="text-[11px] uppercase tracking-wider mb-2 flex items-center" style={{ color: '#6B7A90' }}>Generated Output<InfoTip description="The draft connector definition returned by the AI. Copy it into the Connector Builder to refine, test, and eventually deploy." /></div>
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
