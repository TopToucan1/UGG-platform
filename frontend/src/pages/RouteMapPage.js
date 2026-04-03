import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { MapPin, Desktop, Warning, CurrencyDollar, MagnifyingGlass, X, CaretRight } from '@phosphor-icons/react';
import { useNavigate } from 'react-router-dom';

const STATUS_C = { healthy: '#00D97E', degraded: '#FFB800', critical: '#FF3B3B' };

function FitBounds({ venues }) {
  const map = useMap();
  useEffect(() => {
    if (venues.length > 0) {
      const bounds = venues.map(v => [v.lat, v.lng]);
      map.fitBounds(bounds, { padding: [40, 40] });
    }
  }, [venues, map]);
  return null;
}

export default function RouteMapPage() {
  const [venues, setVenues] = useState([]);
  const [summary, setSummary] = useState(null);
  const [selected, setSelected] = useState(null);
  const [venueDetail, setVenueDetail] = useState(null);
  const [search, setSearch] = useState('');
  const navigate = useNavigate();

  const fetchData = useCallback(async () => {
    const { data } = await api.get('/route-map/venues');
    setVenues(data.venues || []);
    setSummary(data.estate_summary);
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const selectVenue = async (v) => {
    setSelected(v);
    try {
      const { data } = await api.get(`/route-map/venues/${v.id}`);
      setVenueDetail(data);
    } catch {}
  };

  const filtered = search ? venues.filter(v => v.name.toLowerCase().includes(search.toLowerCase()) || v.city.toLowerCase().includes(search.toLowerCase())) : venues;
  const fmt = (v) => v != null ? `$${Number(v).toLocaleString()}` : '--';

  return (
    <div data-testid="route-map" className="flex gap-0 h-full -m-6">
      {/* Left — Venue List */}
      <div className="w-72 border-r flex flex-col flex-shrink-0 overflow-hidden" style={{ background: '#0C1322', borderColor: '#1A2540' }}>
        <div className="px-4 py-3 border-b" style={{ borderColor: '#1A2540' }}>
          <h2 className="font-heading text-sm font-semibold flex items-center gap-2" style={{ color: '#F0F4FF' }}>
            <MapPin size={16} style={{ color: '#00B4D8' }} /> Route Map
          </h2>
          {summary && (
            <div className="text-[10px] font-mono mt-1" style={{ color: '#4A6080' }}>
              {summary.total_venues} venues | {summary.total_devices} devices | {summary.online_pct}% online
            </div>
          )}
        </div>
        <div className="px-3 py-2">
          <div className="relative">
            <MagnifyingGlass size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2" style={{ color: '#4A6080' }} />
            <input data-testid="venue-search" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search venues..."
              className="w-full pl-8 pr-3 py-2 rounded text-xs outline-none" style={{ background: '#111827', border: '1px solid #1A2540', color: '#F0F4FF' }} />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto" data-testid="venue-list">
          {filtered.map(v => (
            <button key={v.id} data-testid={`venue-item-${v.id}`} onClick={() => selectVenue(v)}
              className="w-full text-left px-4 py-2.5 border-b transition-colors" style={{ borderColor: '#1A254020', background: selected?.id === v.id ? 'rgba(0,180,216,0.06)' : 'transparent' }}>
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: STATUS_C[v.status] || '#4A6080' }} />
                <span className="text-xs font-medium truncate" style={{ color: '#F0F4FF' }}>{v.name}</span>
              </div>
              <div className="flex items-center gap-3 ml-4.5 mt-0.5 text-[10px] font-mono" style={{ color: '#4A6080' }}>
                <span>{v.device_count} dev</span>
                <span>{v.health_pct}%</span>
                <span style={{ color: '#00D97E' }}>{fmt(v.today_nor)}</span>
                {v.exception_count > 0 && <span style={{ color: '#FF3B3B' }}>{v.exception_count} exc</span>}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Center — Map */}
      <div className="flex-1 relative" style={{ background: '#070B14' }}>
        <MapContainer center={[37.8, -117.5]} zoom={6} className="h-full w-full" style={{ background: '#070B14' }}
          zoomControl={false} attributionControl={false}>
          <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
          <FitBounds venues={filtered} />
          {filtered.map(v => (
            <CircleMarker key={v.id} center={[v.lat, v.lng]}
              radius={Math.max(6, Math.min(v.device_count * 2, 18))}
              pathOptions={{ color: STATUS_C[v.status], fillColor: STATUS_C[v.status], fillOpacity: 0.6, weight: 2 }}
              eventHandlers={{ click: () => selectVenue(v) }}>
              <Popup>
                <div style={{ color: '#F0F4FF', background: '#111827', padding: '8px', borderRadius: '6px', minWidth: '180px' }}>
                  <div style={{ fontWeight: 600, fontSize: '13px' }}>{v.name}</div>
                  <div style={{ fontSize: '11px', color: '#8BA3CC', marginTop: '4px' }}>{v.city}, {v.county}</div>
                  <div style={{ fontSize: '11px', color: '#8BA3CC', marginTop: '2px' }}>{v.device_count} devices | {v.health_pct}% online | NOR: {fmt(v.today_nor)}</div>
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>

        {/* Estate Summary Bar */}
        {summary && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-[1000] flex items-center gap-6 px-6 py-2.5 rounded-lg" style={{ background: 'rgba(12,19,34,0.92)', border: '1px solid #1A2540', backdropFilter: 'blur(8px)' }}>
            <div className="text-center"><div className="text-[9px] uppercase tracking-widest" style={{ color: '#4A6080' }}>Venues</div><div className="font-mono text-sm font-bold" style={{ color: '#F0F4FF' }}>{summary.total_venues}</div></div>
            <div className="text-center"><div className="text-[9px] uppercase tracking-widest" style={{ color: '#4A6080' }}>Devices</div><div className="font-mono text-sm font-bold" style={{ color: '#00D97E' }}>{summary.total_devices}</div></div>
            <div className="text-center"><div className="text-[9px] uppercase tracking-widest" style={{ color: '#4A6080' }}>Online</div><div className="font-mono text-sm font-bold" style={{ color: '#00B4D8' }}>{summary.online_pct}%</div></div>
            <div className="text-center"><div className="text-[9px] uppercase tracking-widest" style={{ color: '#4A6080' }}>Today NOR</div><div className="font-mono text-sm font-bold" style={{ color: '#00D97E' }}>{fmt(summary.today_nor)}</div></div>
          </div>
        )}
      </div>

      {/* Right — Venue Detail */}
      {selected && (
        <div className="w-96 border-l flex-shrink-0 overflow-y-auto" style={{ background: '#0C1322', borderColor: '#1A2540' }} data-testid="venue-detail-panel">
          <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: '#1A2540' }}>
            <div>
              <h3 className="font-heading text-base font-semibold" style={{ color: '#F0F4FF' }}>{selected.name}</h3>
              <div className="text-xs mt-0.5" style={{ color: '#4A6080' }}>{selected.address}, {selected.city}, {selected.state}</div>
            </div>
            <button onClick={() => { setSelected(null); setVenueDetail(null); }} style={{ color: '#4A6080' }}><X size={18} /></button>
          </div>
          <div className="p-4 space-y-4">
            {/* Health */}
            <div className="flex items-center gap-3">
              <span className="w-3 h-3 rounded-full" style={{ background: STATUS_C[selected.status] }} />
              <span className="text-sm font-semibold" style={{ color: STATUS_C[selected.status] }}>{selected.health_pct}% Health</span>
              <span className="text-xs font-mono" style={{ color: '#4A6080' }}>{selected.county} County</span>
            </div>
            {/* Stats */}
            <div className="grid grid-cols-3 gap-2">
              <div className="rounded p-2.5" style={{ background: '#111827', border: '1px solid #1A2540' }}>
                <div className="text-[9px] uppercase tracking-wider" style={{ color: '#4A6080' }}>Devices</div>
                <div className="font-mono text-sm font-bold" style={{ color: '#F0F4FF' }}>{selected.device_count}</div>
              </div>
              <div className="rounded p-2.5" style={{ background: '#111827', border: '1px solid #1A2540' }}>
                <div className="text-[9px] uppercase tracking-wider" style={{ color: '#4A6080' }}>Online</div>
                <div className="font-mono text-sm font-bold" style={{ color: '#00D97E' }}>{selected.online_count}</div>
              </div>
              <div className="rounded p-2.5" style={{ background: '#111827', border: '1px solid #1A2540' }}>
                <div className="text-[9px] uppercase tracking-wider" style={{ color: '#4A6080' }}>Exceptions</div>
                <div className="font-mono text-sm font-bold" style={{ color: selected.exception_count > 0 ? '#FF3B3B' : '#00D97E' }}>{selected.exception_count}</div>
              </div>
            </div>
            <div className="rounded p-3" style={{ background: '#111827', border: '1px solid #1A2540' }}>
              <div className="text-[9px] uppercase tracking-wider mb-1" style={{ color: '#4A6080' }}>Today's NOR</div>
              <div className="font-mono text-xl font-bold" style={{ color: '#00D97E' }}>{fmt(selected.today_nor)}</div>
              <div className="text-[10px] font-mono" style={{ color: '#4A6080' }}>Coin In: {fmt(selected.today_coin_in)}</div>
            </div>
            {/* Devices in this venue */}
            {venueDetail?.devices?.length > 0 && (
              <div>
                <div className="text-[10px] uppercase tracking-wider mb-2 font-medium" style={{ color: '#4A6080' }}>Devices ({venueDetail.devices.length})</div>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {venueDetail.devices.map(d => (
                    <div key={d.id} className="flex items-center gap-2 px-2 py-1.5 rounded text-xs" style={{ background: '#111827' }}>
                      <span className="w-2 h-2 rounded-full" style={{ background: d.status === 'online' ? '#00D97E' : d.status === 'error' ? '#FF3B3B' : '#4A6080' }} />
                      <span className="font-mono" style={{ color: '#F0F4FF' }}>{d.external_ref}</span>
                      <span style={{ color: '#4A6080' }}>{d.manufacturer}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {/* Exceptions */}
            {venueDetail?.exceptions?.length > 0 && (
              <div>
                <div className="text-[10px] uppercase tracking-wider mb-2 font-medium" style={{ color: '#FF3B3B' }}>Active Exceptions ({venueDetail.exceptions.length})</div>
                <div className="space-y-1">
                  {venueDetail.exceptions.map(e => (
                    <div key={e.id} className="px-2 py-1.5 rounded text-[10px]" style={{ background: '#111827', borderLeft: `2px solid ${e.severity === 'CRITICAL' ? '#FF3B3B' : '#FFB800'}` }}>
                      <span className="font-mono" style={{ color: '#F0F4FF' }}>{e.device_ref}</span>
                      <span className="ml-2" style={{ color: '#8BA3CC' }}>{e.type?.replace(/_/g, ' ')}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <button data-testid="view-venue-devices" onClick={() => navigate(`/devices?search=${selected.name}`)}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded text-xs font-medium" style={{ background: '#00B4D8', color: '#070B14' }}>
              View Venue Devices <CaretRight size={14} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
