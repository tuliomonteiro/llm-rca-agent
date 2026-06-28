import { RCAReport } from '../types'
import './RCAReportView.css'

interface Props {
  report: RCAReport
}

function confidenceColor(confidence: string): 'high' | 'medium' | 'low' {
  const upper = confidence.toUpperCase()
  if (upper.startsWith('HIGH')) return 'high'
  if (upper.startsWith('LOW')) return 'low'
  return 'medium'
}

interface SectionProps {
  icon: string
  title: string
  children: React.ReactNode
  accent?: string
}

function Section({ icon, title, children, accent }: SectionProps) {
  return (
    <div className={`rca-section ${accent ? `accent-${accent}` : ''}`}>
      <div className="section-header">
        <span className="section-icon">{icon}</span>
        <h3 className="section-title">{title}</h3>
      </div>
      <div className="section-body">{children}</div>
    </div>
  )
}

function List({ items }: { items: string[] }) {
  return (
    <ul className="rca-list">
      {items.map((item, i) => (
        <li key={i}>{item}</li>
      ))}
    </ul>
  )
}

export default function RCAReportView({ report }: Props) {
  const confLevel = confidenceColor(report.confidence)

  const handleCopy = () => {
    const text = [
      `ROOT CAUSE\n${report.root_cause}`,
      `\nCONTRIBUTING FACTORS\n${report.contributing_factors.map(f => `• ${f}`).join('\n')}`,
      `\nIMPACT\n${report.impact}`,
      `\nTIMELINE\n${report.timeline}`,
      `\nIMMEDIATE ACTIONS\n${report.immediate_actions.map(a => `• ${a}`).join('\n')}`,
      `\nPREVENTION\n${report.prevention.map(p => `• ${p}`).join('\n')}`,
      `\nCONFIDENCE\n${report.confidence}`,
    ].join('\n')
    navigator.clipboard.writeText(text).catch(() => {})
  }

  return (
    <div className="rca-report">
      <div className="report-toolbar">
        <div className="report-title-row">
          <h2 className="report-title">Root Cause Analysis Report</h2>
          <span className={`confidence-badge conf-${confLevel}`}>
            {confLevel === 'high' ? '✓' : confLevel === 'low' ? '!' : '~'} {report.confidence}
          </span>
        </div>
        <button className="copy-btn" onClick={handleCopy} title="Copy report to clipboard">
          <span>📋</span> Copy report
        </button>
      </div>

      <Section icon="🔍" title="Root Cause" accent="red">
        <p className="root-cause-text">{report.root_cause}</p>
      </Section>

      <div className="two-col">
        <Section icon="⚠️" title="Contributing Factors">
          <List items={report.contributing_factors} />
        </Section>

        <Section icon="📊" title="Impact">
          <p>{report.impact}</p>
        </Section>
      </div>

      <Section icon="🕐" title="Timeline">
        <p className="timeline-text">{report.timeline}</p>
      </Section>

      <div className="two-col">
        <Section icon="🚨" title="Immediate Actions" accent="orange">
          <List items={report.immediate_actions} />
        </Section>

        <Section icon="🛡️" title="Prevention" accent="green">
          <List items={report.prevention} />
        </Section>
      </div>
    </div>
  )
}
