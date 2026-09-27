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
} from '../constants/tokens'
import { SectionLabel } from './primitives'
import type { ComparisonField } from '../types'

interface ComparisonReportProps {
  fields: ComparisonField[]
  siName?: string
  blName?: string
  subject?: string
  summary?: string
}

// Shared SI-vs-BL comparison table + mismatch detail cards, used by both
// ComparisonPage (the full report view) and ReviewDetailPage (the human
// review queue, so a reviewer sees what actually triggered "Needs Review"
// instead of resolving it blind).
export function ComparisonReport({ fields, siName, blName, subject, summary }: ComparisonReportProps) {
  const mismatches = fields.filter(f => !f.match)

  return (
    <>
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 20, gap: 16 }}>
        <div style={{ minWidth: 0 }}>
          <h2 style={{ fontFamily: 'Playfair Display, serif', fontSize: 26, fontWeight: 700, color: ink, margin: '0 0 6px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{subject || 'BL Comparison'}</h2>
          <p style={{ fontSize: 12, color: muted, margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{siName || 'Shipping_Instruction.pdf'} · {blName || 'Draft_Bill_of_Lading.pdf'}</p>
          {summary && <p style={{ fontSize: 12, color: muted, marginTop: 6, lineHeight: 1.5 }}>{summary}</p>}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 16px', background: mismatches.length > 0 ? amberBg : '#DCFCE7', border: `1px solid ${mismatches.length > 0 ? amberBdr : '#86EFAC'}`, borderRadius: 4, fontSize: 12, fontWeight: 700, color: mismatches.length > 0 ? '#92400E' : green, whiteSpace: 'nowrap' }}>
          {mismatches.length > 0 ? `⚠ ${mismatches.length} mismatch${mismatches.length !== 1 ? 'es' : ''} found` : '✓ All fields match'}
        </div>
      </div>

      <div style={{ border: `1px solid ${border}`, borderRadius: 4, overflow: 'hidden', background: white, marginBottom: 20 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
          <thead>
            <tr style={{ background: surface, borderBottom: `1px solid ${borderLight}` }}>
              {['Field', 'Shipping Instruction', 'Bill of Lading', 'Status'].map(h => (
                <th key={h} style={{ padding: '12px 20px', textAlign: 'left', fontSize: 11, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: muted }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {fields.map((f, i) => (
              <tr key={f.field} style={{ background: f.match ? 'white' : amberBg, borderBottom: i < fields.length - 1 ? `1px solid ${borderLight}` : 'none' }}>
                <td style={{ padding: '13px 20px', fontWeight: 600, color: ink }}>{f.field}</td>
                <td style={{ padding: '13px 20px', color: ink }}>{f.si}</td>
                <td style={{ padding: '13px 20px', fontWeight: f.match ? 400 : 700, color: f.match ? ink : '#92400E' }}>{f.bl}</td>
                <td style={{ padding: '13px 20px' }}>
                  {f.match
                    ? <span style={{ fontSize: 10, fontWeight: 700, color: green, letterSpacing: '0.06em', textTransform: 'uppercase' }}>✓ Match</span>
                    : <span style={{ fontSize: 10, fontWeight: 700, color: amber, letterSpacing: '0.06em', textTransform: 'uppercase' }}>⚠ Mismatch</span>
                  }
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {mismatches.length > 0 && (
        <div style={{ border: `1px solid ${amberBdr}`, borderRadius: 4, overflow: 'hidden', background: white }}>
          <div style={{ padding: '12px 20px', background: amberBg, borderBottom: `1px solid ${amberBdr}` }}>
            <SectionLabel>Attention Required</SectionLabel>
          </div>
          {mismatches.map(f => (
            <div key={f.field} style={{ padding: '20px 24px' }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: ink, marginBottom: 12 }}>{f.field}</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12 }}>
                <div style={{ padding: '16px 20px', border: `1px solid ${border}`, borderRadius: 4, background: surface }}>
                  <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase', color: muted, marginBottom: 8 }}>Shipping Instruction</div>
                  <div style={{ fontFamily: 'Playfair Display, serif', fontSize: 32, fontWeight: 700, color: navy }}>{f.si}</div>
                </div>
                <div style={{ padding: '16px 20px', border: `1px solid ${amberBdr}`, borderRadius: 4, background: amberBg }}>
                  <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase', color: amber, marginBottom: 8 }}>Bill of Lading</div>
                  <div style={{ fontFamily: 'Playfair Display, serif', fontSize: 32, fontWeight: 700, color: '#92400E' }}>{f.bl}</div>
                </div>
              </div>
              <p style={{ fontSize: 11, color: faint, marginTop: 10 }}>Values do not match. Verify with issuing party before proceeding.</p>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
