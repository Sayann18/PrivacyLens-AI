import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { MessageSquareText, Search, X } from 'lucide-react';
import { useConversations } from '../../lib/storage';
import { useDialogFocus } from './useDialogFocus';

export function SearchModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const conversations = useConversations();
  const navigate = useNavigate();
  const { id: activeId } = useParams();
  const [query, setQuery] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  useDialogFocus(open, onClose, panelRef, inputRef);

  useEffect(() => { if (!open) setQuery(''); }, [open]);

  const sorted = useMemo(
    () => [...conversations].sort((a, b) => (a.updatedAt < b.updatedAt ? 1 : -1)),
    [conversations]
  );

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return sorted;
    return sorted.filter(c =>
      c.title.toLowerCase().includes(q) ||
      c.turns.some(t =>
        t.userUrl?.toLowerCase().includes(q) ||
        t.userFiles?.some(f => f.name.toLowerCase().includes(q)) ||
        t.userText?.toLowerCase().includes(q)
      )
    );
  }, [sorted, query]);

  if (!open) return null;

  const openConversation = (id: string) => { onClose(); navigate(`/c/${id}`); };

  return (
    <div className="pl-modal-overlay" onMouseDown={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div
        className="pl-modal-panel pl-modal-lg pl-search-modal"
        role="dialog"
        aria-modal="true"
        aria-label="Search chats"
        ref={panelRef}
        tabIndex={-1}
      >
        <div className="pl-search-modal-head">
          <Search size={16} aria-hidden="true" />
          <input
            ref={inputRef}
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && results[0]) openConversation(results[0].id);
            }}
            placeholder="Search..."
            aria-label="Search chats"
          />
          <button className="icon-button" onClick={onClose} aria-label="Close search">
            <X size={18} />
          </button>
        </div>

        <div className="pl-search-modal-body">
          {conversations.length === 0 ? (
            <p className="pl-search-empty">
              No chats yet
              <br />
              <small>Start a new analysis to see it here.</small>
            </p>
          ) : (
            <>
              <small className="pl-recent-label">{query.trim() ? 'Results' : 'Recent chats'}</small>
              {results.length ? (
                <div className="pl-search-results" role="listbox" aria-label="Conversations">
                  {results.map(c => (
                    <button
                      key={c.id}
                      role="option"
                      aria-selected={c.id === activeId}
                      className={`pl-search-row ${c.id === activeId ? 'active' : ''}`}
                      onClick={() => openConversation(c.id)}
                    >
                      <MessageSquareText size={15} aria-hidden="true" />
                      <span>{c.title}</span>
                    </button>
                  ))}
                </div>
              ) : (
                <p className="pl-search-empty">No matching chats</p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
