import { useState } from 'react';
import { FileText } from 'lucide-react';
import type { ConversationTurn } from '../../lib/types';
import { formatFileSize } from '../../lib/format';

const COLLAPSE_CHARS = 600;
const COLLAPSE_LINES = 8;
const PREVIEW_CHARS = 600;

function LongText({ text }: { text: string }) {
  const [expanded, setExpanded] = useState(false);
  const lineCount = text.split('\n').length;
  const isLong = text.length > COLLAPSE_CHARS || lineCount > COLLAPSE_LINES;
  if (!isLong) return <p className="pl-msg-text">{text}</p>;

  const preview = text.slice(0, PREVIEW_CHARS);
  return (
    <>
      <p className={`pl-msg-text ${expanded ? 'pl-msg-text-expanded' : 'pl-msg-text-collapsed'}`}>
        {expanded ? text : `${preview}${text.length > PREVIEW_CHARS ? '\u2026' : ''}`}
      </p>
      <button type="button" className="pl-msg-toggle" aria-expanded={expanded} onClick={() => setExpanded(value => !value)}>
        {expanded ? 'Show less' : 'Show more'}
      </button>
    </>
  );
}

export function UserMessage({ turn }: { turn: ConversationTurn }) {
  return (
    <div className="pl-msg pl-msg-user">
      <div className="pl-msg-user-bubble">
        {turn.userFiles?.map((file, i) => (
          <div className="pl-attachment-chip static" key={`${file.name}-${i}`}>
            <FileText size={14} aria-hidden="true" />
            <span>{file.name}</span>
            <small>{[file.name.split('.').pop()?.toUpperCase(), formatFileSize(file.size)].filter(Boolean).join(' \u00b7 ')}</small>
          </div>
        ))}
        {turn.userUrl && <p className="pl-msg-url">{turn.userUrl}</p>}
        {turn.userText ? <LongText text={turn.userText} /> : turn.userUrl ? null : !turn.userFiles?.length && (
          <p className="pl-msg-empty">Submitted content</p>
        )}
      </div>
    </div>
  );
}
