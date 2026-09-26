import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { Headphones, HelpCircle, PanelLeftClose, PanelLeftOpen, Plus, Search, Settings, X } from 'lucide-react';
import { newConversationId, useConversations } from '../../lib/storage';
import { RecentItem } from './RecentItem';

export function Sidebar({
  mobileOpen,
  onCloseMobile,
  collapsed,
  onToggleCollapse,
  activeModal,
  onOpenHowItWorks,
  onOpenSettings,
  onOpenSearch
}: {
  mobileOpen: boolean;
  onCloseMobile: () => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
  activeModal: 'how-it-works' | 'settings' | 'search' | null;
  onOpenHowItWorks: () => void;
  onOpenSettings: () => void;
  onOpenSearch: () => void;
}) {
  const conversations = useConversations();
  const [supportOpen, setSupportOpen] = useState(false);
  const navigate = useNavigate();
  const { id: activeId } = useParams();

  useEffect(() => {
    document.body.classList.toggle('sidebar-open', mobileOpen);
    const onEsc = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onCloseMobile();
        setSupportOpen(false);
      }
    };
    window.addEventListener('keydown', onEsc);
    return () => {
      document.body.classList.remove('sidebar-open');
      window.removeEventListener('keydown', onEsc);
    };
  }, [mobileOpen, onCloseMobile]);

  useEffect(() => {
    if (!supportOpen) return;
    const onPointerDown = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest('.pl-support-wrap')) setSupportOpen(false);
    };
    document.addEventListener('mousedown', onPointerDown);
    return () => document.removeEventListener('mousedown', onPointerDown);
  }, [supportOpen]);

  const startNewAnalysis = () => {
    onCloseMobile();
    navigate(`/c/${newConversationId()}`);
  };

  const handleDeleted = (deletedId: string) => {
    if (activeId === deletedId) navigate('/');
  };

  const pinned = conversations.filter((conversation) => conversation.pinned);
  const recent = conversations.filter((conversation) => !conversation.pinned).slice(0, 20);

  return (
    <>
      <div className={`pl-sidebar-backdrop ${mobileOpen ? 'visible' : ''}`} onClick={onCloseMobile} aria-hidden="true" />
      <aside className={`pl-sidebar ${mobileOpen ? 'open' : ''} ${collapsed ? 'collapsed' : ''}`} role="navigation" aria-label="Main navigation">
        <div className="pl-sidebar-head">
          <Link to="/" className="brand" onClick={onCloseMobile} aria-label="PrivacyLens AI home">
            {!collapsed && <>PrivacyLens <b>AI</b></>}
          </Link>
          {!collapsed && (
            <button className={`icon-button ${activeModal === 'search' ? 'active' : ''}`} onClick={onOpenSearch} aria-label="Search chats">
              <Search size={19} />
            </button>
          )}
          <button className="icon-button pl-collapse-btn" onClick={onToggleCollapse} aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}>
            {collapsed ? <PanelLeftOpen size={19} /> : <PanelLeftClose size={19} />}
          </button>
        </div>

        <button className="pl-new-analysis" onClick={startNewAnalysis} title={collapsed ? 'New Analysis' : undefined}>
          <Plus size={19} aria-hidden="true" />
          {!collapsed && <span>New Analysis</span>}
        </button>

        <nav className="pl-nav" aria-label="Sections">
          <button
            type="button"
            className={activeModal === 'how-it-works' ? 'active' : ''}
            onClick={() => { onCloseMobile(); onOpenHowItWorks(); }}
            title={collapsed ? 'How It Works' : undefined}
          >
            <HelpCircle size={19} aria-hidden="true" />
            {!collapsed && <span>How It Works</span>}
          </button>
        </nav>

        {!collapsed && (
          <div className="pl-recent">
            {pinned.length > 0 && (
              <>
                <small className="pl-recent-label">Pinned</small>
                <div className="pl-recent-list">
                  {pinned.map((conversation) => (
                    <RecentItem
                      key={conversation.id}
                      conversation={conversation}
                      active={conversation.id === activeId}
                      onClick={onCloseMobile}
                      onDeleted={handleDeleted}
                    />
                  ))}
                </div>
              </>
            )}
            <small className="pl-recent-label">Recents</small>
            {recent.length ? (
              <div className="pl-recent-list">
                {recent.map((conversation) => (
                  <RecentItem
                    key={conversation.id}
                    conversation={conversation}
                    active={conversation.id === activeId}
                    onClick={onCloseMobile}
                    onDeleted={handleDeleted}
                  />
                ))}
              </div>
            ) : (
              <p className="pl-recent-empty">Your recent analyses will appear here.</p>
            )}
          </div>
        )}

        <div className="pl-sidebar-foot">
          <div className="pl-support-wrap">
            <button
              type="button"
              className={`pl-settings-link pl-support-link ${supportOpen ? 'active' : ''}`}
              onClick={() => setSupportOpen(value => !value)}
              title={collapsed ? 'Contact Support' : undefined}
              aria-expanded={supportOpen}
              aria-controls="pl-support-popover"
            >
              <Headphones size={18} aria-hidden="true" />
              {!collapsed && <span>Contact Support</span>}
            </button>
            {supportOpen && (
              <div className={`pl-support-popover ${collapsed ? 'collapsed' : ''}`} id="pl-support-popover" role="dialog" aria-label="Contact Support">
                <div className="pl-support-popover-head">
                  <strong>Contact Support</strong>
                  <button type="button" className="pl-support-close" onClick={() => setSupportOpen(false)} aria-label="Close support">
                    <X size={15} aria-hidden="true" />
                  </button>
                </div>
                <p>For help or feedback, email</p>
                <a href="mailto:chakrabortysayan861@gmail.com">chakrabortysayan861@gmail.com</a>
              </div>
            )}
          </div>
          <button
            type="button"
            className={`pl-settings-link ${activeModal === 'settings' ? 'active' : ''}`}
            onClick={() => { onCloseMobile(); onOpenSettings(); }}
            title={collapsed ? 'Settings' : undefined}
          >
            <Settings size={19} aria-hidden="true" />
            {!collapsed && <span>Settings</span>}
          </button>
        </div>
      </aside>
    </>
  );
}
