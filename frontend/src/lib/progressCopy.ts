import type { AnalysisInputType } from './types';

export const ANALYSIS_STAGES = [
  'Reading your document',
  'Understanding its structure',
  'Extracting relevant terms',
  'Reviewing privacy and data practices',
  'Reviewing payments and subscriptions',
  'Reviewing important contract terms',
  'Preparing your summary'
] as const;

export const ANALYSIS_COMPLETE = 'Analysis complete';

const FIRST_MESSAGE: Record<AnalysisInputType, string> = {
  text: 'Analyzing your text\u2026',
  image: 'Analyzing your image\u2026',
  pdf: 'Analyzing your PDF\u2026',
  document: 'Analyzing your document\u2026',
  spreadsheet: 'Analyzing your spreadsheet\u2026',
  presentation: 'Analyzing your presentation\u2026',
  url: 'Analyzing the webpage\u2026',
  files: 'Analyzing your files\u2026'
};

export function getAnalyzingLabel(type: AnalysisInputType): string {
  return FIRST_MESSAGE[type];
}


export function getProgressPlan(type: AnalysisInputType): string[] {
  const reading = type === 'url' ? 'Reading the webpage\u2026' : 'Reading your document\u2026';
  return [
    FIRST_MESSAGE[type],
    reading,
    ...ANALYSIS_STAGES.slice(1).map(stage => `${stage}\u2026`)
  ];
}
