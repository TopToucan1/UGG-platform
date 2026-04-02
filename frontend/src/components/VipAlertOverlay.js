import { useState, useEffect, useRef } from 'react';
import { API_URL } from '@/lib/api';
import api from '@/lib/api';
import { Crown, Star, X, GameController, Clock, CurrencyDollar, UserCircle } from '@phosphor-icons/react';
import { motion, AnimatePresence } from 'framer-motion';

export default function VipAlertOverlay() {
  const [alerts, setAlerts] = useState([]);
  const [history, setHistory] = useState([]);
  const [showPanel, setShowPanel] = useState(false);
  const wsRef = useRef(null);

  // Fetch historical VIP alerts
  useEffect(() => {
    api.get('/events/vip-alerts?limit=20').then(r => setHistory(r.data.alerts || [])).catch(() => {});
  }, []);

  // WebSocket for real-time VIP alerts
  useEffect(() => {
    const wsUrl = API_URL.replace('https://', 'wss://').replace('http://', 'ws://');
    let ws;
    let reconnectTimer;

    const connect = () => {
      ws = new WebSocket(`${wsUrl}/api/events/ws/vip`);
      wsRef.current = ws;

      ws.onmessage = (msg) => {
        try {
          const alert = JSON.parse(msg.data);
          if (alert.type === 'vip_player_alert') {
            setAlerts(prev => [alert, ...prev].slice(0, 5));
            setHistory(prev => [alert, ...prev].slice(0, 30));
            // Auto-dismiss after 12s
            setTimeout(() => {
              setAlerts(prev => prev.filter(a => a.id !== alert.id));
            }, 12000);
          }
        } catch {}
      };

      ws.onclose = () => {
        reconnectTimer = setTimeout(connect, 5000);
      };
      ws.onerror = () => ws.close();
    };

    connect();
    return () => { if (reconnectTimer) clearTimeout(reconnectTimer); if (ws) ws.close(); };
  }, []);

  const dismissAlert = (id) => {
    setAlerts(prev => prev.filter(a => a.id !== id));
  };

  const TIER_BG = { Diamond: 'rgba(185,242,255,0.08)', Platinum: 'rgba(192,192,192,0.08)' };
  const TIER_BORDER = { Diamond: 'rgba(185,242,255,0.3)', Platinum: 'rgba(192,192,192,0.3)' };
  const TIER_TEXT = { Diamond: '#B9F2FF', Platinum: '#C0C0C0' };

  return (
    <>
      {/* Floating VIP Alert Toasts */}
      <div className="fixed top-16 right-6 z-50 space-y-2 w-96" data-testid="vip-alert-overlay">
        <AnimatePresence>
          {alerts.map(a => (
            <motion.div
              key={a.id}
              initial={{ opacity: 0, x: 100, scale: 0.95 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 100, scale: 0.95 }}
              transition={{ duration: 0.3 }}
              className="rounded-lg border p-4 shadow-lg"
              style={{ background: TIER_BG[a.player_tier] || '#12151C', borderColor: TIER_BORDER[a.player_tier] || '#272E3B', backdropFilter: 'blur(8px)' }}
              data-testid={`vip-toast-${a.id}`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Crown size={18} weight="fill" style={{ color: TIER_TEXT[a.player_tier] || '#FFD700' }} />
                  <span className="font-heading text-sm font-bold" style={{ color: TIER_TEXT[a.player_tier] || '#E8ECF1' }}>
                    VIP Alert
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded flex items-center gap-1" style={{ background: `${TIER_TEXT[a.player_tier]}20`, color: TIER_TEXT[a.player_tier] }}>
                    <Star size={10} weight="fill" /> {a.player_tier}
                  </span>
                </div>
                <button onClick={() => dismissAlert(a.id)} style={{ color: '#6B7A90' }}><X size={14} /></button>
              </div>
              <div className="text-sm font-medium mb-1" style={{ color: '#E8ECF1' }}>
                {a.player_name} just carded in
              </div>
              <div className="text-xs mb-2" style={{ color: '#A3AEBE' }}>
                at {a.device_ref}
              </div>
              <div className="flex items-center gap-3 text-[10px] font-mono">
                <span className="flex items-center gap-1" style={{ color: '#00D4AA' }}>
                  <CurrencyDollar size={10} /> ${(a.lifetime_value / 1000).toFixed(1)}k lifetime
                </span>
                <span className="flex items-center gap-1" style={{ color: '#6B7A90' }}>
                  <Clock size={10} /> {a.avg_session_minutes}min avg
                </span>
                <span style={{ color: '#6B7A90' }}>{a.total_visits} visits</span>
              </div>
              <div className="flex flex-wrap gap-1 mt-2">
                {a.preferred_games?.slice(0, 3).map(g => (
                  <span key={g} className="text-[9px] px-1.5 py-0.5 rounded flex items-center gap-0.5" style={{ background: '#1A1E2A', color: '#A3AEBE', border: '1px solid #272E3B' }}>
                    <GameController size={8} /> {g}
                  </span>
                ))}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* VIP History Panel Toggle */}
      <button
        data-testid="vip-panel-toggle"
        onClick={() => setShowPanel(!showPanel)}
        className="fixed bottom-6 left-64 z-40 flex items-center gap-2 px-4 py-2.5 rounded-full shadow-lg transition-all hover:scale-105"
        style={{ background: 'linear-gradient(135deg, #B9F2FF20, #FFD70020)', border: '1px solid #FFD70040', color: '#FFD700' }}
      >
        <Crown size={18} weight="fill" />
        <span className="text-xs font-semibold">VIP Alerts</span>
        {history.length > 0 && (
          <span className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold" style={{ background: '#FFD700', color: '#0A0C10' }}>
            {history.length}
          </span>
        )}
      </button>

      {/* VIP History Panel */}
      <AnimatePresence>
        {showPanel && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="fixed bottom-20 left-64 z-40 w-96 max-h-[70vh] rounded-lg border shadow-2xl flex flex-col overflow-hidden"
            style={{ background: '#12151C', borderColor: '#FFD70030' }}
            data-testid="vip-history-panel"
          >
            <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: '#272E3B' }}>
              <div className="flex items-center gap-2">
                <Crown size={16} weight="fill" style={{ color: '#FFD700' }} />
                <span className="font-heading text-sm font-semibold" style={{ color: '#E8ECF1' }}>VIP Player Activity</span>
              </div>
              <button onClick={() => setShowPanel(false)} style={{ color: '#6B7A90' }}><X size={16} /></button>
            </div>
            <div className="flex-1 overflow-y-auto">
              {history.length === 0 ? (
                <div className="p-8 text-center text-xs" style={{ color: '#6B7A90' }}>
                  <Crown size={32} className="mx-auto mb-2" style={{ color: '#272E3B' }} />
                  No VIP alerts yet — waiting for Platinum/Diamond members to card in
                </div>
              ) : (
                history.map(a => (
                  <div key={a.id} className="px-4 py-3 border-b hover:bg-white/[0.02]" style={{ borderColor: '#272E3B10' }}>
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <UserCircle size={16} style={{ color: TIER_TEXT[a.player_tier] || '#E8ECF1' }} />
                        <span className="text-xs font-medium" style={{ color: '#E8ECF1' }}>{a.player_name}</span>
                        <span className="text-[9px] font-mono px-1 py-0.5 rounded" style={{ background: `${TIER_TEXT[a.player_tier]}15`, color: TIER_TEXT[a.player_tier] }}>
                          {a.player_tier}
                        </span>
                      </div>
                      <span className="text-[10px] font-mono" style={{ color: '#6B7A90' }}>
                        {new Date(a.occurred_at).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="text-[10px] font-mono ml-6" style={{ color: '#6B7A90' }}>
                      {a.device_ref} | ${(a.lifetime_value / 1000).toFixed(1)}k lifetime | {a.total_visits} visits
                    </div>
                  </div>
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
