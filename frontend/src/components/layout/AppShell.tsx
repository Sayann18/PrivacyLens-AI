import { useEffect, useState, type ReactNode } from 'react';
import { Outlet, useParams } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { HowItWorksModal } from '../overlays/HowItWorksModal';
import { SettingsModal } from '../overlays/SettingsModal';
import { SearchModal } from '../overlays/SearchModal';
import { repairConversationCollection, repairConversationStatuses, useConversations } from '../../lib/storage';

type ModalKind = 'how-it-works' | 'settings' | 'search' | null;

export function AppShell({ title: legacyTitle, children }: { title?: string; children?: ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [modal, setModal] = useState<ModalKind>(null);
  const { id } = useParams();
  const conversations = useConversations();
  const currentTitle = conversations.find(c => c.id === id)?.title;

  useEffect(() => { repairConversationCollection(); repairConversationStatuses(); }, []);

  return (
    <div className={`pl-shell ${collapsed ? 'pl-shell-collapsed' : ''}`}>
      <a href="#main-content" className="skip-link">Skip to main content</a>
      <Sidebar
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed(v => !v)}
        activeModal={modal}
        onOpenHowItWorks={() => setModal('how-it-works')}
        onOpenSettings={() => setModal('settings')}
        onOpenSearch={() => setModal('search')}
      />
      <div className="pl-main">
        <TopBar title={currentTitle || legacyTitle} onOpenMobileSidebar={() => setMobileOpen(true)} />
        <main id="main-content" className="pl-content">
          {children || <Outlet />}
        </main>
      </div>

      <HowItWorksModal open={modal === 'how-it-works'} onClose={() => setModal(null)} />
      <SettingsModal open={modal === 'settings'} onClose={() => setModal(null)} />
      <SearchModal open={modal === 'search'} onClose={() => setModal(null)} />
    </div>
  );
}
