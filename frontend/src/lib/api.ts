import type { AnalysisItem, AnalysisReport } from './types';
import { adaptAnalysisResponse, isBackendAnalysisReport } from './analysisResponseAdapter';
import { extractSupportedFormats, isKnownStatus, mapStatus, resolveStatusCode } from './statusMessages';

export const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export type ApiErrorInfo = {
  code?: string;
  message?: string;
  details?: unknown;
};

export function getApiError(body: any, status?: number): ApiErrorInfo {
  if (!body) return {};

  if (body.error && typeof body.error === 'object') {
    return {
      code: body.error.code,
      message: body.error.message,
      details: body.error.details
    };
  }

  if (body.detail && typeof body.detail === 'object' && !Array.isArray(body.detail) && body.detail.error) {
    const err = body.detail.error;
    return {
      code: err.code,
      message: err.message,
      details: err.details
    };
  }

  if (Array.isArray(body.detail)) {
    const messages = body.detail
      .map((item: any) => {
        if (typeof item === 'string') return item;
        const field = Array.isArray(item?.loc) ? item.loc.filter((l: any) => l !== 'body').join('.') : '';
        return field ? `${field}: ${item?.msg || 'invalid'}` : item?.msg || 'Invalid value';
      })
      .filter(Boolean);
    return {
      code: 'MALFORMED_REQUEST',
      message: messages.join('; ') || 'Invalid request parameters.',
      details: body.detail
    };
  }

  if (typeof body.detail === 'string' && body.detail.trim()) {
    return { message: body.detail.trim() };
  }

  if (typeof body.message === 'string' && body.message.trim()) {
    return { code: body.code, message: body.message.trim() };
  }

  return {};
}

function failedItem(label: string, httpStatus: number, body: any, aborted = false): AnalysisItem {
  const info = getApiError(body, httpStatus);
  const errorCode = resolveStatusCode(httpStatus, info.code, aborted);
  const supportedFormats = extractSupportedFormats(info.details);
  return { label, error: mapStatus(errorCode, { supportedFormats }).message, errorCode, supportedFormats };
}

function failedItemFromCode(label: string, errorCode: string): AnalysisItem {
  return { label, error: mapStatus(errorCode).message, errorCode };
}

export async function requestAnalysis(label: string, init: RequestInit): Promise<AnalysisItem> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 60_000);
  try {
    const response = await fetch(`${API_BASE}/api/analyses`, { ...init, signal: controller.signal });
    const body = await response.json().catch(() => ({}));

    if (body.analyzable === false || body.status === 'NO_ANALYZABLE_CONTENT') {
      const code = isKnownStatus(body.status) ? String(body.status) : 'NO_ANALYZABLE_CONTENT';
      return { label, notice: { kind: 'info', code, message: mapStatus(code).message } };
    }

    if (!response.ok) {
      const errInfo = getApiError(body, response.status);
      if (errInfo.code === 'NO_ANALYZABLE_CONTENT') {
        return { label, notice: { kind: 'info', code: 'NO_ANALYZABLE_CONTENT', message: mapStatus('NO_ANALYZABLE_CONTENT').message } };
      }
      return failedItem(label, response.status, body);
    }

    const warnings = Array.isArray(body.warnings) && body.warnings.length > 0 ? body.warnings.join(' ') : undefined;
    const report = isBackendAnalysisReport(body) ? adaptAnalysisResponse(body) : (body as AnalysisReport);
    return { label, report, warning: warnings };
  } catch (error) {
    return failedItem(label, 0, {}, error instanceof Error && error.name === 'AbortError');
  } finally {
    window.clearTimeout(timeout);
  }
}

export async function analyzeUrl(url: string): Promise<AnalysisItem> {
  return requestAnalysis(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url }) });
}

export async function analyzeText(text: string): Promise<AnalysisItem> {
  return requestAnalysis('Pasted text', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }) });
}

export async function analyzeFile(file: File): Promise<AnalysisItem> {
  const max = 25 * 1024 * 1024;
  if (file.size > max) return failedItemFromCode(file.name, 'FILE_TOO_LARGE');
  const form = new FormData();
  form.append('file', file);
  return requestAnalysis(file.name, { method: 'POST', body: form });
}
