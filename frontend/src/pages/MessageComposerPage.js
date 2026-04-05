import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { ChatCircleDots, PaperPlaneTilt, Plus } from '@phosphor-icons/react';
import InfoTip from '@/components/InfoTip';

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
          <InfoTip label="Message Composer" description="Compose and send on-screen messages directly to EGMs — promotions, service notices, shift changes. Campaigns can target specific sites or the whole floor." />
        </h1>
        <button data-testid="new-campaign-btn" onClick={() => setShowCreate(true)} className="flex items-center gap-2 px-4 py-2 rounded text-sm font-medium" style={{ background: '#00D4AA', color: '#0A0C10' }}>
          <Plus size={16} /> New Campaign
        </button>
        <InfoTip description="Start a new draft campaign. You can edit and review before sending to machines." />
      </div>

      {showCreate && (
        <div className="rounded border p-6 space-y-4" style={{ background: '#12151C', borderColor: '#272E3B' }}>
          <h3 className="font-heading text-lg font-semibold flex items-center" style={{ color: '#E8ECF1' }}>Create Campaign<InfoTip description="Fill in the details below to draft a new message campaign. It starts as a draft and is only sent when you click Send." /></h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="flex items-center text-[11px] uppercase tracking-wider mb-1.5" style={{ color: '#6B7A90' }}>Campaign Name<InfoTip description="Internal label used to identify this campaign in the list. Not shown on machines." /></label>
              <input data-testid="campaign-name" value={name} onChange={e => setName(e.target.value)} className="w-full px-3 py-2.5 rounded text-sm outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }} />
            </div>
            <div>
              <label className="flex items-center text-[11px] uppercase tracking-wider mb-1.5" style={{ color: '#6B7A90' }}>Target Device Count<InfoTip description="How many EGMs this campaign should reach. Leave blank for the default batch size." /></label>
              <input data-testid="campaign-device-count" type="number" value={deviceCount} onChange={e => setDeviceCount(parseInt(e.target.value) || 0)} className="w-full px-3 py-2.5 rounded text-sm outline-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }} />
            </div>
          </div>
          <div>
            <label className="flex items-center text-[11px] uppercase tracking-wider mb-1.5" style={{ color: '#6B7A90' }}>Message Content<InfoTip description="The actual text that will appear on the EGM screen. Keep it short — machines have limited space." /></label>
            <textarea data-testid="campaign-content" value={content} onChange={e => setContent(e.target.value)} rows={3} className="w-full px-3 py-2.5 rounded text-sm outline-none resize-none" style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }} />
          </div>
          <div className="flex gap-2">
            <button data-testid="create-campaign-submit" onClick={createCampaign} className="px-4 py-2 rounded text-sm font-medium" style={{ background: '#00D4AA', color: '#0A0C10' }}>Create</button>
            <InfoTip description="Save this as a draft campaign. It will not be sent until you click Send." />
            <button onClick={() => setShowCreate(false)} className="px-4 py-2 rounded text-sm" style={{ color: '#6B7A90' }}>Cancel</button>
            <InfoTip description="Discard your draft and close the form." />
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
                <InfoTip label="Campaign Status" description="Draft = saved but not sent. Scheduled = queued for delivery. Delivered = successfully shown on the target machines. Failed = could not be delivered." />
              </div>
              <div className="text-xs mt-0.5" style={{ color: '#A3AEBE' }}>{c.content}</div>
              <div className="text-[10px] font-mono mt-1" style={{ color: '#6B7A90' }}>
                Target: {c.target_device_count} devices | Delivered: {c.delivered_count} | Failed: {c.failed_count}
              </div>
            </div>
            {c.status === 'draft' && (
              <>
              <button data-testid={`send-campaign-${c.id}`} onClick={() => sendCampaign(c.id)} className="flex items-center gap-1 px-3 py-1.5 rounded text-xs font-medium" style={{ background: '#00D4AA', color: '#0A0C10' }}>
                <PaperPlaneTilt size={14} /> Send
              </button>
              <InfoTip description="Deliver this draft campaign to the targeted EGMs right now. Cannot be undone once sent." />
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
