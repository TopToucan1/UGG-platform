import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { BookOpen, MagnifyingGlass, CaretRight, Rocket, ChartBar, MapPin, Flask, Sparkle, Cpu, GearSix } from '@phosphor-icons/react';
import InfoTip from '@/components/InfoTip';

const SECTION_ICONS = { 'getting-started': Rocket, 'operations': ChartBar, 'route-ops': MapPin, 'testing': Flask, 'ai-tools': Sparkle, 'hardware': Cpu, 'admin': GearSix };

export default function DocsLibraryPage() {
  const [sections, setSections] = useState([]);
  const [activeSection, setActiveSection] = useState(null);
  const [sectionDocs, setSectionDocs] = useState(null);
  const [activeArticle, setActiveArticle] = useState(null);
  const [search, setSearch] = useState('');
  const [searchResults, setSearchResults] = useState([]);

  useEffect(() => { api.get('/library').then(r => setSections(r.data.sections || [])); }, []);

  const loadSection = async (sectionId) => {
    setActiveSection(sectionId);
    setActiveArticle(null);
    const { data } = await api.get(`/library/section/${sectionId}`);
    setSectionDocs(data);
    if (data.docs?.length > 0) setActiveArticle(data.docs[0]);
  };

  const searchDocs = async () => {
    if (!search.trim()) { setSearchResults([]); return; }
    const { data } = await api.get(`/library/search?q=${encodeURIComponent(search)}`);
    setSearchResults(data.results || []);
  };

  const loadArticleFromSearch = async (docId) => {
    const { data } = await api.get(`/library/article/${docId}`);
    setActiveArticle(data);
    setActiveSection(data.section_id);
    setSearchResults([]);
    setSearch('');
    // Also load the section
    const secData = await api.get(`/library/section/${data.section_id}`);
    setSectionDocs(secData.data);
  };

  return (
    <div data-testid="docs-library" className="flex gap-0 h-full -m-6">
      {/* Left — Sections + TOC */}
      <div className="w-72 border-r flex flex-col flex-shrink-0 overflow-hidden" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
        <div className="px-4 py-3 border-b" style={{ borderColor: '#1A2540' }}>
          <h2 className="font-heading text-sm font-semibold flex items-center gap-2" style={{ color: '#F0F4FF' }}>
            <BookOpen size={16} style={{ color: '#06B6D4' }} /> Documentation
            <InfoTip label="Documentation Library" description="In-app operator guides for every corner of the platform — getting started, daily operations, route ops, hardware setup, admin, and more. Search across all docs with the box below." />
          </h2>
        </div>
        {/* Search */}
        <div className="px-3 py-2">
          <div className="relative flex items-center">
            <MagnifyingGlass size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2" style={{ color: '#4A6080' }} />
            <input data-testid="doc-search" value={search} onChange={e => setSearch(e.target.value)} onKeyDown={e => e.key === 'Enter' && searchDocs()} placeholder="Search docs..."
              className="w-full pl-8 pr-3 py-2 rounded text-xs outline-none" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} />
            <InfoTip label="Search" description="Type a keyword and press Enter to search across every article in the library. Click a result to jump straight to it." />
          </div>
          {searchResults.length > 0 && (
            <div className="mt-1 rounded border" style={{ background: '#111827', borderColor: '#1A2540' }}>
              {searchResults.map(r => (
                <button key={r.id} onClick={() => loadArticleFromSearch(r.id)} className="w-full text-left px-3 py-2 border-b text-xs hover:bg-white/[0.03]" style={{ borderColor: '#1A254020' }}>
                  <div style={{ color: '#F0F4FF' }}>{r.title}</div>
                  <div className="text-[9px]" style={{ color: '#4A6080' }}>{r.section} | {r.snippet?.slice(0, 60)}...</div>
                </button>
              ))}
            </div>
          )}
        </div>
        {/* Section list */}
        <div className="flex-1 overflow-y-auto">
          {sections.map(s => {
            const Icon = SECTION_ICONS[s.id] || BookOpen;
            const isActive = activeSection === s.id;
            return (
              <div key={s.id}>
                <button data-testid={`doc-section-${s.id}`} onClick={() => loadSection(s.id)}
                  className="w-full text-left px-4 py-2.5 flex items-center gap-2 transition-colors"
                  style={{ background: isActive ? 'rgba(6,182,212,0.08)' : 'transparent' }}>
                  <Icon size={14} style={{ color: isActive ? '#06B6D4' : '#4A6080' }} />
                  <span className="text-xs font-medium" style={{ color: isActive ? '#06B6D4' : '#8BA3CC' }}>{s.title}</span>
                  <span className="ml-auto text-[9px] font-mono" style={{ color: '#4A6080' }}>{s.doc_count}</span>
                </button>
                {isActive && sectionDocs?.docs && (
                  <div className="ml-8 border-l" style={{ borderColor: '#1A2540' }}>
                    {sectionDocs.docs.map(d => (
                      <button key={d.id} data-testid={`doc-article-${d.id}`} onClick={() => setActiveArticle(d)}
                        className="w-full text-left px-3 py-1.5 text-[11px] transition-colors"
                        style={{ color: activeArticle?.id === d.id ? '#06B6D4' : '#4A6080', background: activeArticle?.id === d.id ? 'rgba(6,182,212,0.05)' : 'transparent' }}>
                        {d.title}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Right — Article Content */}
      <div className="flex-1 overflow-y-auto p-8" style={{ background: '#070B14' }}>
        {activeArticle ? (
          <div className="max-w-3xl" data-testid="doc-content">
            <div className="mb-6">
              <div className="text-[10px] uppercase tracking-wider mb-2" style={{ color: '#4A6080' }}>{sectionDocs?.title || activeArticle.section_title}</div>
              <h1 className="font-heading text-2xl font-bold" style={{ color: '#F0F4FF' }}>{activeArticle.title}</h1>
            </div>
            <div className="space-y-4">
              {activeArticle.content?.split('\n\n').map((block, i) => {
                // Handle markdown-like formatting
                if (block.startsWith('**') && block.endsWith('**')) {
                  return <h2 key={i} className="font-heading text-lg font-semibold mt-6 mb-2" style={{ color: '#F0F4FF' }}>{block.replace(/\*\*/g, '')}</h2>;
                }
                if (block.startsWith('**')) {
                  return <h3 key={i} className="font-heading text-base font-semibold mt-4 mb-2" style={{ color: '#00B4D8' }}>{block.replace(/\*\*/g, '')}</h3>;
                }

                // Process inline formatting
                const lines = block.split('\n');
                return (
                  <div key={i} className="space-y-1">
                    {lines.map((line, li) => {
                      if (line.startsWith('- ') || line.startsWith('* ')) {
                        return (
                          <div key={li} className="flex gap-2 ml-4 text-sm" style={{ color: '#8BA3CC' }}>
                            <span style={{ color: '#06B6D4' }}>•</span>
                            <span dangerouslySetInnerHTML={{ __html: line.slice(2).replace(/\*\*(.*?)\*\*/g, '<strong style="color:#F0F4FF">$1</strong>').replace(/`(.*?)`/g, '<code style="color:#00D97E;background:#111827;padding:1px 4px;border-radius:3px;font-size:12px">$1</code>') }} />
                          </div>
                        );
                      }
                      if (/^\d+\.\s/.test(line)) {
                        return (
                          <div key={li} className="flex gap-2 ml-4 text-sm" style={{ color: '#8BA3CC' }}>
                            <span className="font-mono font-bold" style={{ color: '#FFB800' }}>{line.match(/^\d+/)[0]}.</span>
                            <span dangerouslySetInnerHTML={{ __html: line.replace(/^\d+\.\s*/, '').replace(/\*\*(.*?)\*\*/g, '<strong style="color:#F0F4FF">$1</strong>').replace(/`(.*?)`/g, '<code style="color:#00D97E;background:#111827;padding:1px 4px;border-radius:3px;font-size:12px">$1</code>') }} />
                          </div>
                        );
                      }
                      return <p key={li} className="text-sm leading-relaxed" style={{ color: '#8BA3CC' }} dangerouslySetInnerHTML={{ __html: line.replace(/\*\*(.*?)\*\*/g, '<strong style="color:#F0F4FF">$1</strong>').replace(/`(.*?)`/g, '<code style="color:#00D97E;background:#111827;padding:1px 4px;border-radius:3px;font-size:12px">$1</code>') }} />;
                    })}
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center max-w-md">
              <BookOpen size={48} className="mx-auto mb-4" style={{ color: '#1A2540' }} />
              <h3 className="font-heading text-xl font-semibold mb-2" style={{ color: '#F0F4FF' }}>UGG Documentation Library</h3>
              <p className="text-sm mb-4" style={{ color: '#4A6080' }}>Comprehensive guides for every aspect of the Universal Gaming Gateway. Select a section from the left to get started.</p>
              <div className="grid grid-cols-2 gap-2">
                {sections.map(s => {
                  const Icon = SECTION_ICONS[s.id] || BookOpen;
                  return (
                    <button key={s.id} onClick={() => loadSection(s.id)} className="flex items-center gap-2 px-3 py-2.5 rounded-lg text-xs text-left transition-colors hover:-translate-y-[1px]" style={{ background: '#0C1322', border: '1px solid #1A2540', color: '#8BA3CC' }}>
                      <Icon size={14} style={{ color: '#06B6D4' }} /> {s.title} ({s.doc_count})
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
