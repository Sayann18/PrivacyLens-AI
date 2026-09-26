import { useRef } from 'react';
import { X } from 'lucide-react';
import { useDialogFocus } from './useDialogFocus';

export function Modal({
  open,
  onClose,
  title,
  leading,
  width = 'md',
  children
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  leading?: React.ReactNode;
  width?: 'sm' | 'md';
  children: React.ReactNode;
}) {
  const panelRef = useRef<HTMLDivElement>(null);
  useDialogFocus(open, onClose, panelRef);

  if (!open) return null;

  return (
    <div className="pl-modal-overlay" onMouseDown={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div
        className={`pl-modal-panel pl-modal-${width}`}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        ref={panelRef}
        tabIndex={-1}
      >
        <header className="pl-modal-head">
          <div className="pl-modal-head-left">
            {leading}
            <h2>{title}</h2>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </header>
        <div className="pl-modal-body">{children}</div>
      </div>
    </div>
  );
}
