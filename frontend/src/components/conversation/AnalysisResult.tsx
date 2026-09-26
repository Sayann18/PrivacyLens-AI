import { useState } from 'react';
import { AlertTriangle, FileText, Info, ShieldAlert } from 'lucide-react';
import type { AnalysisNotice, AnalysisReport, BackendEvidence } from '../../lib/types';
import { cleanCopy } from '../../lib/format';
import {
  RESULT_COPY, RISK_ANALYSIS_COPY, THINGS_TO_KNOW, getPriorityFindings
} from '../../lib/resultCopy';
import {
  EXTRACTION_COMPLETE_LABEL, describeExtraction, describeExtractionInfo, mapStatus, type UiIcon, type UiActionKind, type UiStatus
} from '../../lib/statusMessages';
import { TextButton } from '../ui/TextButton';

export function AnalysisResult({ report, label, warning }: { report: AnalysisReport; label?: string; warning?: string }) {
  if (!report) return null;
  const backend = report.backend;
  const summaryText = backend?.summary.text?.trim() || (backend?.summary.key_points || []).slice(0, 3).join(' ');
  const extraction = backend ? describeExtractionInfo(backend.extractionInfo) : describeExtraction(warning);
  const fromExtractedSource = Boolean(label) && label !== 'Pasted text';
  const showCompleteLabel = fromExtractedSource && !extraction && (!backend || backend.extractionStatus === 'COMPLETE');

  const findings = Array.isArray(report.findings) ? report.findings : [];
  const keyPoints = Array.isArray(report.top_things_to_know) ? report.top_things_to_know : [];
  const evidenceById = new Map((backend?.evidence || []).map(evidence => [evidence.evidence_id, evidence]));
  const priority = getPriorityFindings(findings);
  const recommendationItems: { id: string; text: string }[] = backend
    ? backend.recommendations.map((rec, i) => ({
        id: rec.recommendation_id || `rec-${i}`,
        text: rec.title && rec.description ? `${rec.title}: ${rec.description}` : (rec.description || rec.title)
      }))
    : Array.from(new Set(findings.map(finding => finding?.recommendation).filter(Boolean))).map(text => ({ id: text, text }));

  return (
    <div className="pl-result" style={{ opacity: 1, visibility: 'visible' }}>
      <div className="pl-result-heading">
        <h3>Result</h3>
      </div>

      {summaryText && (
        <section className="pl-summary-card">
          <div className="pl-summary-card-head">
            <FileText size={16} aria-hidden="true" />
            <h4>Summary</h4>
          </div>
          <p>{cleanCopy(summaryText)}</p>
        </section>
      )}


      {extraction ? (
        <div className="pl-result-warning-banner" role="status">
          <Info size={14} aria-hidden="true" />
          <span>
            <b>{extraction.label}</b> &middot; {extraction.title}. {extraction.message}
            {extraction.detail ? ` ${extraction.detail}` : ''}
          </span>
        </div>
      ) : showCompleteLabel && (
        <p className="muted small">{EXTRACTION_COMPLETE_LABEL}</p>
      )}

      {backend?.riskAnalysis && <RiskAnalysisSection risk={backend.riskAnalysis} />}

      {backend ? (
        <>
          <h4>{THINGS_TO_KNOW.heading}</h4>
          {backend.highlights.length > 0 ? (
            <ul className="pl-result-list">
              {backend.highlights.map((highlight, index) => {
                const evidence = highlight.evidence_id ? evidenceById.get(highlight.evidence_id) : undefined;
                return (
                  <li key={`highlight-${index}`}>
                    <div>
                      <strong>{cleanCopy(highlight.title)}</strong>
                      {highlight.summary && <><br />{cleanCopy(highlight.summary)}</>}
                      {evidence && <EvidencePreview evidence={evidence} />}
                    </div>
                  </li>
                );
              })}
            </ul>
          ) : null}
        </>
      ) : priority.length > 0 ? (
        <>
          <h4>{THINGS_TO_KNOW.heading}</h4>
          <ul className="pl-result-list">
            {priority.map(({ finding, index }) => {
              const summary = finding.explanation || finding.clause;
              const evidence = finding.evidence_ids?.length ? (report.backend?.evidence || []).find(item => finding.evidence_ids?.includes(item.evidence_id)) : undefined;
              return (
                <li key={`${finding.category}-${index}`}>
                  <div>
                    <strong>{cleanCopy(finding.title || 'Identified clause')}</strong>
                    {summary && <><br />{cleanCopy(summary)}</>}
                    {evidence && <EvidencePreview evidence={evidence} />}
                  </div>
                </li>
              );
            })}
          </ul>
        </>
      ) : keyPoints.length > 0 && (
        <>
          <h4>{THINGS_TO_KNOW.heading}</h4>
          <ul className="pl-result-list">
            {keyPoints.map((item, idx) => <li key={`${item}-${idx}`}>{cleanCopy(item)}</li>)}
          </ul>
        </>
      )}

      <h4>{RESULT_COPY.followUpHeading}</h4>
      <ul className="pl-result-list">
        {recommendationItems.map(item => <li key={item.id}>{cleanCopy(item.text)}</li>)}
        {!recommendationItems.length && <li className="muted">{RESULT_COPY.noFollowUp}</li>}
      </ul>

      <p className="pl-disclaimer"><strong>{RESULT_COPY.aboutHeading}</strong><br />{RESULT_COPY.aboutText}</p>
    </div>
  );
}


function RiskAnalysisSection({
  risk,
}: {
  risk: NonNullable<NonNullable<AnalysisReport['backend']>['riskAnalysis']>;
}) {
  const levelClass = risk.overall_level.toLowerCase();
  const areas = Array.isArray(risk.areas) ? risk.areas : [];

  return (
    <section className="pl-risk-analysis" aria-labelledby="pl-risk-analysis-heading">
      <div className="pl-risk-analysis-head">
        <ShieldAlert size={17} aria-hidden="true" />
        <h4 id="pl-risk-analysis-heading">{RISK_ANALYSIS_COPY.heading}</h4>
        <span className={`pl-risk-level ${levelClass}`}>{formatRiskLevel(risk.overall_level)}</span>
      </div>
      <div className="pl-risk-analysis-copy">
        <p>{cleanCopy(risk.overall_level === 'NOT_APPLICABLE' ? RISK_ANALYSIS_COPY.notApplicable : areas.length ? risk.explanation : RISK_ANALYSIS_COPY.noAreas)}</p>
      </div>

      {areas.length > 0 ? (
        <div className="pl-risk-area-list">
          {areas.map((area, index) => (
            <article className="pl-risk-area" key={`${area.area}-${area.title}-${index}`}>
              <div className="pl-risk-area-top">
                <span className={`pl-risk-area-dot ${area.level.toLowerCase()}`} aria-hidden="true" />
                <strong>{cleanCopy(area.title)}</strong>
                <span className={`pl-risk-level small ${area.level.toLowerCase()}`}>{formatRiskLevel(area.level)}</span>
              </div>
              <span className="pl-risk-area-category">{formatRiskArea(area.area)}</span>
              {area.summary && <p>{cleanCopy(area.summary)}</p>}
            </article>
          ))}
        </div>
      ) : (
        <div className={`pl-risk-empty ${levelClass}`}>
          <span className="pl-risk-empty-dot" aria-hidden="true" />
          <p>
            {risk.overall_level === 'NOT_APPLICABLE'
              ? RISK_ANALYSIS_COPY.notApplicable
              : RISK_ANALYSIS_COPY.noAreas}
          </p>
        </div>
      )}
    </section>
  );
}


function EvidencePreview({ evidence }: { evidence: BackendEvidence }) {
  const [open, setOpen] = useState(false);
  const sourceLabel = [
    evidence.page ? `Page ${evidence.page}` : '',
    evidence.section || ''
  ].filter(Boolean).join(' · ');
  const sourceUrl = evidence.source_url || '';
  const quote = cleanCopy(evidence.exact_quote || evidence.normalized_quote || '');

  if (!quote && !sourceLabel && !sourceUrl) return null;

  return (
    <div className="pl-source-preview">
      <button type="button" className="pl-source-button" onClick={() => setOpen(value => !value)} aria-expanded={open}>
        {THINGS_TO_KNOW.action}
      </button>
      {open && (
        <div className="pl-source-preview-body">
          {sourceLabel && <span className="pl-source-meta">{cleanCopy(sourceLabel)}</span>}
          {quote && <blockquote>{quote}</blockquote>}
          {sourceUrl && (
            <a href={sourceUrl} target="_blank" rel="noreferrer" className="pl-source-link">Open original source</a>
          )}
        </div>
      )}
    </div>
  );
}

function formatRiskLevel(level: string): string {
  switch (level) {
    case 'HIGH': return 'High attention';
    case 'MODERATE': return 'Moderate attention';
    case 'LOW': return 'Low attention';
    default: return 'Not applicable';
  }
}

function formatRiskArea(area: string): string {
  return area
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function StatusIcon({ icon }: { icon: UiIcon }) {
  return icon === 'info' ? <Info size={15} aria-hidden="true" /> : <AlertTriangle size={15} aria-hidden="true" />;
}

function StatusBody({ status, onAction }: { status: UiStatus; onAction?: (kind: UiActionKind) => void }) {
  return (
    <span>
      <strong>{status.title}</strong><br />
      {status.message}
      {status.hint && <><br /><span className="muted">{status.hint}</span></>}
      {status.note && <><br /><span className="muted">{status.note}</span></>}
      {status.action && onAction && <><br /><TextButton onClick={() => onAction(status.action!.kind)}>{status.action.label}</TextButton></>}
    </span>
  );
}

export function AnalysisError({ label, error, code, supportedFormats, onAction }: {
  label: string; error?: string; code?: string; supportedFormats?: string[]; onAction?: (kind: UiActionKind) => void;
}) {
  const status = code || !error ? mapStatus(code, { supportedFormats }) : undefined;
  return (
    <div className="pl-result pl-result-error">
      <div className="pl-result-head">
        <h3>{label}</h3>
      </div>
      <p className="pl-inline-error">
        {status ? <><StatusIcon icon={status.icon} /> <StatusBody status={status} onAction={onAction} /></> : <><AlertTriangle size={15} aria-hidden="true" /> {cleanCopy(error || '')}</>}
      </p>
    </div>
  );
}

export function AnalysisNoticeCard({ label, notice, onAction }: { label: string; notice: AnalysisNotice; onAction?: (kind: UiActionKind) => void }) {
  const status = mapStatus(notice.code || 'NO_ANALYZABLE_CONTENT');
  return (
    <div className="pl-result pl-result-notice">
      <div className="pl-result-head">
        <h3>{label}</h3>
      </div>
      <p className="pl-inline-notice"><StatusIcon icon={status.icon} /> <StatusBody status={status} onAction={onAction} /></p>
    </div>
  );
}
