import { useState, useEffect, useCallback, useRef } from 'react';
import api from '@/lib/api';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { MapPin, Desktop, Warning, CurrencyDollar, MagnifyingGlass, X, CaretRight, Globe, Mountains } from '@phosphor-icons/react';
import { useNavigate } from 'react-router-dom';

mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_TOKEN;

const STATUS_C = { healthy: '#00D97E', degraded: '#FFB800', critical: '#FF3B3B' };

export default function RouteMapPage() {
  const [venues, setVenues] = useState([]);
  const [summary, setSummary] = useState(null);
  const [selected, setSelected] = useState(null);
  const [venueDetail, setVenueDetail] = useState(null);
  const [search, setSearch] = useState('');
  const [mapStyle, setMapStyle] = useState('dark');
  const mapContainer = useRef(null);
  const mapRef = useRef(null);
  const markersRef = useRef([]);
  const navigate = useNavigate();

  const STYLES = {
    dark: 'mapbox://styles/mapbox/dark-v11',
    satellite: 'mapbox://styles/mapbox/satellite-streets-v12',
    streets: 'mapbox://styles/mapbox/streets-v12',
  };

  const fetchData = useCallback(async () => {
    const { data } = await api.get('/route-map/venues');
    setVenues(data.venues || []);
    setSummary(data.estate_summary);
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Initialize Mapbox
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;
    const map = new mapboxgl.Map({
      container: mapContainer.current,
      style: STYLES[mapStyle],
      center: [-117.5, 37.8],
      zoom: 5.5,
      attributionControl: false,
    });
    map.addControl(new mapboxgl.NavigationControl({ showCompass: false }), 'top-right');
    mapRef.current = map;
    return () => { map.remove(); mapRef.current = null; };
  }, []);

  // Switch map style
  useEffect(() => {
    if (!mapRef.current) return;
    mapRef.current.setStyle(STYLES[mapStyle]);
    // Re-add markers after style load
    mapRef.current.once('style.load', () => addMarkers(venues));
  }, [mapStyle]);

  // Add/update markers when venues change
  useEffect(() => {
    if (!mapRef.current || !venues.length) return;
    // Wait for style to be loaded
    if (mapRef.current.isStyleLoaded()) {
      addMarkers(venues);
      fitBounds(venues);
    } else {
      mapRef.current.once('style.load', () => {
        addMarkers(venues);
        fitBounds(venues);
      });
    }
  }, [venues]);

  const addMarkers = (venueList) => {
    // Clear old markers
    markersRef.current.forEach(m => m.remove());
    markersRef.current = [];
    if (!mapRef.current) return;

    venueList.forEach(v => {
      const color = STATUS_C[v.status] || '#4A6080';
      const size = Math.max(14, Math.min(v.device_count * 4, 36));

      const el = document.createElement('div');
      el.style.width = `${size}px`;
      el.style.height = `${size}px`;
      el.style.borderRadius = '50%';
      el.style.background = color;
      el.style.opacity = '0.85';
      el.style.border = `2px solid ${color}`;
      el.style.boxShadow = `0 0 ${size/2}px ${color}60`;
      el.style.cursor = 'pointer';
      el.style.transition = 'transform 0.15s ease, box-shadow 0.15s ease';
      el.addEventListener('mouseenter', () => { el.style.transform = 'scale(1.3)'; el.style.boxShadow = `0 0 ${size}px ${color}90`; });
      el.addEventListener('mouseleave', () => { el.style.transform = 'scale(1)'; el.style.boxShadow = `0 0 ${size/2}px ${color}60`; });
      el.addEventListener('click', () => selectVenue(v));

      // Tooltip popup
      const popup = new mapboxgl.Popup({ offset: 15, closeButton: false, className: 'ugg-popup' })
        .setHTML(`
          <div style="background:#111827;color:#F0F4FF;padding:10px 14px;border-radius:8px;border:1px solid #1A2540;font-family:'IBM Plex Sans',sans-serif;min-width:200px">
            <div style="font-weight:700;font-size:14px;margin-bottom:4px">${v.name}</div>
            <div style="font-size:11px;color:#8BA3CC">${v.city}, ${v.county} County</div>
            <div style="display:flex;gap:12px;margin-top:8px;font-family:'JetBrains Mono',monospace;font-size:11px">
              <span style="color:${color}">${v.device_count} dev</span>
              <span style="color:#00D97E">${v.health_pct}%</span>
              <span style="color:#00B4D8">$${v.today_nor?.toLocaleString()}</span>
              ${v.exception_count > 0 ? `<span style="color:#FF3B3B">${v.exception_count} exc</span>` : ''}
            </div>
          </div>
        `);

      const marker = new mapboxgl.Marker({ element: el })
        .setLngLat([v.lng, v.lat])
        .setPopup(popup)
        .addTo(mapRef.current);

      markersRef.current.push(marker);
    });
  };

  const fitBounds = (venueList) => {
    if (!mapRef.current || !venueList.length) return;
    const bounds = new mapboxgl.LngLatBounds();
    venueList.forEach(v => bounds.extend([v.lng, v.lat]));
    mapRef.current.fitBounds(bounds, { padding: 60, maxZoom: 12 });
  };

  const selectVenue = async (v) => {
    setSelected(v);
    if (mapRef.current) {
      mapRef.current.flyTo({ center: [v.lng, v.lat], zoom: 12, duration: 1200 });
    }
    try {
      const { data } = await api.get(`/route-map/venues/${v.id}`);
      setVenueDetail(data);
    } catch {}
  };

  const flyToVenue = (v) => {
    selectVenue(v);
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
            <button key={v.id} data-testid={`venue-item-${v.id}`} onClick={() => flyToVenue(v)}
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

      {/* Center — Mapbox Map */}
      <div className="flex-1 relative" style={{ background: '#070B14' }}>
        <div ref={mapContainer} className="absolute inset-0" data-testid="mapbox-container" />

        {/* Map Style Toggle */}
        <div className="absolute top-4 left-4 z-10 flex rounded-lg overflow-hidden" style={{ border: '1px solid #1A2540', background: 'rgba(12,19,34,0.9)', backdropFilter: 'blur(8px)' }} data-testid="map-style-toggle">
          {[
            { id: 'dark', label: 'Dark', icon: Globe },
            { id: 'satellite', label: 'Satellite', icon: Mountains },
            { id: 'streets', label: 'Streets', icon: MapPin },
          ].map(s => (
            <button key={s.id} data-testid={`map-style-${s.id}`} onClick={() => setMapStyle(s.id)}
              className="flex items-center gap-1.5 px-3 py-2 text-[10px] font-medium uppercase tracking-wider transition-colors"
              style={{ background: mapStyle === s.id ? 'rgba(0,180,216,0.15)' : 'transparent', color: mapStyle === s.id ? '#00B4D8' : '#4A6080', borderRight: '1px solid #1A2540' }}>
              <s.icon size={14} /> {s.label}
            </button>
          ))}
        </div>

        {/* Estate Summary Bar */}
        {summary && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-10 flex items-center gap-6 px-6 py-2.5 rounded-lg" style={{ background: 'rgba(12,19,34,0.92)', border: '1px solid #1A2540', backdropFilter: 'blur(8px)' }}>
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
            <div className="flex items-center gap-3">
              <span className="w-3 h-3 rounded-full" style={{ background: STATUS_C[selected.status] }} />
              <span className="text-sm font-semibold" style={{ color: STATUS_C[selected.status] }}>{selected.health_pct}% Health</span>
              <span className="text-xs font-mono" style={{ color: '#4A6080' }}>{selected.county} County</span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {[
                { label: 'Devices', value: selected.device_count, color: '#F0F4FF' },
                { label: 'Online', value: selected.online_count, color: '#00D97E' },
                { label: 'Exceptions', value: selected.exception_count, color: selected.exception_count > 0 ? '#FF3B3B' : '#00D97E' },
              ].map(s => (
                <div key={s.label} className="rounded p-2.5" style={{ background: '#111827', border: '1px solid #1A2540' }}>
                  <div className="text-[9px] uppercase tracking-wider" style={{ color: '#4A6080' }}>{s.label}</div>
                  <div className="font-mono text-sm font-bold" style={{ color: s.color }}>{s.value}</div>
                </div>
              ))}
            </div>
            <div className="rounded p-3" style={{ background: '#111827', border: '1px solid #1A2540' }}>
              <div className="text-[9px] uppercase tracking-wider mb-1" style={{ color: '#4A6080' }}>Today's NOR</div>
              <div className="font-mono text-xl font-bold" style={{ color: '#00D97E' }}>{fmt(selected.today_nor)}</div>
              <div className="text-[10px] font-mono" style={{ color: '#4A6080' }}>Coin In: {fmt(selected.today_coin_in)}</div>
            </div>
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
