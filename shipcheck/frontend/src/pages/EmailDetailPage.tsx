import { useEffect, useState } from 'react'
import type { GmailEmail } from '../types'
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
} from '../constants/tokens'
import { SectionLabel, Badge, Spinner } from '../components/primitives'
import { getEmailAttachmentsApi, getAttachmentDownloadUrl } from '../services/api'

interface EmailDetailPageProps {
  email: GmailEmail
  onBack: () => void
  onProcess: () => void
  isComparing?: boolean
  gmailConnected?: boolean
  onGoToSettings?: () => void
  compareError?: string | null
}

export function EmailDetailPage({ email, onBack, onProcess, isComparing, gmailConnected, onGoToSettings, compareError }: EmailDetailPageProps) {
  const isDoc = email.type === 'Document Comparison'
  const isPending = email.status === 'New' || email.status === 'Processing'
  const needsGmail = isPending && !gmailConnected

  const [attachmentNames, setAttachmentNames] = useState<string[] | null>(null)
  const [attachmentsLoading, setAttachmentsLoading] = useState(false)

  useEffect(() => {
    setAttachmentNames(null)
    if (!email.hasAttachments) return
    setAttachmentsLoading(true)
    getEmailAttachmentsApi(email.id)
      .then(setAttachmentNames)
      .catch(err => {
        console.warn(`Failed to list attachments for ${email.id}:`, err)
        setAttachmentNames(null)
      })
      .finally(() => setAttachmentsLoading(false))
  }, [email.id, email.hasAttachments])
  return (
    <div style={{ padding: 28 }}>
      <button onClick={onBack} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: navy, border: `1px solid ${border}`, background: white, cursor: 'pointer', padding: '7px 14px', borderRadius: 4, marginBottom: 24 }}>← Back to Inbox</button>

      <div style={{ border: `1px solid ${border}`, borderRadius: 4, background: white, padding: '24px 28px', marginBottom: 16 }}>
        <h2 style={{ fontFamily: 'Playfair Display, serif', fontSize: 24, fontWeight: 700, color: ink, margin: '0 0 18px' }}>{email.subject}</h2>
        <div style={{ display: 'grid', gridTemplateColumns: '60px 1fr', gap: '8px 12px', fontSize: 14, marginBottom: 16 }}>
          <span style={{ color: muted, fontWeight: 600, fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', paddingTop: 2 }}>From</span><span style={{ color: ink, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{email.fromName} &lt;{email.from}&gt;</span>
          <span style={{ color: muted, fontWeight: 600, fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', paddingTop: 2 }}>Date</span><span style={{ color: ink }}>{email.date}</span>
        </div>
        <div style={{ display: 'flex', gap: 6, paddingTop: 12, borderTop: `1px solid ${borderLight}` }}>
          <Badge label={email.status === 'Processing' ? 'Processing' : email.type} />
          {isDoc && email.status !== 'Processing' && <Badge label={email.status} />}
        </div>
      </div>

      {email.body && (
        <div style={{ border: `1px solid ${border}`, borderRadius: 4, background: white, padding: '20px 24px', marginBottom: 16 }}>
          <SectionLabel>Message</SectionLabel>
          <p style={{ fontSize: 14, color: ink, lineHeight: 1.7, whiteSpace: 'pre-line', margin: 0 }}>{email.body}</p>
        </div>
      )}

      {email.hasAttachments && (
        <div style={{ border: `1px solid ${border}`, borderRadius: 4, background: white, padding: '20px 24px', marginBottom: 16 }}>
          <SectionLabel>Attachments</SectionLabel>
          {attachmentsLoading ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', border: `1px solid ${borderLight}`, borderRadius: 4, background: surface }}>
              <Spinner size={14} color={navy} />
              <span style={{ fontSize: 12, color: muted }}>Checking attachments…</span>
            </div>
          ) : attachmentNames && attachmentNames.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {attachmentNames.map(name => (
                <div key={name} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', border: `1px solid ${borderLight}`, borderRadius: 4, background: surface }}>
                  <span style={{ flex: 1, fontSize: 12, fontWeight: 600, color: ink, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{name}</span>
                  <a
                    href={getAttachmentDownloadUrl(email.id, name)}
                    download={name}
                    style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', padding: '5px 10px', border: `1px solid ${border}`, borderRadius: 3, background: white, color: navy, textDecoration: 'none', whiteSpace: 'nowrap' }}
                  >
                    Download
                  </a>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ padding: '10px 14px', border: `1px solid ${borderLight}`, borderRadius: 4, background: surface }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: ink }}>Attachments detected on message</div>
              <div style={{ fontSize: 11, color: muted }}>Couldn't list filenames right now - shipping documents are attached to this message thread.</div>
            </div>
          )}
        </div>
      )}

      {isDoc ? (
        <>
          {compareError && (
            <div style={{ border: '1px solid #FECACA', borderRadius: 4, background: '#FEF2F2', padding: '12px 16px', marginBottom: 12, fontSize: 12, color: '#991B1B' }}>
              ⚠ {compareError}
            </div>
          )}
          <div style={{ border: `1px solid ${border}`, borderRadius: 4, background: '#EEF2FF', padding: '16px 24px', display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#1E1B4B' }}>Compare SI vs Bill of Lading</div>
              <div style={{ fontSize: 11, color: '#3730A3', marginTop: 2 }}>
                {isComparing
                  ? 'Extracting and comparing attachments…'
                  : needsGmail
                  ? 'Gmail is not connected in this session - reconnect it to fetch this email\'s attachments.'
                  : 'Analyse 7 fields and surface discrepancies'}
              </div>
            </div>
            {isComparing ? (
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, fontSize: 12, fontWeight: 600, color: '#3730A3' }}>
                <Spinner size={14} color="#3730A3" /> Comparing…
              </div>
            ) : needsGmail ? (
              <button onClick={onGoToSettings} style={{ fontSize: 12, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', padding: '10px 20px', background: navy, color: white, border: 'none', borderRadius: 4, cursor: onGoToSettings ? 'pointer' : 'not-allowed' }}>
                Connect Gmail
              </button>
            ) : (
              <button onClick={onProcess} style={{ fontSize: 12, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', padding: '10px 20px', background: navy, color: white, border: 'none', borderRadius: 4, cursor: 'pointer' }}>
                {isPending ? 'Compare Now' : 'View Comparison Report'}
              </button>
            )}
          </div>
        </>
      ) : email.status === 'Processing' ? (
        <div style={{ border: `1px solid ${border}`, borderRadius: 4, background: surface, padding: '16px 24px', display: 'flex', alignItems: 'center', gap: 10 }}>
          <Spinner size={14} color={navy} />
          <p style={{ fontSize: 13, color: muted, margin: 0 }}>This email hasn't been classified yet.</p>
        </div>
      ) : (
        <div style={{ border: `1px solid ${borderLight}`, borderRadius: 4, background: surface, padding: '16px 24px' }}>
          <p style={{ fontSize: 13, color: muted, margin: 0 }}>This email is classified as <strong style={{ color: ink }}>{email.type}</strong> and does not require document comparison.</p>
        </div>
      )}
    </div>
  )
}

