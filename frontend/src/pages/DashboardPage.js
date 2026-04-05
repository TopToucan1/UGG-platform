import { useState, useEffect, useCallback, useRef } from 'react';
import api, { API_URL } from '@/lib/api';
import { Desktop, Warning, Queue, Lightning, SealCheck, WifiX, Wrench, XCircle } from '@phosphor-icons/react';
import Marquee from 'react-fast-marquee';
import { useNavigate } from 'react-router-dom';
import { AreaChart, Area, PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import InfoTip from '@/components/InfoTip';

const COLORS = { online: '#00D4AA', offline: '#FF3B30', error: '#FF3B30', maintenance: '#F5A623', info: '#007AFF', warning: '#F5A623', critical: '#FF3B30' };
const PIE_COLORS = ['#00D4AA', '#007AFF', '#F5A623', '#FF3B30', '#8B5CF6', '#EC4899', '#06B6D4'];

function SummaryCard({ title, icon: Icon, data, color, onClick, testId, info }) {
  return (
    <button data-testid={testId} onClick={onClick} className="rounded border p-4 text-left transition-all duration-150 hover:-translate-y-[1px]" style={{ background: '#12151C', borderColor: '#272E3B' }}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium uppercase tracking-wider flex items-center" style={{ color: '#6B7A90' }}>{title}{info && <InfoTip label={title} description={info} />}</span>
        <Icon size={20} style={{ color }} />
      </div>
      <div className="font-mono text-2xl font-bold" style={{ color: '#E8ECF1' }}>{data.main}</div>
      {data.sub && <div className="text-xs mt-1 font-mono" style={{ color: '#A3AEBE' }}>{data.sub}</div>}
    </button>
  );
}

function SeverityBadge({ severity }) {
  return (
    <span className="text-xs font-mono px-2 py-0.5 rounded" style={{ background: `${COLORS[severity] || '#6B7A90'}20`, color: COLORS[severity] || '#6B7A90' }}>
      {severity}
    </span>
  );
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded border px-3 py-2 text-xs" style={{ background: '#1A1E2A', borderColor: '#272E3B' }}>
      <div className="font-mono" style={{ color: '#E8ECF1' }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color }}>{p.name}: {p.value}</div>
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [devices, setDevices] = useState([]);
  const [events, setEvents] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [charts, setCharts] = useState(null);
  const [throughput, setThroughput] = useState([]);
  const [wsConnected, setWsConnected] = useState(false);
  const [liveCount, setLiveCount] = useState(0);
  const wsRef = useRef(null);
  const navigate = useNavigate();

  const fetchData = useCallback(async () => {
    try {
      const [sumRes, devRes, evtRes, alertRes, chartRes, tpRes] = await Promise.all([
        api.get('/dashboard/summary'),
        api.get('/dashboard/device-health?limit=60'),
        api.get('/dashboard/recent-events?limit=30'),
        api.get('/dashboard/recent-alerts?limit=15'),
        api.get('/dashboard/charts'),
        api.get('/dashboard/event-throughput'),
      ]);
      setSummary(sumRes.data);
      setDevices(devRes.data.devices || []);
      setEvents(evtRes.data.events || []);
      setAlerts(alertRes.data.alerts || []);
      setCharts(chartRes.data);
      setThroughput(tpRes.data.throughput || []);
    } catch (err) {
      console.error('Dashboard fetch error:', err);
    }
  }, []);

  // WebSocket connection for real-time events
  useEffect(() => {
    const wsUrl = API_URL.replace('https://', 'wss://').replace('http://', 'ws://');
    let ws;
    let reconnectTimer;

    const connect = () => {
      ws = new WebSocket(`${wsUrl}/api/events/ws`);
      wsRef.current = ws;

      ws.onopen = () => {
        setWsConnected(true);
      };

      ws.onmessage = (msg) => {
        try {
          const evt = JSON.parse(msg.data);
          evt._wsKey = `ws-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
          setEvents(prev => [evt, ...prev.filter(e => e.id !== evt.id)].slice(0, 50));
          setLiveCount(prev => prev + 1);
          // Update summary event count
          setSummary(prev => prev ? { ...prev, events: { ...prev.events, total: (prev.events.total || 0) + 1, throughput: (prev.events.throughput || 0) + 1 } } : prev);
        } catch {}
      };

      ws.onclose = () => {
        setWsConnected(false);
        reconnectTimer = setTimeout(connect, 3000);
      };

      ws.onerror = () => {
        ws.close();
      };
    };

    connect();

    return () => {
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (ws) ws.close();
    };
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const s = summary;

  return (
    <div data-testid="estate-dashboard" className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-2xl font-bold tracking-tight flex items-center" style={{ color: '#E8ECF1' }}>Estate Dashboard<InfoTip label="Estate Dashboard" description="Your daily starting point. Shows the overall health of every device on the floor, live events streaming in, and any alerts you should look at. Use this screen each morning and whenever something feels off." /></h1>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-xs font-mono" style={{ color: wsConnected ? '#00D4AA' : '#FF3B30' }}>
            <span className={`w-2 h-2 rounded-full ${wsConnected ? 'pulse-online' : ''}`} style={{ background: wsConnected ? '#00D4AA' : '#FF3B30' }} />
            {wsConnected ? `Live (${liveCount} new)` : 'Reconnecting...'}
          </span>
        </div>
      </div>

      {/* Summary Strip */}
      <div className="grid grid-cols-4 gap-4" data-testid="summary-strip">
        <SummaryCard testId="summary-devices" title="Total Devices" icon={Desktop} color="#00D4AA"
          info="Every slot or gaming machine registered on your floor. The smaller line shows how many are currently talking to us, offline, or throwing errors. Click to open the full device list."
          data={{ main: s?.devices?.total ?? '--', sub: `${s?.devices?.online ?? 0} online / ${s?.devices?.offline ?? 0} offline / ${s?.devices?.error ?? 0} error` }}
          onClick={() => navigate('/devices')} />
        <SummaryCard testId="summary-alerts" title="Active Alerts" icon={Warning} color="#FF3B30"
          info="Alerts that still need attention, broken down by how urgent they are. If the critical count is above zero, open this to see what needs fixing right now."
          data={{ main: s?.alerts?.active ?? '--', sub: `${s?.alerts?.critical ?? 0} critical / ${s?.alerts?.warning ?? 0} warning` }}
          onClick={() => navigate('/alerts')} />
        <SummaryCard testId="summary-commands" title="Command Queue" icon={Queue} color="#F5A623"
          info="Commands you or the system have sent to devices that haven't finished yet. A growing number here usually means devices are slow to respond — worth a look."
          data={{ main: s?.commands?.pending ?? '--', sub: 'pending & in-flight' }} />
        <SummaryCard testId="summary-events" title="Event Throughput" icon={Lightning} color="#007AFF"
          info="Total count of standardized events the platform has processed. Useful as a heartbeat — a flatline here means the pipeline stopped receiving data."
          data={{ main: s?.events?.total ?? '--', sub: 'total canonical events' }} />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-12 gap-4">
        {/* Event Volume Area Chart */}
        <div className="col-span-5 rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="event-volume-chart">
          <div className="text-[11px] uppercase tracking-wider mb-3 font-medium flex items-center" style={{ color: '#6B7A90' }}>Event Volume (24h)<InfoTip label="Event Volume (24h)" description="Number of events flowing in each hour for the last day. A sudden drop often means a connector has gone quiet; a spike usually means an incident is unfolding." /></div>
          <ResponsiveContainer width="100%" height={140}>
            <AreaChart data={charts?.hourly_event_volume || []}>
              <defs>
                <linearGradient id="eventGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00D4AA" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#00D4AA" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="hour" tick={{ fill: '#6B7A90', fontSize: 10 }} axisLine={false} tickLine={false} interval={3} />
              <YAxis tick={{ fill: '#6B7A90', fontSize: 10 }} axisLine={false} tickLine={false} width={30} />
              <Tooltip content={<ChartTooltip />} />
              <Area type="monotone" dataKey="events" stroke="#00D4AA" fill="url(#eventGrad)" strokeWidth={2} name="Events" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Protocol Distribution Pie */}
        <div className="col-span-3 rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="protocol-chart">
          <div className="text-[11px] uppercase tracking-wider mb-3 font-medium flex items-center" style={{ color: '#6B7A90' }}>Protocol Mix<InfoTip label="Protocol Mix" description="Shows which communication protocols (SAS, G2S, etc.) your devices are using. Handy for confirming a new connector is actually pulling its weight." /></div>
          <ResponsiveContainer width="100%" height={140}>
            <PieChart>
              <Pie data={charts?.protocol_distribution || []} cx="50%" cy="50%" innerRadius={35} outerRadius={55} dataKey="value" nameKey="name" stroke="none">
                {(charts?.protocol_distribution || []).map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
              </Pie>
              <Tooltip content={<ChartTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-3 mt-1">
            {(charts?.protocol_distribution || []).map((p, i) => (
              <span key={p.name} className="flex items-center gap-1 text-[10px] font-mono" style={{ color: '#A3AEBE' }}>
                <span className="w-2 h-2 rounded-sm" style={{ background: PIE_COLORS[i % PIE_COLORS.length] }} />
                {p.name} ({p.value})
              </span>
            ))}
          </div>
        </div>

        {/* Severity Bar Chart */}
        <div className="col-span-4 rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="severity-chart">
          <div className="text-[11px] uppercase tracking-wider mb-3 font-medium flex items-center" style={{ color: '#6B7A90' }}>Event Severity & Device Status<InfoTip label="Event Severity & Device Status" description="Left bars break recent events down by urgency. Right bars show how many devices are in each state. Check this for a fast read on whether the floor is calm or noisy." /></div>
          <div className="grid grid-cols-2 gap-3">
            <ResponsiveContainer width="100%" height={140}>
              <BarChart data={charts?.severity_distribution || []} barSize={20}>
                <XAxis dataKey="name" tick={{ fill: '#6B7A90', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#6B7A90', fontSize: 10 }} axisLine={false} tickLine={false} width={30} />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="value" name="Events" radius={[3, 3, 0, 0]}>
                  {(charts?.severity_distribution || []).map((entry, i) => {
                    const c = { Info: '#007AFF', Warning: '#F5A623', Critical: '#FF3B30' };
                    return <Cell key={i} fill={c[entry.name] || '#6B7A90'} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <ResponsiveContainer width="100%" height={140}>
              <BarChart data={charts?.device_status_distribution || []} barSize={20}>
                <XAxis dataKey="name" tick={{ fill: '#6B7A90', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#6B7A90', fontSize: 10 }} axisLine={false} tickLine={false} width={30} />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="value" name="Devices" radius={[3, 3, 0, 0]}>
                  {(charts?.device_status_distribution || []).map((entry, i) => {
                    const c = { Online: '#00D4AA', Offline: '#FF3B30', Error: '#FF3B30', Maintenance: '#F5A623' };
                    return <Cell key={i} fill={c[entry.name] || '#6B7A90'} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Main Content — Health Map + Live Feed */}
      <div className="grid grid-cols-12 gap-4" style={{ height: 'calc(100vh - 490px)' }}>
        {/* Device Health Map */}
        <div className="col-span-8 rounded border overflow-hidden flex flex-col" style={{ background: '#12151C', borderColor: '#272E3B' }}>
          <div className="flex items-center justify-between px-4 py-2.5 border-b" style={{ borderColor: '#272E3B' }}>
            <h2 className="font-heading text-sm font-semibold flex items-center" style={{ color: '#E8ECF1' }}>Device Health Map<InfoTip label="Device Health Map" description="A color-coded tile for every device on the floor. Green means online, red means offline or errored, amber means maintenance. Click any tile to open that device's full detail panel." /></h2>
            <div className="flex items-center gap-3 text-[10px]" style={{ color: '#6B7A90' }}>
              <span className="flex items-center gap-1"><SealCheck size={12} style={{ color: '#00D4AA' }} />Online</span>
              <span className="flex items-center gap-1"><WifiX size={12} style={{ color: '#FF3B30' }} />Offline</span>
              <span className="flex items-center gap-1"><XCircle size={12} style={{ color: '#FF3B30' }} />Error</span>
              <span className="flex items-center gap-1"><Wrench size={12} style={{ color: '#F5A623' }} />Maint</span>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            <div className="grid grid-cols-10 gap-1.5" data-testid="device-health-grid">
              {devices.map(d => (
                <button key={d.id} data-testid={`device-badge-${d.external_ref}`}
                  onClick={() => navigate(`/devices?selected=${d.id}`)}
                  className="rounded border p-1.5 text-center transition-all duration-150 hover:-translate-y-[1px]"
                  style={{ background: `${COLORS[d.status]}10`, borderColor: `${COLORS[d.status]}30` }}
                  title={`${d.external_ref} — ${d.manufacturer} ${d.model}`}>
                  <div className="font-mono text-[9px] font-semibold truncate" style={{ color: COLORS[d.status] }}>{d.external_ref}</div>
                  <div className="text-[8px] truncate" style={{ color: '#6B7A90' }}>{d.protocol_family}</div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Live Event Feed */}
        <div className="col-span-4 rounded border overflow-hidden flex flex-col" style={{ background: '#12151C', borderColor: '#272E3B' }}>
          <div className="flex items-center justify-between px-4 py-2.5 border-b" style={{ borderColor: '#272E3B' }}>
            <h2 className="font-heading text-sm font-semibold flex items-center" style={{ color: '#E8ECF1' }}>Live Event Feed<InfoTip label="Live Event Feed" description="Every event from every device as it arrives. Newest entries appear at the top. Great for spotting patterns — like multiple devices at the same bank all reporting errors within seconds of each other." /></h2>
            <span className={`w-2 h-2 rounded-full ${wsConnected ? 'pulse-online' : ''}`} style={{ background: wsConnected ? '#00D4AA' : '#FF3B30' }} />
          </div>
          <div className="flex-1 overflow-y-auto" data-testid="live-event-feed">
            {events.map((evt, i) => (
              <div key={evt.id} className={`px-3 py-1.5 border-b text-xs transition-colors hover:bg-white/[0.02] ${i === 0 ? 'animate-slide-in animate-fade-highlight' : ''}`} style={{ borderColor: '#272E3B10' }}>
                <div className="flex items-center justify-between mb-0.5">
                  <span className="font-mono text-[10px]" style={{ color: '#A3AEBE' }}>{new Date(evt.occurred_at).toLocaleTimeString()}</span>
                  <SeverityBadge severity={evt.severity} />
                </div>
                <div className="font-mono text-[11px] font-medium" style={{ color: '#E8ECF1' }}>{evt.event_type}</div>
                <div className="truncate text-[10px]" style={{ color: '#6B7A90' }}>
                  {evt.device_ref || devices.find(d => d.id === evt.device_id)?.external_ref || evt.device_id?.slice(0, 8)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Alert Ticker */}
      {alerts.length > 0 && (
        <div className="rounded border overflow-hidden" style={{ background: '#12151C', borderColor: '#272E3B' }} data-testid="alert-ticker">
          <Marquee speed={40} gradient={false} pauseOnHover>
            {alerts.map(a => (
              <span key={a.id} className="inline-flex items-center gap-2 px-6 py-2 font-mono text-xs cursor-pointer" onClick={() => navigate('/alerts')} style={{ color: COLORS[a.severity] }}>
                <span className="w-1.5 h-1.5 rounded-full" style={{ background: COLORS[a.severity] }} />
                {a.message}
              </span>
            ))}
          </Marquee>
        </div>
      )}
    </div>
  );
}
