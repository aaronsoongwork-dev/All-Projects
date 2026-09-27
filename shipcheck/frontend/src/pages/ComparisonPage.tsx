import {
  white,
  border,
  navy,
  ink,
  muted,
} from '../constants/tokens'
import { SectionLabel } from '../components/primitives'
import { ComparisonReport } from '../components/ComparisonReport'
import type { ComparisonField } from '../types'

interface ComparisonPageProps {
  fields?: ComparisonField[]
  siName?: string
  blName?: string
  subject?: string
  onBack: () => void
  onGoToUpload?: () => void
}

export function ComparisonPage({ fields, siName, blName, subject, onBack, onGoToUpload }: ComparisonPageProps) {
  const comparisonRows = fields || []

  if (comparisonRows.length === 0) {
    return (
      <div style={{ padding: 28 }}>
        <button onClick={onBack} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: navy, border: `1px solid ${border}`, background: white, cursor: 'pointer', padding: '7px 14px', borderRadius: 4, marginBottom: 24 }}>← Back</button>
        <SectionLabel>Shipment Comparison — SI vs Bill of Lading</SectionLabel>

        <div style={{ border: `1px solid ${border}`, borderRadius: 4, background: white, padding: '48px 24px', textAlign: 'center' }}>
          <div style={{ fontSize: 32, marginBottom: 12, opacity: 0.4 }}>📊</div>
          <h3 style={{ fontFamily: 'Playfair Display, serif', fontSize: 20, fontWeight: 700, color: ink, margin: '0 0 8px' }}>No Comparison Data Found</h3>
          <p style={{ fontSize: 13, color: muted, maxWidth: 460, margin: '0 auto 20px', lineHeight: 1.5 }}>
            No comparison has been executed yet for this record. You can upload and compare custom Shipping Instructions and Bills of Lading in the Upload tool.
          </p>
          {onGoToUpload && (
            <button
              onClick={onGoToUpload}
              style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', padding: '11px 24px', background: navy, color: white, border: 'none', borderRadius: 4, cursor: 'pointer' }}
            >
              Go to Upload & Compare →
            </button>
          )}
        </div>
      </div>
    )
  }

  return (
    <div style={{ padding: 28 }}>
      <button onClick={onBack} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: navy, border: `1px solid ${border}`, background: white, cursor: 'pointer', padding: '7px 14px', borderRadius: 4, marginBottom: 24 }}>← Back</button>
      <SectionLabel>Shipment Comparison — SI vs Bill of Lading</SectionLabel>
      <ComparisonReport fields={comparisonRows} siName={siName} blName={blName} subject={subject} />
    </div>
  )
}

