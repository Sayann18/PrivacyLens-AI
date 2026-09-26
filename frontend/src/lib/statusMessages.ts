
export type UiSeverity = 'info' | 'warning' | 'error';
export type UiIcon = 'alert' | 'info';
export type UiActionKind = 'add-document' | 'try-another-file' | 'try-again' | 'analyze-again';
export type UiAction = { label: string; kind: UiActionKind };

export type UiStatus = {
  code: string;
  title: string;
  message: string;
  hint?: string;
  note?: string;
  severity: UiSeverity;
  icon: UiIcon;
  action?: UiAction;
};

const ACTION = {
  addDocument: { label: 'Add Document', kind: 'add-document' },
  tryAnotherFile: { label: 'Try Another File', kind: 'try-another-file' },
  tryAgain: { label: 'Try Again', kind: 'try-again' },
  analyzeAgain: { label: 'Analyze Again', kind: 'analyze-again' }
} as const satisfies Record<string, UiAction>;

const DEFAULT_FORMAT_HINT = 'Try PDF, DOCX, TXT, or a supported image format.';

type StatusEntry = Omit<UiStatus, 'code'>;

const STATUS_TABLE: Record<string, StatusEntry> = {
  MISSING_CONTENT: {
    title: 'Nothing to analyze yet',
    message: 'Please upload a document, paste some text, or enter a public URL.',
    severity: 'info', icon: 'info', action: ACTION.addDocument
  },
  MALFORMED_REQUEST: {
    title: 'We couldn\u2019t process that request',
    message: 'The submitted information wasn\u2019t in a valid format. Please try again.',
    severity: 'error', icon: 'alert'
  },
  UNSUPPORTED_FILE_TYPE: {
    title: 'This file type isn\u2019t supported',
    message: 'Please upload a supported document or image format.',
    hint: DEFAULT_FORMAT_HINT,
    severity: 'error', icon: 'alert', action: ACTION.tryAnotherFile
  },
  FILE_TOO_LARGE: {
    title: 'This file is too large',
    message: 'Please choose a smaller file and try again.',
    severity: 'error', icon: 'alert', action: ACTION.tryAnotherFile
  },
  EMPTY_FILE: {
    title: 'The file appears to be empty',
    message: 'We couldn\u2019t find any content to analyze.',
    severity: 'error', icon: 'alert', action: ACTION.tryAnotherFile
  },
  CORRUPTED_DOCUMENT: {
    title: 'We couldn\u2019t read this document',
    message: 'The file may be damaged or incomplete. Try opening it on your device and uploading a new copy.',
    severity: 'error', icon: 'alert', action: ACTION.tryAnotherFile
  },
  ENCRYPTED_DOCUMENT: {
    title: 'This document is protected',
    message: 'Please upload an accessible copy without a password or encryption.',
    severity: 'error', icon: 'alert', action: ACTION.tryAnotherFile
  },
  UNSUPPORTED_ENCODING: {
    title: 'We couldn\u2019t read the text encoding',
    message: 'Please convert the document to a standard text format and try again.',
    severity: 'error', icon: 'alert', action: ACTION.tryAnotherFile
  },

  INVALID_IMAGE: {
    title: 'That doesn\u2019t appear to be an image',
    message: 'Please upload a valid image file.',
    severity: 'error', icon: 'alert', action: ACTION.tryAnotherFile
  },
  OCR_UNAVAILABLE: {
    title: 'We couldn\u2019t read the text in this image',
    message: 'Text recognition isn\u2019t currently available for this document.',
    hint: 'You can try uploading a clearer image or a text-based PDF.',
    severity: 'error', icon: 'alert', action: ACTION.tryAnotherFile
  },
  NO_ANALYZABLE_CONTENT: {
    title: 'No readable text found',
    message: 'We couldn\u2019t detect enough text in this image to perform the analysis.',
    severity: 'info', icon: 'info', action: ACTION.tryAnotherFile
  },
  NO_READABLE_CONTENT: {
    title: 'We couldn\u2019t find enough readable text',
    message: 'The content didn\u2019t include enough text to analyze. Try a different file or paste the text directly.',
    severity: 'info', icon: 'info', action: ACTION.tryAnotherFile
  },
  EXTRACTION_FAILED: {
    title: 'Document reading failed',
    message: 'We couldn\u2019t obtain usable content from this file.',
    severity: 'error', icon: 'alert', action: ACTION.tryAnotherFile
  },

  INVALID_URL: {
    title: 'That URL doesn\u2019t look valid',
    message: 'Please check the link and try again.',
    severity: 'error', icon: 'alert'
  },
  URL_UNREACHABLE: {
    title: 'We couldn\u2019t access that webpage',
    message: 'Check that the URL is public and available, then try again.',
    severity: 'error', icon: 'alert'
  },
  URL_UPSTREAM_ERROR: {
    title: 'The webpage couldn\u2019t be retrieved',
    message: 'The site may be unavailable or may not allow automated access.',
    severity: 'error', icon: 'alert'
  },
  URL_UNREADABLE: {
    title: 'We couldn\u2019t extract readable content from that webpage',
    message: 'Try pasting the text or uploading the document instead.',
    severity: 'error', icon: 'alert'
  },

  ANALYSIS_FAILED: {
    title: 'We couldn\u2019t complete the analysis',
    message: 'Something prevented the document from being analyzed successfully.',
    note: 'Your original document was not changed.',
    severity: 'error', icon: 'alert', action: ACTION.tryAgain
  },
  ANALYSIS_NOT_FOUND: {
    title: 'This analysis is no longer available',
    message: 'The saved analysis could not be retrieved. Please analyze the document again.',
    severity: 'info', icon: 'info', action: ACTION.analyzeAgain
  },
  SERVICE_UNAVAILABLE: {
    title: 'This service is temporarily unavailable',
    message: 'Please try again in a few moments.',
    severity: 'error', icon: 'alert', action: ACTION.tryAgain
  },
  RATE_LIMITED: {
    title: 'Too many requests',
    message: 'Please wait a moment and try again.',
    severity: 'warning', icon: 'alert', action: ACTION.tryAgain
  },
  TIMEOUT: {
    title: 'The analysis took longer than expected',
    message: 'Please try again. Larger documents can take longer to process.',
    severity: 'warning', icon: 'alert', action: ACTION.tryAgain
  }
};

const ALIASES: Record<string, string> = {
  DOCUMENT_TOO_LARGE: 'FILE_TOO_LARGE',
  EMPTY_DOCUMENT: 'EMPTY_FILE',
  CORRUPTED_IMAGE: 'INVALID_IMAGE',
  URL_TIMEOUT: 'URL_UPSTREAM_ERROR',
  INTERNAL_ERROR: 'ANALYSIS_FAILED'
};

const FALLBACK_CODE = 'ANALYSIS_FAILED';

function canonicalCode(code?: string | null): string | undefined {
  if (typeof code !== 'string') return undefined;
  const key = code.trim().toUpperCase();
  const resolved = ALIASES[key] || key;
  return STATUS_TABLE[resolved] ? resolved : undefined;
}

export function isKnownStatus(code?: string | null): boolean {
  return Boolean(canonicalCode(code));
}

function formatFormatList(formats: string[]): string {
  const items = formats.map(f => f.replace(/^[.\s]+/, '').replace(/^image\//i, '').toUpperCase()).filter(Boolean);
  if (!items.length) return DEFAULT_FORMAT_HINT;
  if (items.length === 1) return `Try ${items[0]}.`;
  return `Try ${items.slice(0, -1).join(', ')}, or ${items[items.length - 1]}.`;
}

export function extractSupportedFormats(details: unknown): string[] | undefined {
  if (!details || typeof details !== 'object') return undefined;
  const record = details as Record<string, unknown>;
  for (const key of ['supported_formats', 'supported_extensions', 'supported_types', 'allowed_extensions', 'supported']) {
    const value = record[key];
    if (Array.isArray(value)) {
      const list = value.filter((v): v is string => typeof v === 'string' && v.trim().length > 0);
      if (list.length) return list;
    }
  }
  return undefined;
}

export function mapStatus(code?: string | null, options?: { supportedFormats?: string[] }): UiStatus {
  const resolved = canonicalCode(code) || FALLBACK_CODE;
  const entry = STATUS_TABLE[resolved];
  const status: UiStatus = { code: resolved, ...entry };
  if (resolved === 'UNSUPPORTED_FILE_TYPE' && options?.supportedFormats?.length) {
    status.hint = formatFormatList(options.supportedFormats);
  }
  return status;
}

export function resolveStatusCode(httpStatus: number, apiCode?: string | null, aborted = false): string {
  if (aborted) return 'TIMEOUT';
  const known = canonicalCode(apiCode);
  if (known) return known;
  if (httpStatus === 0) return 'SERVICE_UNAVAILABLE';
  if (httpStatus === 415) return 'UNSUPPORTED_FILE_TYPE';
  if (httpStatus === 413) return 'FILE_TOO_LARGE';
  if (httpStatus === 429) return 'RATE_LIMITED';
  if (httpStatus === 404) return 'ANALYSIS_NOT_FOUND';
  if (httpStatus === 503) return 'SERVICE_UNAVAILABLE';
  if (httpStatus === 504) return 'TIMEOUT';
  if (httpStatus === 400 || httpStatus === 422) return 'MALFORMED_REQUEST';
  return FALLBACK_CODE;
}


export type ExtractionState = {
  label: string;
  title: string;
  message: string;
  detail?: string;
  ocrIncomplete: boolean;
};

export const EXTRACTION_COMPLETE_LABEL = 'Text extraction complete';

export function describeExtraction(warning?: string | null): ExtractionState | null {
  const raw = typeof warning === 'string' ? warning.trim() : '';
  if (!raw) return null;
  const pages = raw.match(/(\d+)\s+(?:of|out of)\s+(\d+)\s+pages?/i);
  const ocrIncomplete = /\b(ocr|text recognition|image)/i.test(raw);
  return {
    label: 'Partial extraction',
    title: 'Analysis completed with limited text',
    message: 'Some parts of the document could not be read. The results below are based on the content we were able to extract.',
    detail: pages ? `${pages[1]} of ${pages[2]} pages could not be fully read.` : undefined,
    ocrIncomplete
  };
}

export function describeExtractionInfo(info: {
  extraction_status: 'COMPLETE' | 'PARTIAL' | 'FAILED' | 'NO_READABLE_CONTENT';
  warnings: string[];
  pages_total?: number | null;
  pages_failed?: number | null;
} | null | undefined): ExtractionState | null {
  if (!info) return null;
  const ocrIncomplete = (info.warnings || []).some(w => /\b(ocr|text recognition|image)/i.test(w));
  const pageDetail = info.pages_failed && info.pages_total
    ? `${info.pages_failed} of ${info.pages_total} pages could not be fully read.`
    : undefined;

  switch (info.extraction_status) {
    case 'PARTIAL':
      return {
        label: 'Partial extraction',
        title: 'Analysis completed with limited text',
        message: 'Some parts of the document could not be read. The results below are based on the content we were able to extract.',
        detail: pageDetail,
        ocrIncomplete
      };
    case 'FAILED':
      return {
        label: 'Document reading failed',
        title: 'Document reading failed',
        message: 'We couldn\u2019t obtain usable content from this file.',
        ocrIncomplete
      };
    case 'NO_READABLE_CONTENT':
      return {
        label: 'No readable text',
        title: 'We couldn\u2019t find enough readable text',
        message: 'There isn\u2019t enough usable content in this document to perform a reliable analysis.',
        ocrIncomplete
      };
    default:
      return null;
  }
}


export type StatusDomain = 'privacy' | 'financial';

const PRIVACY_STATUS: Record<string, string> = {
  DISCLOSED: 'Clearly stated',
  PARTIALLY_DISCLOSED: 'Partially explained',
  AMBIGUOUS: 'Wording is unclear',
  NOT_FOUND: 'Not found in this document',
  CONFLICTING: 'Potentially inconsistent wording'
};

const FINANCIAL_STATUS: Record<string, string> = {
  EXPLICIT: 'Clearly stated',
  AMBIGUOUS: 'Details are unclear',
  NOT_CLEARLY_STATED: 'Not clearly stated',
  CONFLICTING: 'Conflicting information found'
};

export function describeFindingStatus(status: unknown, domain: StatusDomain = 'privacy'): string | undefined {
  if (typeof status !== 'string' || !status.trim()) return undefined;
  const key = status.trim().toUpperCase().replace(/[\s-]+/g, '_');
  const table = domain === 'financial' ? FINANCIAL_STATUS : PRIVACY_STATUS;
  return table[key] || PRIVACY_STATUS[key] || FINANCIAL_STATUS[key];
}


export type Importance = 'high' | 'medium' | 'low' | 'info';

const IMPORTANCE_LABEL: Record<Importance, string> = {
  high: 'Important to review',
  medium: 'Worth checking',
  low: 'Additional detail',
  info: 'Additional detail'
};

export function describeImportance(severity?: string | null): string {
  const key = (typeof severity === 'string' ? severity.toLowerCase() : 'low') as Importance;
  return IMPORTANCE_LABEL[key] || IMPORTANCE_LABEL.low;
}

export const CONFIDENCE_EXPLANATION = 'Confidence reflects how directly the available document evidence supports this finding.';

const CONFIDENCE_LABEL = { high: 'Strong evidence', medium: 'Moderate evidence', low: 'Limited evidence' } as const;

export function confidenceLevel(confidence?: number | null, evidenceQuality?: string | null): keyof typeof CONFIDENCE_LABEL | undefined {
  const quality = typeof evidenceQuality === 'string' ? evidenceQuality.trim().toLowerCase() : '';
  if (quality === 'high' || quality === 'medium' || quality === 'low') return quality;
  if (typeof confidence !== 'number' || isNaN(confidence)) return undefined;
  const score = confidence > 1 ? confidence / 100 : confidence;
  if (score >= 0.75) return 'high';
  if (score >= 0.5) return 'medium';
  return 'low';
}

export function describeConfidence(confidence?: number | null, evidenceQuality?: string | null): string | undefined {
  const level = confidenceLevel(confidence, evidenceQuality);
  return level ? CONFIDENCE_LABEL[level] : undefined;
}


export type VerificationState = 'running' | 'supported' | 'mixed' | 'insufficient' | 'failed';
export type VerificationMessage = { title: string; hint?: string; severity: UiSeverity };

const VERIFICATION_TABLE: Record<VerificationState, VerificationMessage> = {
  running: { title: 'Checking available sources\u2026', severity: 'info' },
  supported: { title: 'Sources generally support this claim', severity: 'info' },
  mixed: { title: 'Sources provide mixed information', severity: 'warning' },
  insufficient: { title: 'Not enough reliable evidence found', severity: 'info' },
  failed: {
    title: 'We couldn\u2019t complete source verification',
    hint: 'Try again or review the available sources manually.',
    severity: 'error'
  }
};

export function describeVerification(verdict?: string | null): VerificationMessage & { state: VerificationState } {
  const key = typeof verdict === 'string' ? verdict.trim().toLowerCase().replace(/[\s-]+/g, '_') : '';
  let state: VerificationState = 'insufficient';
  if (key in VERIFICATION_TABLE) state = key as VerificationState;
  else if (/^(supported|verified|true|strong|strong_agreement|agree|confirmed)/.test(key)) state = 'supported';
  else if (/^(mixed|partial|conflict|disputed|contradict)/.test(key)) state = 'mixed';
  else if (/^(failed|error|unavailable)/.test(key)) state = 'failed';
  else if (/^(running|pending|checking|in_progress)/.test(key)) state = 'running';
  return { state, ...VERIFICATION_TABLE[state] };
}


const TOKEN_LABELS: Record<string, string> = {
  NOT_CLEARLY_STATED: 'not clearly stated',
  PARTIALLY_DISCLOSED: 'partially explained',
  NOT_FOUND: 'not found in this document',
  DISCLOSED: 'clearly stated',
  EXPLICIT: 'clearly stated',
  AMBIGUOUS: 'unclear',
  CONFLICTING: 'potentially inconsistent',
  OCR_UNAVAILABLE: 'text recognition unavailable',
  NO_ANALYZABLE_CONTENT: 'no readable text',
  REVIEW_RECOMMENDED: 'review suggested'
};

const TOKEN_PATTERN = new RegExp(`\\b(${Object.keys(TOKEN_LABELS).sort((a, b) => b.length - a.length).join('|')})\\b`, 'g');

export function humanizeBackendTokens(text: string): string {
  if (!text) return text;
  return text.replace(TOKEN_PATTERN, (token, _group, offset: number) => {
    const label = TOKEN_LABELS[token];
    const before = text.slice(0, offset).trimEnd();
    return before === '' || /[.!?]$/.test(before) ? label.charAt(0).toUpperCase() + label.slice(1) : label;
  });
}
