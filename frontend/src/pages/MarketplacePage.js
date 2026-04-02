import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Storefront, MagnifyingGlass, Star, ShieldCheck, Download, Tag, Funnel } from '@phosphor-icons/react';

const PRICE_COLORS = { free: '#00D4AA', per_device: '#007AFF', subscription: '#F5A623', one_time: '#8B5CF6' };
const CAT_COLORS = ['#00D4AA', '#007AFF', '#F5A623', '#FF3B30', '#8B5CF6', '#EC4899', '#06B6D4'];

export default function MarketplacePage() {
  const [connectors, setConnectors] = useState([]);
  const [total, setTotal] = useState(0);
  const [categories, setCategories] = useState([]);
  const [catCounts, setCatCounts] = useState({});
  const [stats, setStats] = useState(null);
  const [catFilter, setCatFilter] = useState('');
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    api.get('/marketplace/categories').then(r => { setCategories(r.data.categories || []); setCatCounts(r.data.counts || {}); }).catch(() => {});
    api.get('/marketplace/stats/summary').then(r => setStats(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    const params = new URLSearchParams();
    if (catFilter) params.set('category', catFilter);
    if (search) params.set('search', search);
    api.get(`/marketplace?${params}`).then(r => { setConnectors(r.data.connectors || []); setTotal(r.data.total || 0); }).catch(() => {});
  }, [catFilter, search]);

  const installConnector = async (id) => {
    await api.post(`/marketplace/${id}/install`);
    const { data } = await api.get(`/marketplace/${id}`);
    setSelected(data);
    setConnectors(prev => prev.map(c => c.id === id ? { ...c, installs: (c.installs || 0) + 1 } : c));
  };

  return (
    <div data-testid="marketplace" className="flex gap-0 h-full -m-6">
      {/* Left — Categories & Stats */}
      <div className="w-60 border-r flex flex-col flex-shrink-0 overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }}>
        <div className="px-4 py-3 border-b" style={{ borderColor: '#272E3B' }}>
          <h2 className="font-heading text-sm font-semibold flex items-center gap-2" style={{ color: '#E8ECF1' }}>
            <Storefront size={16} style={{ color: '#00D4AA' }} /> Marketplace
          </h2>
        </div>
        {stats && (
          <div className="px-4 py-3 border-b space-y-2" style={{ borderColor: '#272E3B' }}>
            <div className="flex justify-between text-xs"><span style={{ color: '#6B7A90' }}>Connectors</span><span className="font-mono" style={{ color: '#E8ECF1' }}>{stats.total}</span></div>
            <div className="flex justify-between text-xs"><span style={{ color: '#6B7A90' }}>Certified</span><span className="font-mono" style={{ color: '#00D4AA' }}>{stats.certified}</span></div>
            <div className="flex justify-between text-xs"><span style={{ color: '#6B7A90' }}>Free</span><span className="font-mono" style={{ color: '#00D4AA' }}>{stats.free}</span></div>
            <div className="flex justify-between text-xs"><span style={{ color: '#6B7A90' }}>Vendors</span><span className="font-mono" style={{ color: '#E8ECF1' }}>{stats.vendors}</span></div>
          </div>
        )}
        <div className="px-4 py-2 text-[10px] uppercase tracking-wider font-medium" style={{ color: '#6B7A90' }}>Categories</div>
        <div className="flex-1 overflow-y-auto px-2">
          <button data-testid="cat-all" onClick={() => setCatFilter('')} className="w-full text-left px-3 py-2 rounded text-xs mb-0.5 transition-colors"
            style={{ background: !catFilter ? 'rgba(0,212,170,0.1)' : 'transparent', color: !catFilter ? '#00D4AA' : '#A3AEBE' }}>
            All ({total})
          </button>
          {categories.map((c, i) => (
            <button key={c} data-testid={`cat-${c.toLowerCase().replace(/\s+/g, '-')}`} onClick={() => setCatFilter(c)}
              className="w-full text-left px-3 py-2 rounded text-xs mb-0.5 transition-colors flex justify-between"
              style={{ background: catFilter === c ? 'rgba(0,212,170,0.1)' : 'transparent', color: catFilter === c ? '#00D4AA' : '#A3AEBE' }}>
              <span>{c}</span><span className="font-mono" style={{ color: '#6B7A90' }}>{catCounts[c] || 0}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Center — Connector Grid */}
      <div className="flex-1 flex flex-col overflow-hidden" style={{ background: '#0A0C10' }}>
        <div className="flex items-center gap-3 px-6 py-3 border-b" style={{ borderColor: '#272E3B', background: '#12151C' }}>
          <div className="relative flex-1">
            <MagnifyingGlass size={14} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: '#6B7A90' }} />
            <input data-testid="marketplace-search" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search connectors, vendors..."
              className="w-full pl-9 pr-4 py-2 rounded text-sm outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }} />
          </div>
          <span className="text-xs font-mono" style={{ color: '#6B7A90' }}>{total} results</span>
        </div>
        <div className="flex-1 overflow-y-auto p-6">
          <div className="grid grid-cols-2 gap-4" data-testid="marketplace-grid">
            {connectors.map(c => (
              <button key={c.id} data-testid={`mkt-item-${c.id}`} onClick={() => setSelected(c)}
                className="rounded border p-4 text-left transition-all duration-150 hover:-translate-y-[1px]"
                style={{ background: selected?.id === c.id ? 'rgba(0,212,170,0.04)' : '#12151C', borderColor: selected?.id === c.id ? '#00D4AA40' : '#272E3B' }}>
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <div className="text-sm font-medium flex items-center gap-2" style={{ color: '#E8ECF1' }}>
                      {c.name}
                      {c.certified && <ShieldCheck size={14} weight="fill" style={{ color: '#00D4AA' }} />}
                    </div>
                    <div className="text-[10px] font-mono mt-0.5" style={{ color: '#6B7A90' }}>by {c.vendor_name} {c.vendor_verified && '(verified)'}</div>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded" style={{ background: `${PRICE_COLORS[c.price_model]}20`, color: PRICE_COLORS[c.price_model] }}>
                    {c.price_model === 'free' ? 'Free' : `$${c.price}/${c.price_model === 'per_device' ? 'device' : c.price_model === 'subscription' ? 'mo' : 'once'}`}
                  </span>
                </div>
                <p className="text-xs mb-3 line-clamp-2" style={{ color: '#A3AEBE' }}>{c.description}</p>
                <div className="flex items-center gap-3 text-[10px] font-mono">
                  <span className="flex items-center gap-1" style={{ color: '#F5A623' }}><Star size={12} weight="fill" /> {c.rating}</span>
                  <span style={{ color: '#6B7A90' }}>{c.reviews} reviews</span>
                  <span style={{ color: '#6B7A90' }}><Download size={10} className="inline" /> {c.installs}</span>
                  <span className="px-1.5 py-0.5 rounded" style={{ background: c.status === 'published' ? 'rgba(0,212,170,0.1)' : 'rgba(245,166,35,0.1)', color: c.status === 'published' ? '#00D4AA' : '#F5A623' }}>{c.status}</span>
                </div>
                <div className="flex flex-wrap gap-1 mt-2">
                  {c.tags?.slice(0, 4).map(t => (
                    <span key={t} className="text-[9px] px-1.5 py-0.5 rounded" style={{ background: '#1A1E2A', color: '#6B7A90' }}>{t}</span>
                  ))}
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Right — Detail */}
      {selected && (
        <div className="w-80 border-l flex-shrink-0 overflow-y-auto" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="marketplace-detail">
          <div className="p-4 border-b" style={{ borderColor: '#272E3B' }}>
            <h3 className="font-heading text-base font-semibold" style={{ color: '#E8ECF1' }}>{selected.name}</h3>
            <div className="text-xs mt-1" style={{ color: '#6B7A90' }}>by {selected.vendor_name}</div>
            <div className="flex items-center gap-2 mt-2">
              {selected.certified && <span className="flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded" style={{ background: 'rgba(0,212,170,0.1)', color: '#00D4AA' }}><ShieldCheck size={12} /> Certified</span>}
              <span className="text-[10px] font-mono flex items-center gap-1" style={{ color: '#F5A623' }}><Star size={12} weight="fill" /> {selected.rating} ({selected.reviews})</span>
            </div>
          </div>
          <div className="p-4 space-y-4">
            <p className="text-xs" style={{ color: '#A3AEBE' }}>{selected.description}</p>
            <div className="grid grid-cols-2 gap-2">
              <div className="rounded border p-2" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
                <div className="text-[9px] uppercase tracking-wider" style={{ color: '#6B7A90' }}>Version</div>
                <div className="font-mono text-xs" style={{ color: '#E8ECF1' }}>{selected.version}</div>
              </div>
              <div className="rounded border p-2" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
                <div className="text-[9px] uppercase tracking-wider" style={{ color: '#6B7A90' }}>Installs</div>
                <div className="font-mono text-xs" style={{ color: '#E8ECF1' }}>{selected.installs}</div>
              </div>
              <div className="rounded border p-2" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
                <div className="text-[9px] uppercase tracking-wider" style={{ color: '#6B7A90' }}>Price</div>
                <div className="font-mono text-xs" style={{ color: PRICE_COLORS[selected.price_model] }}>{selected.price === 0 ? 'Free' : `$${selected.price}`}</div>
              </div>
              <div className="rounded border p-2" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
                <div className="text-[9px] uppercase tracking-wider" style={{ color: '#6B7A90' }}>Protocols</div>
                <div className="font-mono text-xs" style={{ color: '#E8ECF1' }}>{selected.protocol_support?.join(', ')}</div>
              </div>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider mb-2" style={{ color: '#6B7A90' }}>Tags</div>
              <div className="flex flex-wrap gap-1">{selected.tags?.map(t => <span key={t} className="text-[10px] px-2 py-0.5 rounded" style={{ background: '#1A1E2A', color: '#A3AEBE', border: '1px solid #272E3B' }}><Tag size={10} className="inline mr-1" />{t}</span>)}</div>
            </div>
            <button data-testid="install-connector-btn" onClick={() => installConnector(selected.id)} className="w-full py-2.5 rounded text-sm font-medium" style={{ background: '#00D4AA', color: '#0A0C10' }}>
              <Download size={16} className="inline mr-2" /> Install Connector
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
