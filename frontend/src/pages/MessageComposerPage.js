import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { ChatCircleDots, PaperPlaneTilt, Plus } from '@phosphor-icons/react';

export default function MessageComposerPage() {
  const [campaigns, setCampaigns] = useState([]);
  const [sites, setSites] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [content, setContent] = useState('');
  const [targetSites, setTargetSites] = useState([]);
  const [deviceCount, setDeviceCount] = useState(0);

  useEffect(() => {
    api.get('/messages').then(r => setCampaigns(r.data.campaigns || [])).catch(() => {});
    api.get('/admin/sites').then(r => setSites(r.data.sites || [])).catch(() => {});
  }, []);

  const createCampaign = async () => {
    try {
      const { data } = await api.post('/messages', { name, content, target_sites: targetSites, target_device_count: deviceCount || 30 });
      setCampaigns([data, ...campaigns]);
      setShowCreate(false);
      setName(''); setContent('');
    } catch (err) { console.error(err); }
  };

  const sendCampaign = async (id) => {
    try {
      await api.post(`/messages/${id}/send`);
      const { data } = await api.get('/messages');
      setCampaigns(data.campaigns || []);
    } catch (err) { console.error(err); }
  };

  const statusColors = { draft: '#6B7A90', scheduled: '#F5A623', delivered: '#00D4AA', failed: '#FF3B30' };

  return (
    <div data-testid="message-composer" className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-2xl font-bold tracking-tight flex items-center gap-3" style={{ color: '#E8ECF1' }}>
          <ChatCircleDots size={24} style={{ color: '#007AFF' }} /> Message Composer
        </h1>
        <button data-testid="new-campaign-btn" onClick={() => setShowCreate(true)} className="flex items-center gap-2 px-4 py-2 rounded text-sm font-medium" style={{ background: '#00D4AA', color: '#0A0C10' }}>
          <Plus size={16} /> New Campaign
        </button>
      </div>

      {showCreate && (
        <div className="rounded border p-6 space-y-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
          <h3 className="font-heading text-lg font-semibold" style={{ color: '#E8ECF1' }}>Create Campaign</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-[11px] uppercase tracking-wider mb-1.5" style={{ color: '#6B7A90' }}>Campaign Name</label>
              <input data-testid="campaign-name" value={name} onChange={e => setName(e.target.value)} className="w-full px-3 py-2.5 rounded text-sm outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }} />
            </div>
            <div>
              <label className="block text-[11px] uppercase tracking-wider mb-1.5" style={{ color: '#6B7A90' }}>Target Device Count</label>
              <input data-testid="campaign-device-count" type="number" value={deviceCount} onChange={e => setDeviceCount(parseInt(e.target.value) || 0)} className="w-full px-3 py-2.5 rounded text-sm outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }} />
            </div>
          </div>
          <div>
            <label className="block text-[11px] uppercase tracking-wider mb-1.5" style={{ color: '#6B7A90' }}>Message Content</label>
            <textarea data-testid="campaign-content" value={content} onChange={e => setContent(e.target.value)} rows={3} className="w-full px-3 py-2.5 rounded text-sm outline-none resize-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }} />
          </div>
          <div className="flex gap-2">
            <button data-testid="create-campaign-submit" onClick={createCampaign} className="px-4 py-2 rounded text-sm font-medium" style={{ background: '#00D4AA', color: '#0A0C10' }}>Create</button>
            <button onClick={() => setShowCreate(false)} className="px-4 py-2 rounded text-sm" style={{ color: '#6B7A90' }}>Cancel</button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {campaigns.map(c => (
          <div key={c.id} data-testid={`campaign-row-${c.id}`} className="rounded border px-4 py-3 flex items-center gap-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
            <ChatCircleDots size={18} style={{ color: statusColors[c.status] }} />
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium" style={{ color: '#E8ECF1' }}>{c.name}</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded capitalize" style={{ background: `${statusColors[c.status]}20`, color: statusColors[c.status] }}>{c.status}</span>
              </div>
              <div className="text-xs mt-0.5" style={{ color: '#A3AEBE' }}>{c.content}</div>
              <div className="text-[10px] font-mono mt-1" style={{ color: '#6B7A90' }}>
                Target: {c.target_device_count} devices | Delivered: {c.delivered_count} | Failed: {c.failed_count}
              </div>
            </div>
            {c.status === 'draft' && (
              <button data-testid={`send-campaign-${c.id}`} onClick={() => sendCampaign(c.id)} className="flex items-center gap-1 px-3 py-1.5 rounded text-xs font-medium" style={{ background: '#00D4AA', color: '#0A0C10' }}>
                <PaperPlaneTilt size={14} /> Send
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
