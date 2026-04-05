import { Info } from '@phosphor-icons/react';
import * as TooltipPrimitive from '@radix-ui/react-tooltip';

/**
 * InfoTip — tiny info icon that shows a rich tooltip on hover or keyboard focus.
 * Self-contained (own Provider) so it can be dropped next to any element without
 * wrapping parent pages. Dark theme styled to match the app.
 *
 * Usage:
 *   <InfoTip label="Name of thing" description="What it does and how to use it." />
 *
 * Or just:
 *   <InfoTip description="Plain explanation." />
 *
 * Optional size prop (default 12). Keep it tiny per design.
 */
export default function InfoTip({ label, description, size = 12, side = 'top' }) {
  return (
    <TooltipPrimitive.Provider delayDuration={150}>
      <TooltipPrimitive.Root>
        <TooltipPrimitive.Trigger asChild>
          <button
            type="button"
            aria-label={label ? `Info: ${label}` : 'More info'}
            className="inline-flex items-center justify-center align-middle ml-1 rounded-full transition-colors focus:outline-none focus:ring-1"
            style={{
              color: '#6B7A90',
              width: size + 4,
              height: size + 4,
              cursor: 'help',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = '#00D4AA')}
            onMouseLeave={(e) => (e.currentTarget.style.color = '#6B7A90')}
            onClick={(e) => e.stopPropagation()}
          >
            <Info size={size} weight="fill" />
          </button>
        </TooltipPrimitive.Trigger>
        <TooltipPrimitive.Portal>
          <TooltipPrimitive.Content
            side={side}
            sideOffset={6}
            collisionPadding={12}
            className="z-[60] max-w-xs rounded border px-3 py-2 text-[11px] leading-relaxed shadow-lg animate-in fade-in-0 zoom-in-95"
            style={{
              background: '#0A0C10',
              borderColor: '#00D4AA',
              color: '#E8ECF1',
            }}
          >
            {label && (
              <div className="font-medium mb-1" style={{ color: '#00D4AA' }}>
                {label}
              </div>
            )}
            <div style={{ color: '#A3AEBE' }}>{description}</div>
            <TooltipPrimitive.Arrow style={{ fill: '#00D4AA' }} width={10} height={5} />
          </TooltipPrimitive.Content>
        </TooltipPrimitive.Portal>
      </TooltipPrimitive.Root>
    </TooltipPrimitive.Provider>
  );
}
