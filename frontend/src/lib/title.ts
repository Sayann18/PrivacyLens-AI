import type { AnalysisItem, Conversation } from './types';

const GENERIC_FILENAME = /^(unnamed|untitled|untitled[\s_-]?design|image|img|photo|screenshot|screen[\s_-]?shot|scan|document|doc|file|clipboard|paste|upload)[\s_-]?\d*(\.[a-z0-9]+)?$/i;
const DOC_TYPE_LABELS: [RegExp, string][] = [
  [/privacy/i, 'Privacy Policy'],
  [/cookie/i, 'Cookie Policy'],
  [/terms.*(service|use)|tos\b/i, 'Terms of Service'],
  [/terms.*condition/i, 'Terms & Conditions'],
  [/(employee|hr|workplace)/i, 'Employee Data Policy'],
  [/data[\s_-]?(processing|protection)/i, 'Data Processing Policy'],
  [/security/i, 'Security Policy'],
  [/subscription|billing/i, 'Subscription Terms'],
  [/agreement|contract/i, 'Service Agreement']
];

export function normalizeTitle(raw: string): string {
  let title = raw
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/[*_`#]/g, '')
    .replace(/^["'\s]+|["'\s]+$/g, '')
    .replace(/^(conversation\s+)?title\s*:\s*/i, '')
    .replace(/\s+/g, ' ')
    .replace(/[.,;:\-\s]+$/g, '')
    .trim();
  if (title.length > 55) {
    title = title.slice(0, 55).replace(/\s+\S*$/, '').trim();
  }
  return title;
}

export function titleCase(text: string): string {
  return text
    .split(/\s+/)
    .filter(Boolean)
    .map(word => (word.length <= 3 && word === word.toLowerCase() && !/^[0-9]/.test(word) ? word : word[0].toUpperCase() + word.slice(1)))
    .join(' ');
}

export function humanizeFilename(name: string): string {
  const withoutExt = name.replace(/\.[a-z0-9]+$/i, '');
  const spaced = withoutExt.replace(/[_\-.]+/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2');
  return titleCase(spaced.replace(/\s+/g, ' ').trim());
}

export function guessDocTypeFromHint(hint: string): string | null {
  for (const [pattern, label] of DOC_TYPE_LABELS) {
    if (pattern.test(hint)) return label;
  }
  return null;
}

export function humanizeDomain(rawUrl: string): { brand: string; docType: string | null } {
  try {
    const url = new URL(rawUrl.match(/^https?:\/\//) ? rawUrl : `https://${rawUrl}`);
    const host = url.hostname.replace(/^www\./, '');
    const parts = host.split('.');
    const brandPart = parts.length > 2 ? parts[parts.length - 2] : parts[0];
    const brand = titleCase(brandPart.replace(/[-_]/g, ' '));
    const docType = guessDocTypeFromHint(`${url.pathname} ${url.search}`);
    return { brand, docType };
  } catch {
    return { brand: titleCase(rawUrl.replace(/^https?:\/\//, '').split('/')[0]), docType: null };
  }
}

export function extractBrandedPhrase(text: string): string | null {
  const pattern = /\b([A-Z][A-Za-z0-9&.']*(?:\s+(?:of|the|and|&)?\s?[A-Z][A-Za-z0-9&.']*){0,2})\s+(Privacy Policy|Privacy Notice|Privacy Statement|Terms of Service|Terms and Conditions|Terms of Use|Cookie Policy|Data Policy|Data Processing Agreement)\b/;
  const match = text.match(pattern);
  if (!match) return null;
  const brand = match[1].trim();
  if (brand.split(/\s+/).length > 3) return null;
  return normalizeTitle(`${brand} ${match[2]}`);
}

export function buildFallbackTitle(input: { text: string; url: string; useUrl: boolean; files: File[] }): string {
  if (input.files.length) {
    const first = input.files[0];
    if (!GENERIC_FILENAME.test(first.name)) {
      const humanized = humanizeFilename(first.name);
      const docType = guessDocTypeFromHint(first.name);
      const base = docType && !new RegExp(docType, 'i').test(humanized) ? `${humanized} ${docType}` : humanized;
      return normalizeTitle(base.endsWith('Review') || base.endsWith('Policy') || base.endsWith('Agreement') ? base : `${base} Review`) || 'Document Review';
    }
    const isImage = first.type?.startsWith('image/') || /\.(png|jpe?g|webp|bmp|gif)$/i.test(first.name);
    return isImage ? 'Image Document Review' : 'Document Review';
  }

  if (input.useUrl && input.url.trim()) {
    const { brand, docType } = humanizeDomain(input.url.trim());
    return normalizeTitle(`${brand} ${docType || 'Privacy Policy'} Review`);
  }

  if (input.text.trim()) {
    const text = input.text.trim();
    const docType = guessDocTypeFromHint(text.slice(0, 400));
    if (docType) return `${docType} Review`;

    if (/^https?:\/\//i.test(text)) {
      const { brand, docType: urlType } = humanizeDomain(text);
      return normalizeTitle(`${brand} ${urlType || 'Policy'} Review`);
    }

    const lower = text.toLowerCase();
    if (lower.includes('privacy') || lower.includes('personal data') || lower.includes('gdpr')) return 'Privacy Policy Review';
    if (lower.includes('terms') || lower.includes('condition') || lower.includes('tos')) return 'Terms of Service Review';
    if (lower.includes('cookie') || lower.includes('tracking')) return 'Cookie & Tracking Audit';
    if (lower.includes('subscription') || lower.includes('billing') || lower.includes('renewal')) return 'Subscription Terms Review';
    if (lower.includes('security') || lower.includes('vulnerability')) return 'Security Assessment';
    if (lower.includes('agreement') || lower.includes('contract')) return 'Service Agreement Review';

    const firstLine = text.split('\n')[0].replace(/^(please\s+)?(analyze|review|check|summarize|read|look at)\s+(this|the|my)?\s*/i, '').trim();
    if (firstLine.length >= 6 && firstLine.length <= 40 && /^[A-Za-z0-9\s.,'&-]+$/.test(firstLine)) {
      const words = firstLine.split(/\s+/);
      const hasGibberish = words.some(w => w.length > 4 && !/[aeiouy]/i.test(w));
      if (!hasGibberish && words.length >= 2 && words.length <= 5) {
        return normalizeTitle(`${titleCase(firstLine)} Review`);
      }
    }

    return 'Policy & Document Review';
  }

  return 'Privacy Analysis';
}

export function buildRefinedTitle(
  items: AnalysisItem[],
  fallback: string,
  input?: { url?: string; useUrl?: boolean; files?: (File | { name: string })[] }
): string | null {
  const noticeItem = items.find(i => i.notice);
  if (noticeItem && !items.some(i => i.report)) {
    return 'Image Document Review';
  }

  const report = items.find(item => item.report)?.report;
  if (!report) return null;

  const corpus = [report.source, report.summary, ...(report.top_things_to_know || [])].filter(Boolean).join(' ');
  const branded = extractBrandedPhrase(corpus);
  if (branded) return branded;

  const typeMap: Record<string, string> = {
    privacy_policy: 'Privacy Policy Review',
    terms_and_conditions: 'Terms of Service Review',
    subscription_terms: 'Subscription & Billing Terms',
    service_agreement: 'Service Agreement Review',
    mixed_terms_privacy: 'Terms & Privacy Review',
  };

  let title = typeMap[report.document_type] || '';

  if (!title) {
    const docType = guessDocTypeFromHint(corpus);
    if (docType) title = `${docType} Review`;
  }

  if (!title) {
    const categories = (report.findings || []).map(f => f.category);
    if (categories.some(c => c.includes('data') || c.includes('track') || c.includes('cookie'))) {
      title = 'Data Privacy & Tracking Review';
    } else if (categories.some(c => c.includes('pay') || c.includes('renew') || c.includes('cancel'))) {
      title = 'Subscription & Payment Terms';
    } else if (categories.some(c => c.includes('liab') || c.includes('arbit') || c.includes('indemn'))) {
      title = 'Legal Liability & Terms Review';
    } else {
      title = 'Document Policy Analysis';
    }
  }

  if (input?.useUrl && input.url?.trim()) {
    const { brand } = humanizeDomain(input.url.trim());
    return normalizeTitle(`${brand} ${title}`);
  }

  if (report.source && !GENERIC_FILENAME.test(report.source) && !report.source.includes('pasted') && !report.source.includes('upload')) {
    const humanSource = humanizeFilename(report.source);
    if (humanSource && humanSource.length < 35) {
      return normalizeTitle(`${humanSource} Review`);
    }
  }

  return normalizeTitle(title);
}

export function deriveSummarizedTitle(conversation: Conversation): string {
  if (conversation.titleSource === 'manual') {
    return conversation.title;
  }

  for (const turn of conversation.turns) {
    if (turn.items && turn.items.length > 0) {
      const refined = buildRefinedTitle(turn.items, conversation.title, {
        url: turn.userUrl,
        useUrl: Boolean(turn.userUrl),
        files: turn.userFiles
      });
      if (refined) return refined;
    }
  }

  const firstTurn = conversation.turns[0];
  if (firstTurn) {
    return buildFallbackTitle({
      text: firstTurn.userText || '',
      url: firstTurn.userUrl || '',
      useUrl: Boolean(firstTurn.userUrl),
      files: (firstTurn.userFiles || []).map(f => new File([], f.name, { type: f.type }))
    });
  }

  return conversation.title || 'Privacy Analysis';
}
