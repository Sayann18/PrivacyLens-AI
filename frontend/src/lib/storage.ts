import { useEffect, useState } from 'react';
import type { AppSettings, Conversation, ConversationTurn } from './types';

const SETTINGS_KEY = 'privacylens.settings.v1';
const CONVERSATIONS_KEY = 'privacylens.conversations.v1';
const CONVERSATIONS_MAX = 100;
const CONVERSATIONS_EVENT = 'privacylens:conversations-changed';

export const DEFAULT_SETTINGS: AppSettings = { theme: 'dark', displayName: 'Security workspace' };

export function readSettings(): AppSettings {
  try {
    const raw = window.localStorage.getItem(SETTINGS_KEY);
    if (!raw) return DEFAULT_SETTINGS;
    return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) };
  } catch {
    return DEFAULT_SETTINGS;
  }
}

function writeSettings(settings: AppSettings) {
  try {
    window.localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  } catch {}
}

export function useSettings() {
  const [settings, setSettings] = useState<AppSettings>(() => readSettings());
  const update = (patch: Partial<AppSettings>) => {
    setSettings((current) => {
      const next = { ...current, ...patch };
      writeSettings(next);
      return next;
    });
  };
  return [settings, update] as const;
}

function normalizeInput(value?: string) {
  return (value || '').trim().replace(/\s+/g, ' ').toLowerCase();
}

function conversationInputKey(conversation: Conversation) {
  const firstTurn = conversation.turns[0];
  if (!firstTurn) return `conversation:${conversation.id}`;
  const reportSource = firstTurn.items?.find((item) => item.report?.source)?.report?.source;
  if (reportSource?.trim()) return `source:${normalizeInput(reportSource)}`;
  if (firstTurn.userUrl?.trim()) return `url:${normalizeInput(firstTurn.userUrl)}`;
  if (firstTurn.userFiles?.length) {
    const files = firstTurn.userFiles
      .map((file) => `${normalizeInput(file.name)}:${file.size}:${normalizeInput(file.type)}`)
      .sort()
      .join('|');
    return `files:${files}`;
  }
  if (firstTurn.userText?.trim()) return `text:${normalizeInput(firstTurn.userText)}`;
  return `turn:${normalizeInput(firstTurn.id)}`;
}

function isRawInputTitle(conversation: Conversation) {
  if (conversation.titleSource === 'manual') return false;
  const title = normalizeInput(conversation.title);
  const firstTurn = conversation.turns[0];
  if (!firstTurn) return false;
  if (title === 'pasted text' || title === 'text input') return true;
  const rawInputs = [firstTurn.userUrl, firstTurn.userText, ...(firstTurn.userFiles || []).map((file) => file.name)].filter(Boolean);
  if (rawInputs.some((value) => title === normalizeInput(value))) return true;
  return false;
}

function rankConversation(conversation: Conversation) {
  const legacy = conversation.id.startsWith('legacy-history-') ? 0 : 1;
  const refined = isRawInputTitle(conversation) ? 0 : 1;
  const manual = conversation.titleSource === 'manual' ? 1 : 0;
  return [legacy, refined, manual, conversation.turns.length, new Date(conversation.updatedAt).getTime()];
}

function compareRank(a: Conversation, b: Conversation) {
  const rankA = rankConversation(a);
  const rankB = rankConversation(b);
  for (let index = 0; index < rankA.length; index += 1) {
    if (rankA[index] !== rankB[index]) return rankB[index] - rankA[index];
  }
  return 0;
}

function normalizeConversations(input: Conversation[]) {
  const groups = new Map<string, Conversation[]>();
  for (const conversation of input) {
    const key = conversationInputKey(conversation);
    const group = groups.get(key) || [];
    group.push(conversation);
    groups.set(key, group);
  }

  const output: Conversation[] = [];
  for (const group of groups.values()) {
    if (group.length === 1) {
      output.push(group[0]);
      continue;
    }
    const refined = group.filter((conversation) => !conversation.id.startsWith('legacy-history-') && !isRawInputTitle(conversation));
    if (refined.length) {
      output.push(...refined);
      continue;
    }
    output.push([...group].sort(compareRank)[0]);
  }

  return output.sort((a, b) => (a.updatedAt < b.updatedAt ? 1 : -1)).slice(0, CONVERSATIONS_MAX);
}

export function readConversations(): Conversation[] {
  try {
    const raw = window.localStorage.getItem(CONVERSATIONS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? normalizeConversations(parsed) : [];
  } catch {
    return [];
  }
}

function writeConversations(list: Conversation[]) {
  try {
    window.localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(normalizeConversations(list)));
  } catch {}
  window.dispatchEvent(new Event(CONVERSATIONS_EVENT));
}

export function repairConversationCollection() {
  const current = readStoredConversations();
  const normalized = normalizeConversations(current);
  if (JSON.stringify(current) !== JSON.stringify(normalized)) writeConversations(normalized);
}

function readStoredConversations(): Conversation[] {
  try {
    const raw = window.localStorage.getItem(CONVERSATIONS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function getConversation(id: string): Conversation | undefined {
  return readConversations().find((conversation) => conversation.id === id);
}

export function saveConversation(conversation: Conversation) {
  const list = readConversations();
  const index = list.findIndex((item) => item.id === conversation.id);
  if (index >= 0) list[index] = conversation;
  else list.unshift(conversation);
  writeConversations(list);
}

export function renameConversation(id: string, title: string) {
  const list = readConversations();
  const index = list.findIndex((conversation) => conversation.id === id);
  if (index >= 0) {
    list[index] = { ...list[index], title, titleSource: 'manual' };
    writeConversations(list);
  }
}

export function setConversationPinned(id: string, pinned: boolean) {
  const list = readConversations();
  const index = list.findIndex((conversation) => conversation.id === id);
  if (index >= 0) {
    list[index] = { ...list[index], pinned };
    writeConversations(list);
  }
}

export function deleteConversation(id: string) {
  writeConversations(readConversations().filter((conversation) => conversation.id !== id));
}

export function clearConversations() {
  writeConversations([]);
}

export function repairConversationStatuses() {
  const list = readConversations();
  let changed = false;
  const repaired = list.map((conversation) => {
    const turns = conversation.turns.map((turn) => {
      if (turn.status === 'pending' && turn.items && turn.items.length > 0) {
        changed = true;
        return { ...turn, status: 'complete' as const };
      }
      return turn;
    });
    return turns === conversation.turns ? conversation : { ...conversation, turns };
  });
  if (changed) writeConversations(repaired);
}

export function appendTurn(id: string, title: string, turn: ConversationTurn) {
  const existing = getConversation(id);
  const now = new Date().toISOString();
  const conversation: Conversation = existing
    ? { ...existing, updatedAt: now, turns: [...existing.turns, turn] }
    : { id, title, titleSource: 'automatic', createdAt: now, updatedAt: now, turns: [turn] };
  saveConversation(conversation);
  return conversation;
}

export function updateTurnItems(id: string, turnId: string, items: ConversationTurn['items']) {
  const existing = getConversation(id);
  if (!existing) return;
  const turns = existing.turns.map((turn) => (turn.id === turnId ? { ...turn, items, status: 'complete' as const } : turn));
  saveConversation({ ...existing, turns, updatedAt: new Date().toISOString() });
}

export function refineConversationTitle(id: string, title: string) {
  const existing = getConversation(id);
  if (!existing || existing.titleSource === 'manual' || existing.turns.length !== 1) return;
  const next = title.trim();
  if (!next || next === existing.title) return;
  saveConversation({ ...existing, title: next, titleSource: 'automatic' });
}

export function useConversations() {
  const [list, setList] = useState<Conversation[]>(() => readConversations());
  useEffect(() => {
    const refresh = () => setList(readConversations());
    window.addEventListener(CONVERSATIONS_EVENT, refresh);
    window.addEventListener('storage', refresh);
    return () => {
      window.removeEventListener(CONVERSATIONS_EVENT, refresh);
      window.removeEventListener('storage', refresh);
    };
  }, []);
  return list;
}

export function newConversationId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}
