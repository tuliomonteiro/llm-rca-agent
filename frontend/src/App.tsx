import { useState } from 'react'
import './App.css'
import { AnalysisResult, ApiError } from './types'
import IncidentForm from './components/IncidentForm'
import RCAReportView from './components/RCAReportView'
import FallbackReportView from './components/FallbackReportView'
import { isRCAReport } from './types'

type AppState = 'idle' | 'loading' | 'success' | 'error'

export default function App() {
  const [state, setState] = useState<AppState>('idle')
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string>('')
  const [incident, setIncident] = useState<string>('')

  const handleAnalyze = async (text: string) => {
    setState('loading')
    setError('')
    setResult(null)
    setIncident(text)

    try {
      const res = await fetch('/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ incident: text }),
      })

      if (!res.ok) {
        const errData: ApiError = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }))
        throw new Error(errData.detail || `Request failed with status ${res.status}`)
      }

      const data: AnalysisResult = await res.json()
      setResult(data)
      setState('success')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred')
      setState('error')
    }
  }

  const handleReset = () => {
    setState('idle')
    setResult(null)
    setError('')
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-inner">
          <div className="logo">
            <span className="logo-icon">⚡</span>
            <div>
              <h1>LLM RCA Agent</h1>
              <p>AI-powered Root Cause Analysis for production incidents</p>
            </div>
          </div>
          <div className="header-badges">
            <span className="badge badge-ai">Powered by Gemini</span>
            <span className="badge badge-rag">RAG-enhanced</span>
          </div>
        </div>
      </header>

      <main className="app-main">
        <div className="container">
          {state !== 'success' && (
            <IncidentForm
              onSubmit={handleAnalyze}
              loading={state === 'loading'}
              initialValue={state === 'error' ? incident : ''}
            />
          )}

          {state === 'loading' && (
            <div className="analysis-progress">
              <div className="spinner-ring" />
              <div className="progress-text">
                <p className="progress-title">Analyzing incident...</p>
                <p className="progress-sub">Retrieving similar incidents and runbooks from knowledge base</p>
              </div>
            </div>
          )}

          {state === 'error' && (
            <div className="error-banner">
              <span className="error-icon">⚠</span>
              <div>
                <strong>Analysis failed</strong>
                <p>{error}</p>
              </div>
            </div>
          )}

          {state === 'success' && result && (
            <div className="result-wrapper">
              <div className="result-actions">
                <button className="btn btn-outline" onClick={handleReset}>
                  ← Analyze another incident
                </button>
              </div>

              <div className="incident-recap">
                <span className="recap-label">Incident</span>
                <p className="recap-text">{incident}</p>
              </div>

              {isRCAReport(result) ? (
                <RCAReportView report={result} />
              ) : (
                <FallbackReportView report={result} />
              )}
            </div>
          )}
        </div>
      </main>

      <footer className="app-footer">
        <p>LLM RCA Agent — RAG-powered incident analysis using local embeddings + Gemini/Ollama</p>
      </footer>
    </div>
  )
}
