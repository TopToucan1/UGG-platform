import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Sparkle, Wrench, CurrencyDollar, Warning, MagnifyingGlass, PaperPlaneTilt, Clock, Lightning } from '@phosphor-icons/react';

const ANALYSIS_TYPES = [
  { id: 'predictive', label: 'Predictive Maintenance', icon: Wrench, color: '#FF3B3B', desc: 'Predict device failures before they happen' },
  { id: 'forecast', label: 'NOR Forecast', icon: CurrencyDollar, color: '#00D97E', desc: 'Revenue predictions for 7 and 30 days' },
  { id: 'exceptions', label: 'Exception Patterns', icon: Warning, color: '#FFB800', desc: 'Pattern analysis across all exceptions' },
  { id: 'query', label: 'Ask Anything', icon: MagnifyingGlass, color: '#00B4D8', desc: 'Natural language query about your estate' },
];

export default function AIAnalyticsPage() {
  const [activeType, setActiveType] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [question, setQuestion] = useState('');
  const [history, setHistory] = useState([]);

  useEffect(() => { api.get('/ai-analytics/history?limit=10').then(r => setHistory(r.data.results || [])).catch(() => {}); }, []);

  const runAnalysis = async (type) => {
    setActiveType(type);
    setLoading(true);
    setResult(null);
    try {
      let data;
      if (type === 'predictive') {
        ({ data } = await api.post('/ai-analytics/predictive-maintenance'));
      } else if (type === 'forecast') {
        ({ data } = await api.post('/ai-analytics/nor-forecast'));
      } else if (type === 'exceptions') {
        ({ data } = await api.post('/ai-analytics/exception-patterns'));
      }
      setResult(data);
      setHistory(prev => [data, ...prev].slice(0, 10));
    } catch (err) {
      setResult({ error: err.response?.data?.detail || err.message });
    }
    setLoading(false);
  };

  const askQuestion = async () => {
    if (!question.trim()) return;
    setActiveType('query');
    setLoading(true);
    setResult(null);
    try {
      const { data } = await api.post('/ai-analytics/query', { question });
      setResult(data);
      setHistory(prev => [data, ...prev].slice(0, 10));
    } catch (err) {
      setResult({ error: err.response?.data?.detail || err.message });
    }
    setLoading(false);
  };

  return (
    <div data-testid="ai-analytics" className="flex gap-0 h-full -m-6">
      {/* Left — Analysis Types + History */}
      <div className="w-72 border-r flex flex-col flex-shrink-0 overflow-hidden" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
        <div className="px-4 py-3 border-b" style={{ borderColor: '#1A2540' }}>
          <h2 className="font-heading text-sm font-semibold flex items-center gap-2" style={{ color: '#F0F4FF' }}>
            <Sparkle size={16} weight="fill" style={{ color: '#FFB800' }} /> AI Analytics
          </h2>
          <div className="text-[10px] mt-0.5" style={{ color: '#4A6080' }}>Powered by Gemini 3 Flash</div>
        </div>

        {/* Analysis Buttons */}
        <div className="p-3 space-y-2">
          {ANALYSIS_TYPES.filter(t => t.id !== 'query').map(t => (
            <button key={t.id} data-testid={`analysis-${t.id}`} onClick={() => runAnalysis(t.id)}
              disabled={loading}
              className="w-full text-left px-3 py-3 rounded-lg transition-all hover:-translate-y-[1px] disabled:opacity-50"
              style={{ background: activeType === t.id ? `${t.color}10` : '#111827', border: `1px solid ${activeType === t.id ? `${t.color}40` : '#1A2540'}` }}>
              <div className="flex items-center gap-2 mb-1">
                <t.icon size={16} style={{ color: t.color }} />
                <span className="text-xs font-semibold" style={{ color: '#F0F4FF' }}>{t.label}</span>
              </div>
              <div className="text-[10px]" style={{ color: '#4A6080' }}>{t.desc}</div>
            </button>
          ))}
        </div>

        {/* History */}
        <div className="px-3 py-2 text-[9px] uppercase tracking-widest font-medium" style={{ color: '#4A6080' }}>History</div>
        <div className="flex-1 overflow-y-auto px-3">
          {history.map(h => {
            const typeConfig = ANALYSIS_TYPES.find(t => t.id === h.type || (h.type === 'predictive_maintenance' && t.id === 'predictive') || (h.type === 'nor_forecast' && t.id === 'forecast') || (h.type === 'exception_patterns' && t.id === 'exceptions'));
            return (
              <button key={h.id} onClick={() => { setResult(h); setActiveType(h.type); }}
                className="w-full text-left px-3 py-2 rounded mb-1 text-[10px] transition-colors hover:bg-white/[0.03]" style={{ background: '#111827' }}>
                <div className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full" style={{ background: typeConfig?.color || '#4A6080' }} />
                  <span style={{ color: '#F0F4FF' }}>{h.type === 'query' ? h.question?.slice(0, 30) : h.type?.replace(/_/g, ' ')}</span>
                </div>
                <div className="font-mono" style={{ color: '#4A6080' }}>{h.created_at?.slice(0, 16)}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Center — Results */}
      <div className="flex-1 flex flex-col overflow-hidden" style={{ background: '#070B14' }}>
        {/* Natural Language Query Bar */}
        <div className="px-6 py-3 border-b" style={{ borderColor: '#1A2540', background: '#0C1322' }}>
          <div className="flex gap-2">
            <input data-testid="ai-query-input" value={question} onChange={e => setQuestion(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && askQuestion()}
              placeholder="Ask anything about your estate... e.g. 'Which devices are most likely to fail this week?'"
              className="flex-1 px-4 py-2.5 rounded-lg text-sm outline-none" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} />
            <button data-testid="ai-query-send" onClick={askQuestion} disabled={loading}
              className="px-5 py-2.5 rounded-lg text-sm font-semibold disabled:opacity-50" style={{ background: '#00B4D8', color: '#070B14' }}>
              <PaperPlaneTilt size={18} />
            </button>
          </div>
        </div>

        {/* Results Area */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading && (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <Sparkle size={32} className="mx-auto mb-3 animate-spin" style={{ color: '#FFB800' }} />
                <div className="text-sm" style={{ color: '#F0F4FF' }}>Analyzing estate data with Gemini...</div>
                <div className="text-[10px] mt-1" style={{ color: '#4A6080' }}>Querying devices, events, NOR, exceptions, and digital twin data</div>
              </div>
            </div>
          )}

          {result && !loading && !result.error && (
            <div className="space-y-4" data-testid="ai-result">
              {/* Header */}
              <div className="flex items-center gap-3">
                <Sparkle size={20} weight="fill" style={{ color: '#FFB800' }} />
                <span className="font-heading text-lg font-semibold" style={{ color: '#F0F4FF' }}>
                  {result.type === 'query' ? 'Answer' : result.type?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                </span>
                {result.question && <span className="text-xs px-3 py-1 rounded-full" style={{ background: '#111827', color: '#00B4D8' }}>"{result.question}"</span>}
              </div>

              {/* AI Response */}
              <div className="rounded-lg border p-6" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
                <div className="prose prose-invert max-w-none">
                  {result.result?.split('\n').map((line, i) => {
                    if (!line.trim()) return <div key={i} className="h-2" />;
                    // Headers
                    if (line.match(/^\d+\.\s+[A-Z]/)) return <h3 key={i} className="font-heading text-sm font-bold mt-4 mb-2" style={{ color: '#00B4D8' }}>{line}</h3>;
                    if (line.startsWith('**') && line.endsWith('**')) return <h4 key={i} className="font-semibold text-sm mt-3 mb-1" style={{ color: '#F0F4FF' }}>{line.replace(/\*\*/g, '')}</h4>;
                    // Bullets
                    if (line.startsWith('- ') || line.startsWith('* ')) return (
                      <div key={i} className="flex gap-2 ml-4 mb-1 text-sm" style={{ color: '#8BA3CC' }}>
                        <span style={{ color: '#00D97E' }}>•</span>
                        <span>{line.slice(2)}</span>
                      </div>
                    );
                    // Dollar amounts highlighted
                    const highlighted = line.replace(/\$[\d,]+(\.\d+)?/g, match => `<span style="color:#00D97E;font-family:JetBrains Mono,monospace">${match}</span>`);
                    const percentHighlighted = highlighted.replace(/\d+\.?\d*%/g, match => `<span style="color:#FFB800;font-family:JetBrains Mono,monospace">${match}</span>`);
                    return <p key={i} className="text-sm mb-1 leading-relaxed" style={{ color: '#8BA3CC' }} dangerouslySetInnerHTML={{ __html: percentHighlighted }} />;
                  })}
                </div>
              </div>

              {/* Metadata */}
              <div className="flex items-center gap-4 text-[10px] font-mono" style={{ color: '#4A6080' }}>
                <span><Clock size={10} className="inline mr-1" />{result.created_at?.slice(0, 19)}</span>
                {result.device_count !== undefined && <span><Lightning size={10} className="inline mr-1" />{result.device_count} devices analyzed</span>}
                {result.exception_count !== undefined && <span><Warning size={10} className="inline mr-1" />{result.exception_count} exceptions analyzed</span>}
                {result.trend_days && <span>{result.trend_days} days of NOR data</span>}
              </div>
            </div>
          )}

          {result?.error && (
            <div className="rounded-lg border p-4" style={{ background: 'rgba(255,59,59,0.05)', borderColor: '#FF3B3B30' }}>
              <div className="text-sm" style={{ color: '#FF3B3B' }}>{result.error}</div>
            </div>
          )}

          {!result && !loading && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-md">
                <Sparkle size={48} className="mx-auto mb-4" style={{ color: '#1A2540' }} />
                <h3 className="font-heading text-lg font-semibold mb-2" style={{ color: '#F0F4FF' }}>AI-Powered Analytics</h3>
                <p className="text-sm mb-4" style={{ color: '#4A6080' }}>
                  Choose an analysis type from the left panel, or ask any question about your gaming estate using the search bar above.
                </p>
                <div className="space-y-2 text-left">
                  {['Which devices are most likely to fail this week?', 'What will our NOR be next month?', 'Why are we getting so many DEVICE_OFFLINE exceptions?', 'How can we increase revenue by 10%?'].map(q => (
                    <button key={q} onClick={() => { setQuestion(q); }} className="w-full text-left px-3 py-2 rounded text-xs transition-colors hover:bg-white/[0.03]" style={{ background: '#0C1322', border: '1px solid #1A2540', color: '#8BA3CC' }}>
                      "{q}"
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
