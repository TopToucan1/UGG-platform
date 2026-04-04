import { NavLink, useLocation } from 'react-router-dom';
import {
  ChartBar, Desktop, Plugs, Robot, Flask,
  ListMagnifyingGlass, Bell, ChatCircleDots, GearSix,
  Cpu, CaretLeft, CaretRight, CurrencyDollar, Users,
  Storefront, Trophy, FileArrowDown, Monitor, Cube, MapPin, Scales,
  NavigationArrow, ShieldCheck, MagnifyingGlass, WifiHigh, UsersThree, BookOpen, Sparkle, Crown
} from '@phosphor-icons/react';
import { useState } from 'react';

const navItems = [
  { path: '/', label: 'Mission Control', icon: ChartBar },
  { path: '/command-center', label: 'Command Center', icon: Monitor },
  { path: '/devices', label: 'Device Fleet', icon: Desktop },
  { path: '/map', label: 'Route Map', icon: NavigationArrow },
  { path: '/route-ops', label: 'Route Operations', icon: MapPin },
  { path: '/regulatory', label: 'Regulatory', icon: Scales },
  { path: '/financial', label: 'Financial', icon: CurrencyDollar },
  { path: '/players', label: 'Player Sessions', icon: Users },
  { path: '/jackpots', label: 'Jackpots', icon: Trophy },
  { path: '/connectors', label: 'Connectors', icon: Plugs },
  { path: '/marketplace', label: 'Marketplace', icon: Storefront },
  { path: '/content-lab', label: 'Content Lab', icon: Cube },
  { path: '/ai-studio', label: 'AI Studio', icon: Robot },
  { path: '/emulator', label: 'Emulator Lab', icon: Flask },
  { path: '/analyzer', label: 'Analyzer', icon: MagnifyingGlass },
  { path: '/proxy', label: 'Proxy Mode', icon: WifiHigh },
  { path: '/fleet', label: 'Fleet Simulator', icon: UsersThree },
  { path: '/certification', label: 'Certification', icon: ShieldCheck },
  { path: '/compliance', label: 'Compliance Ref', icon: BookOpen },
  { path: '/ai-analytics', label: 'AI Analytics', icon: Sparkle },
  { path: '/pirs', label: 'PIRS Rewards', icon: Crown },
  { path: '/digital-twin', label: 'Digital Twin', icon: Cpu },
  { path: '/audit', label: 'Audit Explorer', icon: ListMagnifyingGlass },
  { path: '/alerts', label: 'Exceptions', icon: Bell },
  { path: '/messages', label: 'Messages', icon: ChatCircleDots },
  { path: '/export', label: 'Export', icon: FileArrowDown },
  { path: '/hardware', label: 'Hardware', icon: Cpu },
  { path: '/docs', label: 'Documentation', icon: BookOpen },
  { path: '/settings', label: 'Settings', icon: GearSix },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  return (
    <aside
      data-testid="main-sidebar"
      className="flex flex-col h-full transition-all duration-200 border-r flex-shrink-0"
      style={{
        width: collapsed ? 64 : 240,
        background: '#12151C',
        borderColor: '#272E3B',
      }}
    >
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-4 h-14 border-b flex-shrink-0" style={{ borderColor: '#272E3B' }}>
        <div className="w-8 h-8 rounded flex items-center justify-center flex-shrink-0" style={{ background: '#00D4AA' }}>
          <Cpu size={18} weight="bold" color="#0A0C10" />
        </div>
        {!collapsed && (
          <span className="font-heading text-lg font-bold tracking-tight" style={{ color: '#E8ECF1' }}>
            UGG
          </span>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
        {navItems.map(({ path, label, icon: Icon }) => {
          const isActive = path === '/' ? location.pathname === '/' : location.pathname.startsWith(path);
          return (
            <NavLink
              key={path}
              to={path}
              data-testid={`nav-${label.toLowerCase().replace(/\s+/g, '-')}`}
              className="flex items-center gap-3 px-3 py-2 rounded text-sm transition-all duration-150"
              style={{
                background: isActive ? 'rgba(0,212,170,0.1)' : 'transparent',
                color: isActive ? '#00D4AA' : '#A3AEBE',
                fontWeight: isActive ? 600 : 400,
              }}
              title={collapsed ? label : undefined}
            >
              <Icon size={20} weight={isActive ? 'fill' : 'regular'} className="flex-shrink-0" />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          );
        })}
      </nav>

      {/* Collapse button */}
      <button
        data-testid="sidebar-collapse-btn"
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-center h-10 border-t transition-colors"
        style={{ borderColor: '#272E3B', color: '#6B7A90' }}
      >
        {collapsed ? <CaretRight size={16} /> : <CaretLeft size={16} />}
      </button>
    </aside>
  );
}
