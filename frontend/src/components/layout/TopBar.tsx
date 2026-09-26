import { Menu } from 'lucide-react';

export function TopBar({ title, onOpenMobileSidebar }: { title?: string; onOpenMobileSidebar: () => void }) {
  return (
    <header className="pl-topbar">
      <button className="mobile-menu icon-button" onClick={onOpenMobileSidebar} aria-label="Open menu">
        <Menu size={19} />
      </button>
      <div className="pl-topbar-title">{title}</div>
    </header>
  );
}
