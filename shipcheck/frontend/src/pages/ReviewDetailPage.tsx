import { useEffect, useState } from 'react'
import {
  surface,
  white,
  border,
  borderLight,
  navy,
  ink,
  muted,
  amber,
  amberBg,
  amberBdr,
  green,
  greenBg,
} from '../constants/tokens'
import { SectionLabel, Spinner } from '../components/primitives'
import { ComparisonReport } from '../components/ComparisonReport'
import { getComparisonsApi, reviewComparisonApi, type ComparisonField } from '../services/api'
import type { GmailEmail, UserInfo } from '../types'

interface ReviewDetailPageProps {
  id: string
  emails: GmailEmail[]
  user?: UserInfo | null
  onBack: () => void
  onResolve?: (id: string, newStatus: 'Match' | 'Mismatch') => void
}

export function ReviewDetailPage({ id, emails, user, onBack, onResolve }: ReviewDetailPageProps) {
  const item = emails.find(e => e.id === id)
  const [resolvedStatus, setResolvedStatus] = useState<'Match' | 'Mismatch' | null>(null)
  const [saving, setSaving] = useState<'Match' | 'Mismatch' | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [comparisonId, setComparisonId] = useState<number | null>(item?.comparisonId ?? null)
  const [fields, setFields] = useState<ComparisonField[] | null>(item?.fields ?? null)
  const [summary, setSummary] = useState<string | undefined>(undefined)
  const [loadingComparison, setLoadingComparison] = useState(!item?.fields)

  useEffect(() => {
    setResolvedStatus(null)
    setError(null)
    if (item?.fields && item?.comparisonId) {
      setComparisonId(item.comparisonId)
      setFields(item.fields)
      setLoadingComparison(false)
      return
    }
    if (!item) return
    setLoadingComparison(true)
    getComparisonsApi(1, 0, item.id)
      .then(records => {
        const rec = records[0]
        if (rec) {
          setComparisonId(rec.id)
          setFields(rec.fields || [])
          setSummary(rec.summary)
        }
      })
      .catch(err => {
        console.warn(`Failed to fetch comparison for review item ${item.id}:`, err)
      })
      .finally(() => setLoadingComparison(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [item?.id])

  if (!item) {
    return (
      <div style={{ padding: 28 }}>
        <button onClick={onBack} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: navy, border: `1px solid ${border}`, background: white, cursor: 'pointer', padding: '7px 14px', borderRadius: 4, marginBottom: 24 }}>← Back to Review</button>
        <div style={{ border: '1px solid #FECACA', borderRadius: 4, background: '#FEF2F2', padding: '16px 20px', color: '#991B1B', fontSize: 13 }}>
          ⚠ Review item with ID <code>{id}</code> was not found. It may have already been resolved.
        </div>
      </div>
    )
  }

  async function handleAction(status: 'Match' | 'Mismatch') {
    setError(null)
    if (!comparisonId) {
      // No linked comparison record to persist against - fall back to local-only
      // resolution so the reviewer isn't blocked, but they should know it didn't save.
      setError('No linked comparison record was found, so this resolution could not be saved. It will only apply to this session.')
      setResolvedStatus(status)
      onResolve?.(item!.id, status)
      return
    }
    setSaving(status)
    try {
      await reviewComparisonApi(comparisonId, { reviewed: true, reviewed_by: user?.email, status })
      setResolvedStatus(status)
      onResolve?.(item!.id, status)
    } catch (err: any) {
      setError(err.message || 'Failed to save this resolution.')
    } finally {
      setSaving(null)
    }
  }

  return (
    <div style={{ padding: 28 }}>
      <button onClick={onBack} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: navy, border: `1px solid ${border}`, background: white, cursor: 'pointer', padding: '7px 14px', borderRadius: 4, marginBottom: 24 }}>← Back to Review</button>

      <div style={{ border: `1px solid ${amberBdr}`, borderRadius: 4, background: amberBg, padding: '16px 20px', marginBottom: 20 }}>
        <div style={{ fontFamily: 'Playfair Display, serif', fontSize: 18, fontWeight: 700, color: '#92400E', marginBottom: 4 }}>⚠ Review Required</div>
        <p style={{ fontSize: 13, color: '#92400E', margin: 0 }}>This email document requires manual operator verification and resolution.</p>
      </div>

      <div style={{ border: `1px solid ${border}`, borderRadius: 4, background: white, padding: '20px 24px', marginBottom: 20 }}>
        <SectionLabel>Email Details</SectionLabel>
        <h3 style={{ fontFamily: 'Playfair Display, serif', fontSize: 20, fontWeight: 700, color: navy, margin: '0 0 10px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.subject}</h3>
        <div style={{ fontSize: 12, color: muted, marginBottom: 12 }}>
          From: <strong style={{ color: ink }}>{item.fromName}</strong> ({item.from}) · Date: {item.date}
        </div>
        <div style={{ padding: '12px 16px', background: surface, borderRadius: 4, fontSize: 13, color: ink, lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
          {item.body || item.snippet || 'No message content available.'}
        </div>
      </div>

      {loadingComparison ? (
        <div style={{ border: `1px solid ${border}`, borderRadius: 4, background: white, padding: '32px 24px', marginBottom: 20, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
          <Spinner size={14} color={navy} />
          <span style={{ fontSize: 13, color: muted }}>Loading comparison details…</span>
        </div>
      ) : fields && fields.length > 0 ? (
        <div style={{ marginBottom: 20 }}>
          <ComparisonReport fields={fields} subject={undefined} summary={summary} />
        </div>
      ) : (
        <div style={{ border: `1px solid ${borderLight}`, borderRadius: 4, background: surface, padding: '16px 24px', marginBottom: 20 }}>
          <p style={{ fontSize: 13, color: muted, margin: 0 }}>No extracted field data is available for this comparison - it may have been flagged before extraction completed (e.g. an unidentifiable or unreadable attachment).</p>
        </div>
      )}

      {error && (
        <div style={{ border: '1px solid #FECACA', borderRadius: 4, background: '#FEF2F2', padding: '12px 16px', marginBottom: 20, fontSize: 12, color: '#991B1B' }}>
          ⚠ {error}
        </div>
      )}

      {resolvedStatus ? (
        <div style={{ border: `1px solid #86EFAC`, borderRadius: 4, background: greenBg, padding: '16px 24px', display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ color: green, fontWeight: 700 }}>✓</span>
          <span style={{ fontSize: 13, fontWeight: 600, color: green }}>Case marked as {resolvedStatus} and resolved successfully.</span>
        </div>
      ) : (
        <div style={{ border: `1px solid ${border}`, borderRadius: 4, background: white, padding: '20px 24px' }}>
          <SectionLabel>Resolution Action</SectionLabel>
          <p style={{ fontSize: 12, color: muted, marginBottom: 16 }}>Select an outcome to update the shipment status:</p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
            <button
              onClick={() => handleAction('Match')}
              disabled={!!saving}
              style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', padding: '10px 20px', background: '#166534', color: white, border: 'none', borderRadius: 4, cursor: saving ? 'not-allowed' : 'pointer', opacity: saving ? 0.6 : 1, display: 'inline-flex', alignItems: 'center', gap: 8 }}
            >
              {saving === 'Match' && <Spinner size={12} color={white} />} ✓ Confirm Match
            </button>
            <button
              onClick={() => handleAction('Mismatch')}
              disabled={!!saving}
              style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', padding: '10px 20px', background: amberBg, color: amber, border: `1px solid ${amberBdr}`, borderRadius: 4, cursor: saving ? 'not-allowed' : 'pointer', opacity: saving ? 0.6 : 1, display: 'inline-flex', alignItems: 'center', gap: 8 }}
            >
              {saving === 'Mismatch' && <Spinner size={12} color={amber} />} ⚠ Mark Mismatch
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
