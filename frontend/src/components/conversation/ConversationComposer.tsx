import { useEffect, useRef, useState } from 'react';
import { ArrowUp, FileText, Plus, X } from 'lucide-react';
import { formatFileSize } from '../../lib/format';
import { getAnalyzingLabel, getProgressPlan } from '../../lib/progressCopy';
import type { AnalysisInputType } from '../../lib/types';

const ACCEPTED = '.pdf,.docx,.pptx,.xlsx,.csv,.txt,.md,.markdown,.json,.html,.htm,.xml,.log,.yaml,.yml,image/png,image/jpeg,image/webp,image/bmp,image/tiff,image/gif';
const MAX_FILES = 10;
const STAGE_INTERVAL_MS = 2600;
const MAX_INPUT_HEIGHT = 144;
const LOADER_SEGMENTS = Array.from({ length: 12 }, (_, i) => i);

function SegmentedLoader() {
  return (
    <span className="pl-loader" aria-hidden="true">
      {LOADER_SEGMENTS.map(i => <i key={i} style={{ '--i': i } as React.CSSProperties} />)}
    </span>
  );
}

function AnalyzingStatus({ type }: { type: AnalysisInputType }) {
  const plan = getProgressPlan(type);
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const timer = window.setInterval(() => setIndex(current => Math.min(current + 1, plan.length - 1)), STAGE_INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, [plan.length]);

  return (
    <div className="pl-composer-row pl-composer-status" role="status" aria-live="polite" aria-busy="true">
      <SegmentedLoader />
      <span className="pl-sr-only">{getAnalyzingLabel(type)}</span>
      <span className="pl-composer-status-text" aria-hidden="true">{plan[index]}</span>
    </div>
  );
}

export function ConversationComposer({
  variant,
  busy,
  analysisType,
  analysisKey,
  onSubmit
}: {
  variant: 'empty' | 'inline';
  busy: boolean;
  analysisType?: AnalysisInputType | null;
  analysisKey?: string;
  onSubmit: (input: { text: string; url: string; useUrl: boolean; files: File[] }) => void;
}) {
  const [files, setFiles] = useState<File[]>([]);
  const [text, setText] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const chooseFiles = (incoming: FileList | File[]) => {
    setFiles(existing => [...existing, ...Array.from(incoming)].slice(0, MAX_FILES));
  };
  const removeFile = (index: number) => setFiles(existing => existing.filter((_, i) => i !== index));
  const ready = files.length > 0 || Boolean(text.trim());

  const submit = () => {
    if (!ready || busy) return;
    const value = text.trim();
    const isDirectUrl = /^https?:\/\/[^\s]+$/i.test(value);
    onSubmit({ text: isDirectUrl ? '' : text, url: isDirectUrl ? value : '', useUrl: isDirectUrl, files });
    setFiles([]); setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = '';
      textareaRef.current.blur();
    }
  };

  const updateText = (value: string) => {
    setText(value);
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, MAX_INPUT_HEIGHT)}px`;
    textarea.style.overflowY = textarea.scrollHeight > MAX_INPUT_HEIGHT ? 'auto' : 'hidden';
  };

  const analyzing = busy && Boolean(analysisType);

  return (
    <div className={`pl-composer-wrap ${variant === 'empty' ? 'pl-composer-wrap-empty' : ''}`}>
      <section
        className={`pl-composer ${dragOver ? 'drag-over' : ''} ${analyzing ? 'is-analyzing' : ''}`}
        onDragOver={e => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={e => { e.preventDefault(); setDragOver(false); chooseFiles(e.dataTransfer.files); }}
      >
        {analyzing && analysisType ? (
          <AnalyzingStatus key={analysisKey} type={analysisType} />
        ) : (<>
        {files.length > 0 && (
          <div className="pl-composer-extras">
            {files.map((file, index) => (
              <div className="pl-attachment-chip" key={`${file.name}-${index}`}>
                <FileText size={14} aria-hidden="true" />
                <span>{file.name}</span>
                <small>{[file.name.split('.').pop()?.toUpperCase(), formatFileSize(file.size)].filter(Boolean).join(' \u00b7 ')}</small>
                <button onClick={() => removeFile(index)} aria-label={`Remove ${file.name}`}><X size={13} /></button>
              </div>
            ))}
          </div>
        )}
        <div className="pl-composer-row">
          <label className="pl-composer-icon-btn" aria-label="Add files">
            <Plus size={19} aria-hidden="true" />
            <input ref={fileInputRef} type="file" accept={ACCEPTED} multiple hidden onChange={e => { if (e.target.files) chooseFiles(e.target.files); e.target.value = ''; }} />
          </label>
          <textarea
            ref={textareaRef}
            aria-label="Paste a privacy policy or ask PrivacyLens to analyze a document"
            value={text}
            onChange={e => updateText(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); submit(); } }}
            placeholder={variant === 'empty' ? 'Paste a policy or ask about this document\u2026' : 'Ask another question, or paste another policy\u2026'}
            disabled={busy}
            rows={1}
          />
          <button className="pl-composer-send" disabled={!ready || busy} onClick={submit} aria-label={busy ? 'Analyzing' : 'Analyze'}>
            {busy ? <span className="spinner" aria-hidden="true" /> : <ArrowUp size={16} aria-hidden="true" />}
          </button>
        </div>
        </>)}
      </section>
      <small className="pl-composer-hint">PDF, DOCX, TXT, spreadsheets, presentations, and images · or paste text or a public URL</small>
    </div>
  );
}
