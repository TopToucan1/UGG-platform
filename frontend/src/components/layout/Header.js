import { useAuth } from '@/contexts/AuthContext';
import { MagnifyingGlass, Bell, SignOut, User } from '@phosphor-icons/react';
import { useState, useEffect } from 'react';
import api from '@/lib/api';
import InfoTip from '@/components/InfoTip';

export default function Header() {
  const { user, logout } = useAuth();
  const [sites, setSites] = useState([]);
  const [selectedSite, setSelectedSite] = useState('all');
  const [showUserMenu, setShowUserMenu] = useState(false);

  useEffect(() => {
    api.get('/admin/sites').then(r => setSites(r.data.sites || [])).catch(() => {});
  }, []);

  return (
    <header
      data-testid="main-header"
      className="flex items-center justify-between h-14 px-6 border-b flex-shrink-0"
      style={{ background: '#12151C', borderColor: '#272E3B' }}
    >
      <div className="flex items-center gap-4">
        {/* Site selector */}
        <div className="flex items-center">
          <select
            data-testid="site-selector"
            value={selectedSite}
            onChange={e => setSelectedSite(e.target.value)}
            className="px-3 py-1.5 rounded text-sm outline-none"
            style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}
          >
            <option value="all">All Sites</option>
            {sites.map(s => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
          <InfoTip label="Site Selector" description="Filter everything in the app to a specific venue (bar, tavern, casino floor). Choose 'All Sites' to see your entire route at once. Applies to most pages that display device or session data." />
        </div>

        {/* Search */}
        <div className="relative flex items-center">
          <MagnifyingGlass size={16} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: '#6B7A90' }} />
          <input
            data-testid="global-search"
            type="text"
            placeholder="Search devices, events..."
            className="pl-9 pr-4 py-1.5 rounded text-sm outline-none w-64"
            style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}
          />
          <InfoTip label="Global Search" description="Quickly find a device by its ID or serial, or an event by keyword, from anywhere in the app." />
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Notifications */}
        <button data-testid="notifications-btn" className="relative p-2 rounded transition-colors" style={{ color: '#A3AEBE' }}>
          <Bell size={20} />
          <span className="absolute top-1 right-1 w-2 h-2 rounded-full" style={{ background: '#FF3B30' }} />
        </button>
        <InfoTip label="Notifications" description="Shows unread system notifications. A red dot means there is new activity — click to review." />

        {/* User menu */}
        <div className="relative flex items-center">
          <button
            data-testid="user-menu-btn"
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 px-3 py-1.5 rounded text-sm transition-colors"
            style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}
          >
            <User size={16} />
            <span>{user?.name || user?.email}</span>
            <span className="text-xs px-1.5 py-0.5 rounded" style={{ background: '#272E3B', color: '#00D4AA' }}>
              {user?.role}
            </span>
          </button>
          <InfoTip label="Your Account" description="Click to open your account menu and sign out. The badge shows your role (admin, operator, engineer, etc.) which controls what features you can access." />

          {showUserMenu && (
            <div
              className="absolute right-0 top-full mt-1 w-48 rounded border z-50 py-1"
              style={{ background: '#1A1E2A', borderColor: '#272E3B' }}
            >
              <button
                data-testid="logout-btn"
                onClick={logout}
                className="w-full flex items-center gap-2 px-4 py-2 text-sm transition-colors text-left"
                style={{ color: '#A3AEBE' }}
                onMouseEnter={e => e.target.style.background = '#272E3B'}
                onMouseLeave={e => e.target.style.background = 'transparent'}
              >
                <SignOut size={16} />
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
