export interface RCAReport {
  root_cause: string
  contributing_factors: string[]
  impact: string
  timeline: string
  immediate_actions: string[]
  prevention: string[]
  confidence: string
}

export interface FallbackReport {
  message: string
  raw_analysis: string
  recommendation: string
}

export type AnalysisResult = RCAReport | FallbackReport

export function isRCAReport(result: AnalysisResult): result is RCAReport {
  return 'root_cause' in result
}

export interface ApiError {
  detail: string
}
