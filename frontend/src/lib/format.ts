import { humanizeBackendTokens } from './statusMessages';

export function formatRelativeDate(iso: string) {
  const date = new Date(iso);
  const time = date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  const dayDiff = Math.round((new Date().setHours(0, 0, 0, 0) - new Date(date).setHours(0, 0, 0, 0)) / 86400000);
  if (dayDiff === 0) return `Today, ${time}`;
  if (dayDiff === 1) return `Yesterday, ${time}`;
  return date.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
}

export function dayBucket(iso: string): 'Today' | 'Yesterday' | 'Previous 7 days' | 'Older' {
  const dayDiff = Math.round((new Date().setHours(0, 0, 0, 0) - new Date(iso).setHours(0, 0, 0, 0)) / 86400000);
  if (dayDiff <= 0) return 'Today';
  if (dayDiff === 1) return 'Yesterday';
  if (dayDiff <= 7) return 'Previous 7 days';
  return 'Older';
}

export function stripMarkupArtifacts(value: string): string {
  if (!value) return value;
  const looksLikeMarkup = /<\/?[a-zA-Z][\w-]*(\s[^<>]*)?>/.test(value);
  if (!looksLikeMarkup) return value;
  return value.replace(/<\/?[a-zA-Z][\w-]*(\s[^<>]*)?>/g, ' ').replace(/\s{2,}/g, ' ').trim();
}

export function cleanCopy(value: string): string {
  return humanizeBackendTokens(stripMarkupArtifacts(value));
}

export function formatFileSize(bytes: number) {
  if (!Number.isFinite(bytes) || bytes <= 0) return '';
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
