import { useState, useEffect } from 'react'
import './IncidentForm.css'

const MAX_CHARS = 8000
const PLACEHOLDER = `Describe the incident in detail. Include:
• When it started (timestamp, timezone)
• What was deployed or changed
• Error messages from logs
• Which services/endpoints are affected
• Current error rates or impact metrics

Example:
2024-03-15 11:30 UTC - Deployed auth-api v3.1.0. Error rate jumped to 45% at 11:45. Logs show: FATAL connection pool exhausted (pool_size=10). All /login endpoints returning 503.`

const EXAMPLES = [
  {
    label: 'DB Connection Pool',
    text: '2024-03-15 11:30 UTC - Deployed auth-api v3.1.0. Error rate jumped to 45% at 11:45. Logs: FATAL connection pool exhausted (pool_size=10). All /login endpoints returning 503. Rollback to v2.4.0 at 11:58 resolved the issue.',
  },
  {
    label: 'OOM Worker Crash',
    text: '2024-04-02 03:15 UTC - report-worker pods started OOMKilling (limit: 512Mi). Memory climbed from 200MB to 512MB over 20 minutes. Heap dumps show large in-memory cache growing unbounded. 1,200 pending reports queued.',
  },
  {
    label: 'High CPU Spike',
    text: '2024-05-10 14:00 UTC - CPU on api-gateway jumped to 100% after traffic spike. p99 latency went from 50ms to 8s. Autoscaler was disabled due to maintenance. No recent deployments.',
  },
]

interface Props {
  onSubmit: (text: string) => void
  loading: boolean
  initialValue?: string
}

export default function IncidentForm({ onSubmit, loading, initialValue = '' }: Props) {
  const [text, setText] = useState(initialValue)

  useEffect(() => {
    if (initialValue) setText(initialValue)
  }, [initialValue])

  const charCount = text.length
  const overLimit = charCount > MAX_CHARS
  const canSubmit = text.trim().length > 0 && !overLimit && !loading

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (canSubmit) onSubmit(text.trim())
  }

  return (
    <div className="form-card">
      <div className="form-header">
        <h2>Incident Description</h2>
        <p>Paste your incident details below and the AI will generate a structured Root Cause Analysis report.</p>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="textarea-wrapper">
          <textarea
            className={`incident-textarea ${overLimit ? 'over-limit' : ''}`}
            value={text}
            onChange={e => setText(e.target.value)}
            placeholder={PLACEHOLDER}
            rows={9}
            disabled={loading}
            aria-label="Incident description"
          />
          <div className={`char-counter ${overLimit ? 'over-limit' : charCount > MAX_CHARS * 0.9 ? 'near-limit' : ''}`}>
            {charCount.toLocaleString()} / {MAX_CHARS.toLocaleString()}
          </div>
        </div>

        {overLimit && (
          <p className="field-error">
            Input exceeds {MAX_CHARS.toLocaleString()} character limit by {(charCount - MAX_CHARS).toLocaleString()} characters.
          </p>
        )}

        <div className="form-footer">
          <div className="example-section">
            <span className="example-label">Try an example:</span>
            <div className="example-buttons">
              {EXAMPLES.map(ex => (
                <button
                  key={ex.label}
                  type="button"
                  className="example-btn"
                  onClick={() => setText(ex.text)}
                  disabled={loading}
                >
                  {ex.label}
                </button>
              ))}
            </div>
          </div>

          <button
            type="submit"
            className={`btn btn-primary submit-btn ${loading ? 'loading' : ''}`}
            disabled={!canSubmit}
          >
            {loading ? (
              <>
                <span className="btn-spinner" />
                Analyzing...
              </>
            ) : (
              <>
                <span>⚡</span>
                Analyze Incident
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
