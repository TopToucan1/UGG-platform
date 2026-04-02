import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { ListMagnifyingGlass, Funnel } from '@phosphor-icons/react';

export default function AuditExplorerPage() {
  const [records, setRecords] = useState([]);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState(null);
  const [actionFilter, setActionFilter] = useState('');
  const [actorFilter, setActorFilter] = useState('');
  const [targetFilter, setTargetFilter] = useState('');

  useEffect(() => {
    api.get('/audit/actions').then(r => setFilters(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    const params = new URLSearchParams();
    if (actionFilter) params.set('action', actionFilter);
    if (actorFilter) params.set('actor', actorFilter);
    if (targetFilter) params.set('target_type', targetFilter);
    params.set('limit', '100');
    api.get(`/audit?${params}`).then(r => {
      setRecords(r.data.records || []);
      setTotal(r.data.total || 0);
    }).catch(() => {});
  }, [actionFilter, actorFilter, targetFilter]);

  return (
    <div data-testid="audit-explorer" className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-2xl font-bold tracking-tight" style={{ color: '#E8ECF1' }}>Audit Explorer</h1>
        <span className="text-xs font-mono" style={{ color: '#6B7A90' }}>{total} records</span>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <Funnel size={16} style={{ color: '#6B7A90' }} />
        <select data-testid="audit-action-filter" value={actionFilter} onChange={e => setActionFilter(e.target.value)} className="px-3 py-1.5 rounded text-xs outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}>
          <option value="">All Actions</option>
          {filters?.actions?.map(a => <option key={a} value={a}>{a}</option>)}
        </select>
        <select data-testid="audit-actor-filter" value={actorFilter} onChange={e => setActorFilter(e.target.value)} className="px-3 py-1.5 rounded text-xs outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}>
          <option value="">All Actors</option>
          {filters?.actors?.map(a => <option key={a} value={a}>{a}</option>)}
        </select>
        <select data-testid="audit-target-filter" value={targetFilter} onChange={e => setTargetFilter(e.target.value)} className="px-3 py-1.5 rounded text-xs outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}>
          <option value="">All Targets</option>
          {filters?.target_types?.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>

      {/* Table */}
      <div className="rounded border overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }}>
        <div className="grid grid-cols-12 gap-2 px-4 py-2 text-[11px] uppercase tracking-wider font-medium border-b" style={{ color: '#6B7A90', borderColor: '#272E3B' }}>
          <div className="col-span-2">Timestamp</div>
          <div className="col-span-2">Actor</div>
          <div className="col-span-2">Action</div>
          <div className="col-span-1">Target</div>
          <div className="col-span-3">Target ID</div>
          <div className="col-span-2">Evidence</div>
        </div>
        <div className="max-h-[calc(100vh-280px)] overflow-y-auto">
          {records.map(r => (
            <div key={r.id} className="grid grid-cols-12 gap-2 px-4 py-2.5 border-b text-xs hover:bg-white/[0.02] transition-colors" style={{ borderColor: '#272E3B20' }}>
              <div className="col-span-2 font-mono" style={{ color: '#6B7A90' }}>{new Date(r.timestamp).toLocaleString()}</div>
              <div className="col-span-2" style={{ color: '#A3AEBE' }}>{r.actor}</div>
              <div className="col-span-2 font-mono font-medium" style={{ color: '#E8ECF1' }}>{r.action}</div>
              <div className="col-span-1 font-mono uppercase" style={{ color: '#6B7A90' }}>{r.target_type}</div>
              <div className="col-span-3 font-mono truncate" style={{ color: '#6B7A90' }}>{r.target_id}</div>
              <div className="col-span-2 font-mono truncate" style={{ color: '#00D4AA' }}>{r.evidence_ref}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
