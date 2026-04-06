import { NavLink, useLocation } from 'react-router-dom';
import {
  ChartBar, Desktop, Plugs, Robot, Flask,
  ListMagnifyingGlass, Bell, ChatCircleDots, GearSix,
  Cpu, CaretLeft, CaretRight, CurrencyDollar, Users,
  Storefront, Trophy, FileArrowDown, Monitor, Cube, MapPin, Scales,
  NavigationArrow, ShieldCheck, MagnifyingGlass, WifiHigh, UsersThree, BookOpen, Sparkle, Crown,
  IdentificationCard, ClockCounterClockwise, Warning, Atom
} from '@phosphor-icons/react';
import * as TooltipPrimitive from '@radix-ui/react-tooltip';
import { useState } from 'react';

const navItems = [
  { path: '/', label: 'Mission Control', icon: ChartBar, tip: 'Main dashboard. Shows the health of your entire operation at a glance: device counts, active alerts, event throughput, and a real-time event feed. Your home base — start here every day.' },
  { path: '/command-center', label: 'Command Center', icon: Monitor, tip: 'Fullscreen operations view designed for wall-mounted displays in a control room. Shows live device status and alerts without the normal sidebar clutter.' },
  { path: '/devices', label: 'Device Fleet', icon: Desktop, tip: 'Full list of every EGM (Electronic Gaming Machine) on your route. Search, filter, and click into any machine to see detailed status, events, commands, and audit history.' },
  { path: '/map', label: 'Route Map', icon: NavigationArrow, tip: 'Geographic view of every venue on your route. See which sites are healthy and which need attention without having to drive out to them.' },
  { path: '/route-ops', label: 'Route Operations', icon: MapPin, tip: 'Day-to-day route operations: service tickets, meter collections, drop reconciliation, and tech visit scheduling across all your venues.' },
  { path: '/regulatory', label: 'Regulatory', icon: Scales, tip: 'State gaming commission reporting dashboard. Generate the monthly/quarterly filings your jurisdiction requires and track compliance status.' },
  { path: '/financial', label: 'Financial', icon: CurrencyDollar, tip: 'Revenue reporting: NOR (Net Operating Revenue), handle, drop, hold percentage, and profit/loss by site or device.' },
  { path: '/players', label: 'Player Sessions', icon: Users, tip: 'Legacy card-based player session view. For the new PIN-based tracking, use PIN Sessions below.' },
  { path: '/pin-players', label: 'PIN Players', icon: IdentificationCard, tip: 'Manage PIN-based player accounts. Create, edit, change PINs, or deactivate. No physical cards — players log in at EGMs by entering a 4–8 digit PIN.' },
  { path: '/pin-sessions', label: 'PIN Sessions', icon: ClockCounterClockwise, tip: 'Live and historical view of credit sessions (money layer) and PIN sessions (player layer). See who is playing right now and review recent activity.' },
  { path: '/session-anomalies', label: 'Session Anomalies', icon: Warning, tip: 'Automatic detection of suspicious behavior: money movement, bonus farming, PIN sharing, rapid cycling. Review HIGH severity flags daily.' },
  { path: '/flywheel', label: 'Engagement Engine', icon: Atom, tip: 'FlywheelOS: intelligent engagement engine that automatically scores next-best-actions and delivers targeted POC offers to EGMs. 11 rule families, multi-factor decision scoring, 6 background workers. Manage rules, view action queue, and monitor engine health.' },
  { path: '/jackpots', label: 'Jackpots', icon: Trophy, tip: 'Track handpay jackpots (W-2G taxable wins) and progressive jackpot status. Approve payouts and generate tax forms.' },
  { path: '/connectors', label: 'Connectors', icon: Plugs, tip: 'Configure protocol adapters (SAS serial, G2S HTTPS, S2S) that connect UGG to your EGM hardware. Usually set up once during installation.' },
  { path: '/marketplace', label: 'Marketplace', icon: Storefront, tip: 'Browse and provision game content: themes, math models, progressives. Push new games to your machines without physical service visits.' },
  { path: '/content-lab', label: 'Content Lab', icon: Cube, tip: 'Game content management workshop: upload, test, and stage game packages before deploying to the marketplace.' },
  { path: '/ai-studio', label: 'AI Studio', icon: Robot, tip: 'Configure the AI assistant and automation rules. Create prompts, train classifiers, and set up AI-driven alerts.' },
  { path: '/emulator', label: 'Emulator Lab', icon: Flask, tip: 'Virtual EGM simulator. Test protocol integrations and replay real device traffic without touching physical hardware.' },
  { path: '/analyzer', label: 'Analyzer', icon: MagnifyingGlass, tip: 'Deep dive into protocol traffic logs. Useful for technicians troubleshooting communication issues between a machine and the gateway.' },
  { path: '/proxy', label: 'Proxy Mode', icon: WifiHigh, tip: 'Configure UGG to run as a transparent proxy between existing systems and EGMs. Used for gradual migration from legacy platforms.' },
  { path: '/fleet', label: 'Fleet Simulator', icon: UsersThree, tip: 'Simulate large fleets of virtual devices for capacity testing and demos. No real hardware required.' },
  { path: '/certification', label: 'Certification', icon: ShieldCheck, tip: 'Submit builds for GLI/BMM lab certification (GLI-11, GLI-21, GLI-33). Track review status and sign-offs required before production deployment.' },
  { path: '/compliance', label: 'Compliance Ref', icon: BookOpen, tip: 'Reference library of gaming regulations and compliance rules organized by jurisdiction. Look up requirements for your state.' },
  { path: '/ai-analytics', label: 'AI Analytics', icon: Sparkle, tip: 'Machine-learning insights across your whole route: player behavior clustering, revenue prediction, anomaly trends, and optimization suggestions.' },
  { path: '/pirs', label: 'PIRS Rewards', icon: Crown, tip: 'Player Incentive & Rewards System. Configure loyalty tiers, bonus rules, and automated player rewards based on play behavior.' },
  { path: '/digital-twin', label: 'Digital Twin', icon: Cpu, tip: 'Real-time digital replica of every device: current meters, state, comms status, integrity check results. The source of truth for "what is this machine doing right now."' },
  { path: '/audit', label: 'Audit Explorer', icon: ListMagnifyingGlass, tip: 'Searchable audit trail: who changed what, when, and why. Required for regulatory investigations and internal accountability.' },
  { path: '/alerts', label: 'Exceptions', icon: Bell, tip: 'Active alerts needing attention: door open, tilt, handpay pending, integrity violations, offline devices. Triage and dispatch from here.' },
  { path: '/messages', label: 'Messages', icon: ChatCircleDots, tip: 'Send messages to EGM display screens (promos, service notices, player messages) directly from UGG to one device or a whole group.' },
  { path: '/export', label: 'Export', icon: FileArrowDown, tip: 'Generate and download reports in CSV, Excel, or PDF format. Includes tax forms, EFT payment files, and regulatory filings.' },
  { path: '/hardware', label: 'Hardware', icon: Cpu, tip: 'Physical device inventory: cabinets, bill validators, printers, button decks. Track serial numbers, firmware, and service history.' },
  { path: '/docs', label: 'Documentation', icon: BookOpen, tip: 'Step-by-step operator manual. Written in plain English for non-technical users. Use the search to find how-to articles on any feature.' },
  { path: '/settings', label: 'Settings', icon: GearSix, tip: 'Configure tenants, sites, users, and agents. Admin-level controls for the whole platform.' },
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
      <TooltipPrimitive.Provider delayDuration={250}>
        <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
          {navItems.map(({ path, label, icon: Icon, tip }) => {
            const isActive = path === '/' ? location.pathname === '/' : location.pathname.startsWith(path);
            return (
              <TooltipPrimitive.Root key={path}>
                <TooltipPrimitive.Trigger asChild>
                  <NavLink
                    to={path}
                    data-testid={`nav-${label.toLowerCase().replace(/\s+/g, '-')}`}
                    className="flex items-center gap-3 px-3 py-2 rounded text-sm transition-all duration-150"
                    style={{
                      background: isActive ? 'rgba(0,212,170,0.1)' : 'transparent',
                      color: isActive ? '#00D4AA' : '#A3AEBE',
                      fontWeight: isActive ? 600 : 400,
                    }}
                  >
                    <Icon size={20} weight={isActive ? 'fill' : 'regular'} className="flex-shrink-0" />
                    {!collapsed && <span>{label}</span>}
                  </NavLink>
                </TooltipPrimitive.Trigger>
                <TooltipPrimitive.Portal>
                  <TooltipPrimitive.Content
                    side="right"
                    sideOffset={8}
                    collisionPadding={12}
                    className="z-[60] max-w-xs rounded border px-3 py-2 text-[11px] leading-relaxed shadow-lg animate-in fade-in-0 zoom-in-95"
                    style={{ background: '#0A0C10', borderColor: '#00D4AA', color: '#E8ECF1' }}
                  >
                    <div className="font-medium mb-1" style={{ color: '#00D4AA' }}>{label}</div>
                    <div style={{ color: '#A3AEBE' }}>{tip}</div>
                    <TooltipPrimitive.Arrow style={{ fill: '#00D4AA' }} width={10} height={5} />
                  </TooltipPrimitive.Content>
                </TooltipPrimitive.Portal>
              </TooltipPrimitive.Root>
            );
          })}
        </nav>
      </TooltipPrimitive.Provider>

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
