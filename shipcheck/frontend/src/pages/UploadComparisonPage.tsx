import type { ComparisonField } from '../types'
import {
  surface,
  white,
  border,
  borderLight,
  navy,
  ink,
  muted,
  faint,
  amber,
  amberBg,
  amberBdr,
  green,
  greenBg,
} from '../constants/tokens'

interface UploadComparisonPageProps {
  result: ComparisonField[]
  siName: string
  blName: string
  onBack: () => void
}

export function UploadComparisonPage({ result, siName, blName, onBack }: UploadComparisonPageProps) {
  const mismatches = result.filter(f => !f.match)
  const unextracted = result.filter(f => f.si === '—' || f.bl === '—')

  return (
    <div style={{ padding: 28 }}>
      <button onClick={onBack} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: navy, border: `1px solid ${border}`, background: white, cursor: 'pointer', padding: '7px 14px', borderRadius: 4, marginBottom: 24 }}>← Upload New</button>

      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, marginBottom: 24 }}>
        <div style={{ minWidth: 0 }}>
          <h2 style={{ fontFamily: 'Playfair Display, serif', fontSize: 26, fontWeight: 700, color: ink, margin: '0 0 6px' }}>Comparison Result</h2>
          <p style={{ fontSize: 12, color: muted, margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{siName} · {blName}</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {mismatches.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 16px', background: amberBg, border: `1px solid ${amberBdr}`, borderRadius: 4, fontSize: 12, fontWeight: 700, color: '#92400E' }}>
              ⚠ {mismatches.length} mismatch{mismatches.length !== 1 ? 'es' : ''}
            </div>
          )}
          {mismatches.length === 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 16px', background: greenBg, border: '1px solid #86EFAC', borderRadius: 4, fontSize: 12, fontWeight: 700, color: green }}>
              ✓ All fields match
            </div>
          )}
        </div>
      </div>

      {unextracted.length > 0 && (
        <div style={{ border: `1px solid ${border}`, borderRadius: 4, background: surface, padding: '12px 16px', marginBottom: 20, fontSize: 12, color: muted }}>
          ℹ {unextracted.length} field{unextracted.length !== 1 ? 's' : ''} could not be extracted — the document may use a non-standard format or scanned image text.
        </div>
      )}

      <div style={{ border: `1px solid ${border}`, borderRadius: 4, overflow: 'hidden', background: white }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
          <thead>
            <tr style={{ background: surface, borderBottom: `1px solid ${borderLight}` }}>
              {['Field', 'Shipping Instruction', 'Bill of Lading', 'Status'].map(h => (
                <th key={h} style={{ padding: '12px 20px', textAlign: 'left', fontSize: 11, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: muted }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {result.map((f, i) => {
              const unread = f.si === '—' || f.bl === '—'
              return (
                <tr key={f.field} style={{ background: f.match ? 'white' : unread ? surface : amberBg, borderBottom: i < result.length - 1 ? `1px solid ${borderLight}` : 'none' }}>
                  <td style={{ padding: '14px 20px', fontWeight: 600, color: ink }}>{f.field}</td>
                  <td style={{ padding: '14px 20px', color: ink }}>{f.si}</td>
                  <td style={{ padding: '14px 20px', fontWeight: f.match ? 400 : 700, color: f.match ? ink : f.bl === '—' ? faint : '#92400E' }}>{f.bl}</td>
                  <td style={{ padding: '14px 20px' }}>
                    {unread
                      ? <span style={{ fontSize: 11, fontWeight: 700, color: faint, letterSpacing: '0.06em', textTransform: 'uppercase' }}>— Unextracted</span>
                      : f.match
                        ? <span style={{ fontSize: 11, fontWeight: 700, color: green, letterSpacing: '0.06em', textTransform: 'uppercase' }}>✓ Match</span>
                        : <span style={{ fontSize: 11, fontWeight: 700, color: amber, letterSpacing: '0.06em', textTransform: 'uppercase' }}>⚠ Mismatch</span>
                    }
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

