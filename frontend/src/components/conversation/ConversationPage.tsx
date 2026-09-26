import { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ConversationComposer } from './ConversationComposer';
import { UserMessage } from './UserMessage';
import { AssistantMessage } from './AssistantMessage';
import { analyzeFile, analyzeText, analyzeUrl } from '../../lib/api';
import { mapStatus } from '../../lib/statusMessages';
import { appendTurn, getConversation, refineConversationTitle, updateTurnItems } from '../../lib/storage';
import { buildFallbackTitle, buildRefinedTitle } from '../../lib/title';
import { getAnalysisInputType } from '../../lib/types';
import type { AnalysisInputType, AnalysisItem, ConversationTurn } from '../../lib/types';
import type { UiActionKind } from '../../lib/statusMessages';

export function ConversationPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [turns, setTurns] = useState<ConversationTurn[]>([]);
  const [busy, setBusy] = useState(false);
  const [conversationId, setConversationId] = useState(id);
  const [analysis, setAnalysis] = useState<{ key: string; type: AnalysisInputType } | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const scrollToResponse = useRef(false);
  const [greeting, setGreeting] = useState(() => getGreeting());
  const [promptIndex, setPromptIndex] = useState(() => Math.floor(Math.random() * EMPTY_PROMPTS.length));
  const isEmpty = turns.length === 0;

  useEffect(() => {
    if (!isEmpty) return;
    const timer = window.setInterval(() => setPromptIndex(index => (index + 1) % EMPTY_PROMPTS.length), 4200);
    return () => window.clearInterval(timer);
  }, [isEmpty]);

  useEffect(() => {
    setConversationId(id);
    if (id) {
      const existing = getConversation(id);
      setTurns(existing?.turns || []);
    } else {
      setTurns([]);
    }
  }, [id]);

  useEffect(() => {
    if (!id || !getConversation(id)) setGreeting(previous => getGreeting(previous));
  }, [id]);

  useEffect(() => {
    const container = scrollRef.current;
    if (!container) return;
    if (!busy && scrollToResponse.current) {
      scrollToResponse.current = false;
      container.querySelector('.pl-turn:last-child')?.scrollIntoView({ block: 'start', behavior: 'smooth' });
      return;
    }
    container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
  }, [turns, busy]);

  const handleSubmit = async (input: { text: string; url: string; useUrl: boolean; files: File[] }) => {
    const activeId = conversationId || `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
    const isFirstTurn = turns.length === 0;
    if (!conversationId) {
      setConversationId(activeId);
    }

    const turnId = `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
    const pendingTurn: ConversationTurn = {
      id: turnId,
      date: new Date().toISOString(),
      status: 'pending',
      userText: input.text.trim() || undefined,
      userUrl: input.useUrl ? input.url.trim() || undefined : undefined,
      userFiles: input.files.map(f => ({ name: f.name, size: f.size, type: f.type })),
      items: []
    };
    setTurns(prev => [...prev, pendingTurn]);
    setAnalysis({ key: turnId, type: getAnalysisInputType(input) });
    setBusy(true);

    const fallbackTitle = buildFallbackTitle(input);
    try { appendTurn(activeId, fallbackTitle, pendingTurn); } catch {}
    if (!conversationId) {
      navigate(`/c/${activeId}`, { replace: true });
    }

    const completed: AnalysisItem[] = [];
    const safelyAnalyze = async (label: string, action: () => Promise<AnalysisItem>) => {
      try { return await action(); }
      catch { return { label, error: mapStatus('ANALYSIS_FAILED').message, errorCode: 'ANALYSIS_FAILED' }; }
    };
    if (input.text.trim()) completed.push(await safelyAnalyze('Pasted text', () => analyzeText(input.text)));
    if (input.useUrl && input.url.trim()) {
      const targetUrl = input.url.trim();
      completed.push(await safelyAnalyze(targetUrl, () => analyzeUrl(targetUrl)));
    }
    for (const file of input.files) completed.push(await safelyAnalyze(file.name, () => analyzeFile(file)));

    const finishedTurn: ConversationTurn = { ...pendingTurn, status: 'complete', items: completed };
    scrollToResponse.current = true;
    setTurns(prev => prev.map(t => (t.id === turnId ? finishedTurn : t)));
    setBusy(false);
    setAnalysis(null);

    try { updateTurnItems(activeId, turnId, completed); } catch {}

    if (isFirstTurn) {
      try {
        const refined = buildRefinedTitle(completed, fallbackTitle, input);
        if (refined) refineConversationTitle(activeId, refined);
      } catch {
      }
    }

  };

  const openFilePicker = () => document.querySelector<HTMLInputElement>('.pl-composer input[type="file"]')?.click();

  const handleStatusAction = (kind: UiActionKind, turn: ConversationTurn) => {
    if (busy) return;
    if (kind === 'add-document' || kind === 'try-another-file') { openFilePicker(); return; }
    if (turn.userText || turn.userUrl) {
      void handleSubmit({ text: turn.userText || '', url: turn.userUrl || '', useUrl: Boolean(turn.userUrl), files: [] });
      return;
    }
    openFilePicker();
  };

  return (
    <div className="pl-conversation">
      {isEmpty ? (
        <div className="pl-empty-state">
          <h1>{greeting}</h1>
          <p className="pl-empty-prompt" key={promptIndex}>{EMPTY_PROMPTS[promptIndex]}</p>
          <ConversationComposer variant="empty" busy={busy} analysisType={analysis?.type} analysisKey={analysis?.key} onSubmit={handleSubmit} />
        </div>
      ) : (
        <>
          <div className="pl-messages" ref={scrollRef}>
            {turns.map(turn => (
              <div className="pl-turn" key={turn.id}>
                <UserMessage turn={turn} />
                <AssistantMessage turn={turn} loading={turn.status === 'pending'} onAction={handleStatusAction} />
              </div>
            ))}
          </div>
          <ConversationComposer variant="inline" busy={busy} analysisType={analysis?.type} analysisKey={analysis?.key} onSubmit={handleSubmit} />
        </>
      )}
    </div>
  );
}

const EMPTY_PROMPTS = [
  'Analyze a privacy policy',
  'Review terms & conditions',
  'Check a document for privacy risks',
  'Understand what data is being collected',
  'Analyze a public URL',
  'Find hidden privacy concerns'
];

function getGreeting(previous?: string) {
  const hour = new Date().getHours();
  const options = hour < 5
    ? ['Still up? Let’s take a quick look.', 'Ready for one more analysis?', 'Late-night review?']
    : hour < 12
      ? ['Good morning! ☀️', 'Good morning! Ready when you are.', 'Morning! What should we look into?']
      : hour < 18
        ? ['Good afternoon! 👋', 'Ready when you are.', 'Afternoon! What should we analyze?']
        : ['Good evening! 🌙', 'What should we review?', 'Evening! Ready to take a closer look?'];
  const available = options.filter(option => option !== previous);
  return available[Math.floor(Math.random() * available.length)] || options[0];
}
