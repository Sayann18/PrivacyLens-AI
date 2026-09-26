import type { ConversationTurn } from '../../lib/types';
import type { UiActionKind } from '../../lib/statusMessages';
import { AnalysisResult, AnalysisError, AnalysisNoticeCard } from './AnalysisResult';

export function AssistantMessage({ turn, loading, onAction }: { turn: ConversationTurn; loading: boolean; onAction?: (kind: UiActionKind, turn: ConversationTurn) => void }) {
  const isStalePending = turn.status === 'pending' && Date.now() - new Date(turn.date).getTime() > 65_000;
  const hasItems = turn.items && turn.items.length > 0;
  const showLoading = !hasItems && loading && !isStalePending;
  const handleAction = onAction ? (kind: UiActionKind) => onAction(kind, turn) : undefined;
  if (showLoading) return null;

  return (
    <div className="pl-msg pl-msg-assistant">
      <div className="pl-msg-assistant-body">
          {!hasItems && (
            <p className="pl-incomplete-result" role="status">
              This analysis didn&rsquo;t finish. Please submit the document again to receive a summary.
            </p>
          )}
          {turn.items.map((item, i) => {
            const key = `${item.label}-${i}`;
            return (
              <div key={key} className="pl-result-group">
                {item.report ? (
                  <AnalysisResult report={item.report} label={item.label} warning={item.warning} />
                ) : item.notice ? (
                  <AnalysisNoticeCard label={item.label} notice={item.notice} onAction={handleAction} />
                ) : (
                  <AnalysisError label={item.label} error={item.error} code={item.errorCode} supportedFormats={item.supportedFormats} onAction={handleAction} />
                )}
              </div>
            );
          })}
      </div>
    </div>
  );
}
