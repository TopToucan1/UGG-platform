import { useState } from 'react';
import { FileArrowDown, FileCsv, Table, Receipt, Users, Desktop, ListMagnifyingGlass, Trophy, Lightning } from '@phosphor-icons/react';
import InfoTip from '@/components/InfoTip';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const REPORTS = [
  { id: 'financial', label: 'Financial Transactions', icon: Receipt, desc: 'Wagers, payouts, vouchers, jackpots, handpays', endpoint: '/api/export/financial/csv', filters: [{ key: 'event_type', label: 'Type', options: ['', 'wager', 'payout', 'voucher_in', 'voucher_out', 'bill_in', 'jackpot', 'bonus', 'handpay'] }] },
  { id: 'players', label: 'Player Sessions', icon: Users, desc: 'Session data with player info, financials, loyalty', endpoint: '/api/export/players/csv', filters: [{ key: 'status', label: 'Status', options: ['', 'active', 'completed'] }] },
  { id: 'devices', label: 'Device Inventory', icon: Desktop, desc: 'All devices with manufacturer, model, status, firmware', endpoint: '/api/export/devices/csv', filters: [] },
  { id: 'events', label: 'Canonical Events', icon: Lightning, desc: 'Event log with types, severity, payloads', endpoint: '/api/export/events/csv', filters: [{ key: 'severity', label: 'Severity', options: ['', 'info', 'warning', 'critical'] }] },
  { id: 'audit', label: 'Audit Trail', icon: ListMagnifyingGlass, desc: 'Immutable audit records with actor, action, evidence', endpoint: '/api/export/audit/csv', filters: [] },
  { id: 'jackpots', label: 'Progressive Jackpots', icon: Trophy, desc: 'Jackpot status, amounts, hit history, linked devices', endpoint: '/api/export/jackpots/csv', filters: [] },
];

export default function ExportPage() {
  const [downloading, setDownloading] = useState(null);
  const [filterValues, setFilterValues] = useState({});

  const downloadReport = async (report) => {
    setDownloading(report.id);
    try {
      const params = new URLSearchParams();
      report.filters?.forEach(f => {
        const val = filterValues[`${report.id}_${f.key}`];
        if (val) params.set(f.key, val);
      });
      const url = `${API_URL}${report.endpoint}?${params.toString()}`;
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', '');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      console.error(err);
    }
    setTimeout(() => setDownloading(null), 2000);
  };

  return (
    <div data-testid="export-page" className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-2xl font-bold tracking-tight flex items-center gap-3" style={{ color: '#E8ECF1' }}>
          <FileArrowDown size={24} style={{ color: '#007AFF' }} /> Export & Reports
          <InfoTip label="Export & Reports" description="Download raw CSV reports for any data domain on the platform. Use these for accounting, tax filings, compliance audits, or loading into spreadsheets for deeper analysis." />
        </h1>
      </div>

      <p className="text-sm max-w-2xl" style={{ color: '#A3AEBE' }}>
        Download CSV reports for any UGG data domain. Reports include all fields with optional filtering. Files are generated in real-time from live data.
      </p>

      <div className="grid grid-cols-2 gap-4" data-testid="export-grid">
        {REPORTS.map(r => (
          <div key={r.id} data-testid={`export-card-${r.id}`} className="rounded border p-5 transition-all hover:-translate-y-[1px]" style={{ background: '#12151C', borderColor: '#272E3B' }}>
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(0,122,255,0.1)' }}>
                <r.icon size={22} style={{ color: '#007AFF' }} />
              </div>
              <div className="flex-1">
                <h3 className="font-heading text-sm font-semibold mb-1 flex items-center" style={{ color: '#E8ECF1' }}>{r.label}
                  <InfoTip label={r.label} description={`Download a CSV of ${r.desc.toLowerCase()}. Use the filter dropdown to narrow the export, then click Download CSV.`} />
                </h3>
                <p className="text-xs mb-3" style={{ color: '#6B7A90' }}>{r.desc}</p>

                {r.filters.length > 0 && (
                  <div className="flex items-center gap-2 mb-3">
                    {r.filters.map(f => (
                      <select key={f.key} data-testid={`export-filter-${r.id}-${f.key}`}
                        value={filterValues[`${r.id}_${f.key}`] || ''}
                        onChange={e => setFilterValues(prev => ({ ...prev, [`${r.id}_${f.key}`]: e.target.value }))}
                        className="px-2 py-1.5 rounded text-xs outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}>
                        <option value="">All {f.label}s</option>
                        {f.options.filter(Boolean).map(o => <option key={o} value={o}>{o}</option>)}
                      </select>
                    ))}
                  </div>
                )}

                <button data-testid={`download-${r.id}`} onClick={() => downloadReport(r)} disabled={downloading === r.id}
                  className="flex items-center gap-2 px-4 py-2 rounded text-xs font-medium transition-colors disabled:opacity-50"
                  style={{ background: downloading === r.id ? 'rgba(0,212,170,0.2)' : 'rgba(0,122,255,0.1)', color: downloading === r.id ? '#00D4AA' : '#007AFF', border: '1px solid rgba(0,122,255,0.2)' }}>
                  <FileCsv size={16} />
                  {downloading === r.id ? 'Downloading...' : 'Download CSV'}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="rounded border p-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
        <div className="text-[11px] uppercase tracking-wider mb-2 font-medium" style={{ color: '#6B7A90' }}>Export Notes</div>
        <ul className="text-xs space-y-1" style={{ color: '#A3AEBE' }}>
          <li>- CSV files include all fields for the selected data domain</li>
          <li>- Maximum 5,000 records per export (adjust limit parameter for larger exports)</li>
          <li>- Reports are generated from live MongoDB data in real-time</li>
          <li>- All timestamps are in UTC format (ISO 8601)</li>
          <li>- Financial amounts are in USD with 2 decimal precision</li>
        </ul>
      </div>
    </div>
  );
}
