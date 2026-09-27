import { useState } from 'react'
import {
  surface,
  white,
  border,
  borderLight,
  navy,
  ink,
  muted,
  faint,
  amberBg,
  amberBdr,
} from '../constants/tokens'
import { ReviewSkeleton, SearchInput } from '../components/primitives'
import type { GmailEmail } from '../types'

interface ReviewPageProps {
  emails: GmailEmail[]
  onSelect: (id: string) => void
  loading?: boolean
}

export function ReviewPage({ emails, onSelect, loading }: ReviewPageProps) {
  const [search, setSearch] = useState('')

  if (loading && emails.length === 0) {
    return <ReviewSkeleton />
  }

  const allReviewItems = emails.filter(e => e.status === 'Needs Review')
  const reviewItems = search
    ? allReviewItems.filter(e =>
        e.subject.toLowerCase().includes(search.toLowerCase()) ||
        e.fromName.toLowerCase().includes(search.toLowerCase()) ||
        e.from.toLowerCase().includes(search.toLowerCase())
      )
    : allReviewItems

  return (
    <div style={{ padding: 28 }}>
      {allReviewItems.length > 0 && (
        <div style={{ border: `1px solid ${amberBdr}`, borderRadius: 4, background: amberBg, padding: '10px 16px', marginBottom: 20, fontSize: 12, color: '#92400E' }}>
          ⚠ {allReviewItems.length} {allReviewItems.length === 1 ? 'case requires' : 'cases require'} manual review and resolution.
        </div>
      )}

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginBottom: 20, alignItems: 'center' }}>
        <SearchInput value={search} onChange={setSearch} placeholder="Search review queue…" />
        <div style={{ marginLeft: 'auto', fontSize: 12, color: faint }}>{reviewItems.length} case{reviewItems.length !== 1 ? 's' : ''}</div>
      </div>

      <div style={{ border: `1px solid ${border}`, borderRadius: 4, overflow: 'hidden', background: white }}>
        <table className="review-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
          <thead>
            <tr style={{ background: surface, borderBottom: `1px solid ${borderLight}` }}>
              {['Email / Document', 'Sender', 'Received', ''].map(h => (
                <th key={h} style={{ padding: '10px 20px', textAlign: 'left', fontSize: 9, fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase', color: muted }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {reviewItems.length > 0 ? (
              reviewItems.map((r, i) => (
                <tr key={r.id} style={{ borderBottom: i < reviewItems.length - 1 ? `1px solid ${borderLight}` : 'none' }}>
                  <td style={{ padding: '13px 20px', fontWeight: 600, color: ink, maxWidth: 320 }}>
                    <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.subject}</div>
                    <div style={{ fontSize: 11, color: muted, fontWeight: 400, marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.snippet}</div>
                  </td>
                  <td style={{ padding: '13px 20px', color: muted, fontSize: 12, whiteSpace: 'nowrap' }}>{r.fromName || r.from}</td>
                  <td style={{ padding: '13px 20px', fontSize: 11, color: faint, whiteSpace: 'nowrap' }}>{r.date}</td>
                  <td style={{ padding: '13px 20px', textAlign: 'right', whiteSpace: 'nowrap' }}>
                    <button onClick={() => onSelect(r.id)} style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', padding: '6px 14px', border: `1px solid ${border}`, borderRadius: 3, background: 'none', cursor: 'pointer', color: navy }}>
                      Review
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={4} style={{ padding: '48px 20px', textAlign: 'center', color: muted, fontSize: 13 }}>
                  {search ? 'No review cases match your search.' : '✓ All clear. No documents or emails currently require human review.'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

