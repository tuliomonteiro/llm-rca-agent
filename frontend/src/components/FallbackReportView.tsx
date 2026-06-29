import { FallbackReport } from '../types'
import './FallbackReportView.css'

interface Props {
  report: FallbackReport
}

export default function FallbackReportView({ report }: Props) {
  return (
    <div className="fallback-report">
      <div className="fallback-header">
        <span className="fallback-icon">🔍</span>
        <div>
          <h2>Limited Context Analysis</h2>
          <p>{report.message}</p>
        </div>
      </div>

      <div className="fallback-section">
        <div className="section-label">AI Analysis</div>
        <p className="fallback-analysis">{report.raw_analysis}</p>
      </div>

      <div className="fallback-tip">
        <span className="tip-icon">💡</span>
        <div>
          <strong>Improve future analyses</strong>
          <p>{report.recommendation}</p>
          <p className="tip-sub">
            Add <code>.md</code> or <code>.txt</code> runbooks and past incident reports to the <code>data/</code>
            directory, then re-run <code>python scripts/ingest.py</code> to index them.
          </p>
        </div>
      </div>
    </div>
  )
}
