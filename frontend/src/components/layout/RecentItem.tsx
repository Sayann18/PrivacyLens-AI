import { useEffect, useRef, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { MoreHorizontal, Pencil, Pin, PinOff, Trash2 } from 'lucide-react';
import { deleteConversation, renameConversation, setConversationPinned } from '../../lib/storage';
import type { Conversation } from '../../lib/types';

export function RecentItem({
  conversation,
  active,
  onClick,
  onDeleted
}: {
  conversation: Conversation;
  active: boolean;
  onClick?: () => void;
  onDeleted: (id: string) => void;
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [renaming, setRenaming] = useState(false);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [title, setTitle] = useState(conversation.title);
  const ref = useRef<HTMLDivElement>(null);
  const menuBtnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => { setTitle(conversation.title); }, [conversation.title]);

  useEffect(() => {
    if (!menuOpen && !confirmingDelete) return;
    const onDocClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) { setMenuOpen(false); setConfirmingDelete(false); }
    };
    const onEsc = (e: KeyboardEvent) => { if (e.key === 'Escape') { setMenuOpen(false); setConfirmingDelete(false); menuBtnRef.current?.focus(); } };
    document.addEventListener('mousedown', onDocClick);
    window.addEventListener('keydown', onEsc);
    return () => {
      document.removeEventListener('mousedown', onDocClick);
      window.removeEventListener('keydown', onEsc);
    };
  }, [menuOpen, confirmingDelete]);

  const commitRename = () => {
    const next = title.trim() || conversation.title;
    renameConversation(conversation.id, next);
    setTitle(next);
    setRenaming(false);
  };

  return (
    <div className={`recent-item ${active ? 'active' : ''}`} ref={ref}>
      {renaming ? (
        <input
          className="recent-rename-input"
          value={title}
          autoFocus
          onChange={e => setTitle(e.target.value)}
          onBlur={commitRename}
          onKeyDown={e => { if (e.key === 'Enter') commitRename(); if (e.key === 'Escape') { setTitle(conversation.title); setRenaming(false); } }}
          aria-label="Rename analysis"
        />
      ) : (
        <NavLink to={`/c/${conversation.id}`} className={`recent-link ${active ? 'active' : ''}`} title={conversation.title} onClick={onClick}>
          {conversation.pinned && <Pin size={11} className="recent-pin-glyph" aria-hidden="true" />}
          {conversation.title}
        </NavLink>
      )}
      <button
        className="recent-menu-btn"
        ref={menuBtnRef}
        aria-label={`More actions for ${conversation.title}`}
        aria-expanded={menuOpen}
        onClick={() => { setMenuOpen(v => !v); setConfirmingDelete(false); }}
      >
        <MoreHorizontal size={15} aria-hidden="true" />
      </button>

      {menuOpen && !confirmingDelete && (
        <div className="recent-menu" role="menu">
          <button role="menuitem" onClick={() => { setMenuOpen(false); setRenaming(true); }}><Pencil size={14} aria-hidden="true" />Rename</button>
          <button role="menuitem" onClick={() => { setConversationPinned(conversation.id, !conversation.pinned); setMenuOpen(false); }}>
            {conversation.pinned ? <PinOff size={14} aria-hidden="true" /> : <Pin size={14} aria-hidden="true" />}
            {conversation.pinned ? 'Unpin' : 'Pin'}
          </button>
          <button role="menuitem" className="danger" onClick={() => setConfirmingDelete(true)}><Trash2 size={14} aria-hidden="true" />Delete</button>
        </div>
      )}

      {confirmingDelete && (
        <div className="recent-menu recent-confirm" role="dialog" aria-label={`Delete ${conversation.title}?`}>
          <p><strong>Delete "{conversation.title}"?</strong></p>
          <p className="muted">This analysis will be removed from your recent list.</p>
          <div className="recent-confirm-actions">
            <button onClick={() => { setConfirmingDelete(false); setMenuOpen(false); }}>Cancel</button>
            <button className="danger" onClick={() => { deleteConversation(conversation.id); setConfirmingDelete(false); setMenuOpen(false); onDeleted(conversation.id); }}>Delete</button>
          </div>
        </div>
      )}
    </div>
  );
}
