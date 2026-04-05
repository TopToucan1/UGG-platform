import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { BookOpen, MagnifyingGlass, ShieldCheck, Warning, CaretRight, Check, X } from '@phosphor-icons/react';
import InfoTip from '@/components/InfoTip';

const SEV_C = { ERROR: '#FF3B3B', WARNING: '#FFB800' };
const CAT_C = { EVENT_SUBSCRIPTION: '#00B4D8', EVENT_REPORT: '#00D97E', STATE_TRANSITION: '#8B5CF6' };

export default function ComplianceBrowserPage() {
  const [rules, setRules] = useState([]);
  const [selected, setSelected] = useState(null);
  const [search, setSearch] = useState('');
  const [catFilter, setCatFilter] = useState('');
  const [classFilter, setClassFilter] = useState('');

  useEffect(() => {
    const params = new URLSearchParams();
    if (catFilter) params.set('category', catFilter);
    if (classFilter) params.set('g2s_class', classFilter);
    if (search) params.set('q', search);
    // Public endpoint — no auth needed but using api for consistency
    api.get(`/compliance/rules?${params}`).then(r => setRules(r.data.rules || [])).catch(() => {
      // Fallback: try without auth
      fetch(`${process.env.REACT_APP_BACKEND_URL}/api/compliance/rules?${params}`).then(r => r.json()).then(d => setRules(d.rules || []));
    });
  }, [search, catFilter, classFilter]);

  const categories = [...new Set(rules.map(r => r.category))];
  const classes = [...new Set(rules.map(r => r.g2s_class))];

  return (
    <div data-testid="compliance-browser" className="flex gap-0 h-full -m-6">
      {/* Left — Filter + Rule List */}
      <div className="w-80 border-r flex flex-col flex-shrink-0 overflow-hidden" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
        <div className="px-4 py-3 border-b" style={{ borderColor: '#1A2540' }}>
          <h2 className="font-heading text-sm font-semibold flex items-center gap-2" style={{ color: '#F0F4FF' }}>
            <BookOpen size={16} style={{ color: '#06B6D4' }} /> Compliance Reference<InfoTip label="Compliance Reference" description="Searchable encyclopedia of G2S protocol rules — what the regulator expects, why it matters, and how to fix violations. Use this to look up any rule ID cited in an audit finding." />
          </h2>
          <div className="text-[10px] mt-0.5" style={{ color: '#4A6080' }}>Public G2S protocol rule encyclopedia</div>
        </div>
        <div className="px-3 py-2 space-y-2">
          <div className="relative">
            <MagnifyingGlass size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2" style={{ color: '#4A6080' }} />
            <input data-testid="compliance-search" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search rules..."
              className="w-full pl-8 pr-3 py-2 rounded text-xs outline-none" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} />
            <InfoTip description="Full-text search across rule IDs, titles, and descriptions." />
          </div>
          <div className="flex items-center">
          <select data-testid="compliance-cat-filter" value={catFilter} onChange={e => setCatFilter(e.target.value)} className="w-full px-3 py-1.5 rounded text-xs outline-none" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }}>
            <option value="">All Categories</option>
            {categories.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <InfoTip description="Filter by rule category (event subscription, event report, state transition, etc.)." />
          </div>
          <div className="flex items-center">
          <select data-testid="compliance-class-filter" value={classFilter} onChange={e => setClassFilter(e.target.value)} className="w-full px-3 py-1.5 rounded text-xs outline-none" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }}>
            <option value="">All Classes</option>
            {classes.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <InfoTip description="Filter by G2S class — the protocol group a rule applies to (meters, cabinet, events, etc.)." />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto" data-testid="rule-list">
          {rules.map(r => (
            <button key={r.ruleId} data-testid={`rule-${r.ruleId}`} onClick={() => setSelected(r)}
              className="w-full text-left px-4 py-3 border-b transition-colors" style={{ borderColor: '#1A254020', background: selected?.ruleId === r.ruleId ? 'rgba(6,182,212,0.05)' : 'transparent' }}>
              <div className="flex items-center gap-2 mb-1">
                <span className="font-mono text-[10px] px-1.5 py-0.5 rounded font-bold" style={{ background: `${SEV_C[r.severity]}15`, color: SEV_C[r.severity] }}>{r.severity}</span>
                <span className="font-mono text-xs font-semibold" style={{ color: '#F0F4FF' }}>{r.ruleId}</span>
              </div>
              <div className="text-xs" style={{ color: '#8BA3CC' }}>{r.title}</div>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-[9px] px-1.5 py-0.5 rounded" style={{ background: `${CAT_C[r.category] || '#4A6080'}15`, color: CAT_C[r.category] || '#4A6080' }}>{r.category}</span>
                <span className="text-[9px] font-mono" style={{ color: '#4A6080' }}>{r.g2s_class}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Right — Rule Detail */}
      <div className="flex-1 overflow-y-auto p-6" style={{ background: '#070B14' }}>
        {selected ? (
          <div className="max-w-3xl space-y-5" data-testid="rule-detail">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <span className="font-mono text-lg font-bold" style={{ color: '#F0F4FF' }}>{selected.ruleId}</span>
                <span className="text-sm px-3 py-1 rounded font-bold" style={{ background: `${SEV_C[selected.severity]}20`, color: SEV_C[selected.severity] }}>{selected.severity}</span>
                <span className="text-xs px-2 py-0.5 rounded" style={{ background: `${CAT_C[selected.category]}15`, color: CAT_C[selected.category] }}>{selected.category}</span>
              </div>
              <h2 className="font-heading text-xl font-bold" style={{ color: '#F0F4FF' }}>{selected.title}</h2>
              <div className="text-xs font-mono mt-1" style={{ color: '#4A6080' }}>{selected.g2s_class}</div>
            </div>

            <div className="rounded-lg border p-4" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
              <div className="text-[10px] uppercase tracking-wider mb-2 font-medium flex items-center" style={{ color: '#4A6080' }}>Description<InfoTip description="Plain-language statement of what the rule requires." /></div>
              <p className="text-sm leading-relaxed" style={{ color: '#8BA3CC' }}>{selected.description}</p>
            </div>

            {selected.why_it_matters && (
              <div className="rounded-lg border p-4" style={{ background: '#0C1322', borderColor: '#FF3B3B20' }}>
                <div className="text-[10px] uppercase tracking-wider mb-2 font-medium flex items-center" style={{ color: '#FF3B3B' }}>Why It Matters<InfoTip description="Regulatory/business impact if the rule is violated — e.g. tax misreporting, license risk." /></div>
                <p className="text-sm leading-relaxed" style={{ color: '#F0F4FF' }}>{selected.why_it_matters}</p>
              </div>
            )}

            {selected.protocol_ref && (
              <div className="rounded-lg border p-4" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
                <div className="text-[10px] uppercase tracking-wider mb-2 font-medium flex items-center" style={{ color: '#00B4D8' }}>Protocol Reference<InfoTip description="Pointer to the section of the G2S specification that defines this rule." /></div>
                <p className="text-sm font-mono" style={{ color: '#00B4D8' }}>{selected.protocol_ref}</p>
              </div>
            )}

            {selected.expected_behavior && (
              <div className="rounded-lg border p-4" style={{ background: '#0C1322', borderColor: '#00D97E20' }}>
                <div className="text-[10px] uppercase tracking-wider mb-2 font-medium flex items-center gap-1" style={{ color: '#00D97E' }}><Check size={12} /> Expected Behavior<InfoTip description="Exactly what a compliant machine or host must do to satisfy this rule." /></div>
                <p className="text-sm leading-relaxed" style={{ color: '#8BA3CC' }}>{selected.expected_behavior}</p>
              </div>
            )}

            {selected.violation_example && (
              <div className="rounded-lg border p-4" style={{ background: '#0C1322', borderColor: '#FF3B3B20' }}>
                <div className="text-[10px] uppercase tracking-wider mb-2 font-medium flex items-center gap-1" style={{ color: '#FF3B3B' }}><X size={12} /> Violation Example<InfoTip description="Concrete example of a non-compliant behavior — useful when triaging real findings." /></div>
                <p className="text-sm leading-relaxed font-mono" style={{ color: '#FF6B6B' }}>{selected.violation_example}</p>
              </div>
            )}

            {selected.fix_guidance && (
              <div className="rounded-lg border p-4" style={{ background: '#0C1322', borderColor: '#FFB80020' }}>
                <div className="text-[10px] uppercase tracking-wider mb-2 font-medium flex items-center gap-1" style={{ color: '#FFB800' }}><ShieldCheck size={12} /> Fix Guidance<InfoTip description="Recommended remediation steps operators can take to close the finding." /></div>
                <p className="text-sm leading-relaxed" style={{ color: '#8BA3CC' }}>{selected.fix_guidance}</p>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <BookOpen size={48} className="mx-auto mb-3" style={{ color: '#1A2540' }} />
              <div className="text-sm" style={{ color: '#4A6080' }}>Select a compliance rule to view full details</div>
              <div className="text-xs mt-1" style={{ color: '#4A6080' }}>{rules.length} rules available</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
