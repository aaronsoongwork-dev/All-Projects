import type { Page, GmailEmail, UserInfo, ClassifyingState } from '../types'
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
  green,
  red,
  redBg,
} from '../constants/tokens'
import { SectionLabel, Badge, Spinner, DashboardSkeleton } from '../components/primitives'

interface DashboardPageProps {
  emails: GmailEmail[]
  user: UserInfo | null
  onNav: (p: Page) => void
  onSelect: (id: string) => void
  loading?: boolean
  classifying?: ClassifyingState
  apiError?: string | null
  comparingIds?: Set<string>
}

export function DashboardPage({
  emails,
  user,
  onNav,
  onSelect,
  loading,
  classifying,
  apiError,
  comparingIds,
}: DashboardPageProps) {
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'
  const firstName = user?.name?.split(' ')[0] || 'User'

  const docComps = emails.filter(e => e.type === 'Document Comparison')
  const mismatches = emails.filter(e => e.status === 'Mismatch')
  const review = emails.filter(e => e.status === 'Needs Review')
  const attention = emails.filter(e => e.status === 'Mismatch' || e.status === 'Needs Review')
  const progressPercent = classifying?.total ? Math.round((classifying.current / classifying.total) * 100) : 0

  if (loading && emails.length === 0) {
    return <DashboardSkeleton greeting={greeting} firstName={firstName} />
  }

  return (
    <div style={{ padding: 28, flex: 1 }}>
      {/* Greeting */}
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontFamily: 'Playfair Display, serif', fontSize: 36, fontWeight: 700, color: ink, lineHeight: 1.1, margin: '0 0 14px' }}>
          {greeting}, <em style={{ fontStyle: 'italic', color: navy }}>{firstName}.</em>
        </h1>

        {/* Status strip — accent color only on actionable cells */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 1, background: border, border: `1px solid ${border}`, borderRadius: 4, overflow: 'hidden', marginBottom: 18 }}>
          {([
            { label: 'Emails', value: emails.length, sub: loading ? 'Fetching…' : 'in inbox', accent: null, click: () => onNav('inbox') },
            { label: 'Doc Checks', value: docComps.length, sub: `${docComps.filter(e => e.status === 'Match').length} matched`, accent: null, click: () => onNav('inbox') },
            { label: 'Mismatches', value: mismatches.length, sub: mismatches.length ? 'Action required' : 'All clear', accent: mismatches.length > 0 ? 'amber' : null, click: () => onNav('inbox') },
            { label: 'Needs Review', value: review.length, sub: review.length ? 'Human review' : 'None pending', accent: review.length > 0 ? 'red' : null, click: () => onNav('review') },
          ] as const).map((s, i) => {
            const bg = s.accent === 'amber' ? amberBg : s.accent === 'red' ? redBg : white
            const line = s.accent === 'amber' ? amber : s.accent === 'red' ? red : navy
            const text = s.accent === 'amber' ? '#92400E' : s.accent === 'red' ? red : navy
            const label = s.accent === 'amber' ? amber : s.accent === 'red' ? red : faint
            return (
              <button
                key={i}
                onClick={s.click}
                style={{ padding: '12px 18px', border: 'none', background: bg, cursor: 'pointer', textAlign: 'left', borderTop: s.accent ? `2px solid ${line}` : '2px solid transparent' }}
              >
                <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: label, marginBottom: 4 }}>{s.label}</div>
                <div style={{ fontFamily: 'Playfair Display, serif', fontSize: 28, fontWeight: 700, color: text, lineHeight: 1 }}>{s.value}</div>
                <div style={{ fontSize: 11, color: label, marginTop: 3 }}>{s.sub}</div>
              </button>
            )
          })}
        </div>

        {/* Initial Fetching Banner */}
        {loading && (
          <div style={{ background: '#F7F5EF', border: `1px solid ${border}`, borderRadius: 4, padding: '12px 18px', marginBottom: 18, display: 'flex', alignItems: 'center', gap: 10 }}>
            <Spinner size={14} color={navy} />
            <span style={{ fontSize: 12, fontWeight: 600, color: navy }}>Retrieving latest shipping emails from Gmail inbox…</span>
          </div>
        )}

        {/* Classification Progress Banner */}
        {classifying?.active && (
          <div style={{ background: '#EFF6FF', border: '1px solid #BFDBFE', borderRadius: 4, padding: '14px 20px', marginBottom: 18 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12, fontWeight: 600, color: '#1E40AF' }}>
                <Spinner size={14} color="#2563EB" />
                AI PIPELINE ACTIVE: Classifying emails with Claude Haiku ({classifying.current} of {classifying.total} analyzed)…
              </div>
              <span style={{ fontSize: 11, fontWeight: 700, color: '#2563EB' }}>
                {progressPercent}%
              </span>
            </div>
            <div style={{ width: '100%', height: 4, background: '#DBEAFE', borderRadius: 2, overflow: 'hidden' }}>
              <div style={{ width: `${progressPercent}%`, height: '100%', background: '#2563EB', transition: 'width 0.3s ease' }} />
            </div>
          </div>
        )}

        {/* Error Alert */}
        {(classifying?.error || apiError) && (
          <div style={{ background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: 4, padding: '12px 18px', marginBottom: 18, display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: '#991B1B', fontWeight: 500 }}>
            <span style={{ fontSize: 14 }}>⚠</span>
            <span><strong>Pipeline Error:</strong> {classifying?.error || apiError}</span>
          </div>
        )}
      </div>

      <div className="dashboard-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 20 }}>
        {/* Recent emails */}
        <div style={{ minWidth: 0 }}>
          <SectionLabel>Recent Activity</SectionLabel>
          <div style={{ border: `1px solid ${border}`, borderRadius: 4, overflow: 'hidden', background: white }}>
            {emails.length === 0 ? (
              <div style={{ padding: '36px 20px', textAlign: 'center', color: muted, fontSize: 13 }}>
                {loading ? (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
                    <Spinner size={14} color={navy} />
                    Retrieving emails from inbox…
                  </div>
                ) : (
                  'No emails loaded yet.'
                )}
              </div>
            ) : (
              emails.slice(0, 6).map((e, i) => (
                <button
                  key={e.id}
                  onClick={() => onSelect(e.id)}
                  style={{ width: '100%', display: 'flex', alignItems: 'flex-start', gap: 12, padding: '13px 20px', border: 'none', background: 'white', cursor: 'pointer', textAlign: 'left', borderBottom: i < 5 ? `1px solid ${borderLight}` : 'none' }}
                  onMouseEnter={ev => (ev.currentTarget as HTMLButtonElement).style.background = surface}
                  onMouseLeave={ev => (ev.currentTarget as HTMLButtonElement).style.background = 'white'}
                >
                  <div style={{ width: 28, height: 28, borderRadius: 4, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700, background: '#EEF2FF', color: '#3730A3', marginTop: 1 }}>
                    {e.fromName?.[0]?.toUpperCase() || 'E'}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 3 }}>
                      <span style={{ fontSize: 13, fontWeight: 600, color: ink, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '80%' }}>{e.subject}</span>
                      <span style={{ fontSize: 10, color: faint, whiteSpace: 'nowrap', marginLeft: 8 }}>{e.date}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, minWidth: 0, overflow: 'hidden' }}>
                      <span style={{ fontSize: 11, color: muted, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flexShrink: 1, minWidth: 0 }}>{e.fromName}</span>
                      {comparingIds?.has(e.id) ? (
                        <Badge label="Comparing" />
                      ) : e.status === 'Processing' ? (
                        <Badge label="Processing" />
                      ) : (
                        <>
                          <Badge label={e.type} />
                          {e.type === 'Document Comparison' && <Badge label={e.status} />}
                        </>
                      )}
                    </div>
                  </div>
                </button>
              ))
            )}
            <button onClick={() => onNav('inbox')} style={{ width: '100%', padding: '10px 20px', border: 'none', background: surface, cursor: 'pointer', fontSize: 11, fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: navy, textAlign: 'left', borderTop: `1px solid ${borderLight}` }}>
              View all {emails.length} emails →
            </button>
          </div>
        </div>

        {/* Right column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 }}>
          {/* Flagged items */}
          <div>
            <SectionLabel>Flagged</SectionLabel>
            <div style={{ border: `1px solid ${border}`, borderRadius: 4, overflow: 'hidden', background: white }}>
              {attention.length === 0 ? (
                <div style={{ padding: '20px', textAlign: 'center' }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: green }}>✓ All clear</div>
                  <div style={{ fontSize: 11, color: faint, marginTop: 2 }}>No items flagged</div>
                </div>
              ) : attention.map((e, i) => (
                <button
                  key={e.id}
                  onClick={() => onSelect(e.id)}
                  style={{ width: '100%', padding: '11px 14px', border: 'none', background: 'white', cursor: 'pointer', textAlign: 'left', borderBottom: i < attention.length - 1 ? `1px solid ${borderLight}` : 'none' }}
                  onMouseEnter={ev => (ev.currentTarget as HTMLButtonElement).style.background = surface}
                  onMouseLeave={ev => (ev.currentTarget as HTMLButtonElement).style.background = 'white'}
                >
                  <div style={{ fontSize: 12, fontWeight: 600, color: ink, marginBottom: 4, lineHeight: 1.3, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{e.subject}</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Badge label={e.status} />
                    <span style={{ fontSize: 10, color: faint }}>{e.date}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Recent Comparisons */}
          <div>
            <SectionLabel>Recent Comparisons</SectionLabel>
            <div style={{ border: `1px solid ${border}`, borderRadius: 4, background: white, overflow: 'hidden' }}>
              {(() => {
                const recent = emails.filter(e => e.type === 'Document Comparison' && e.status !== 'New' && e.status !== 'Processing')
                if (recent.length === 0) return (
                  <div style={{ padding: '20px 14px', textAlign: 'center', fontSize: 12, color: faint }}>No comparisons processed yet</div>
                )
                return recent.slice(0, 4).map((e, i) => {
                  const isMatch = e.status === 'Match'
                  const isMismatch = e.status === 'Mismatch'
                  const isReview = e.status === 'Needs Review'
                  const outcomeColor = isMatch ? green : isReview ? red : isMismatch ? amber : muted
                  const outcomeIcon = isMatch ? '✓' : isMismatch ? '⚠' : isReview ? '?' : '—'
                  return (
                    <button
                      key={e.id}
                      onClick={() => onSelect(e.id)}
                      style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', border: 'none', background: white, cursor: 'pointer', textAlign: 'left', borderBottom: i < Math.min(recent.length, 4) - 1 ? `1px solid ${borderLight}` : 'none' }}
                      onMouseEnter={ev => (ev.currentTarget as HTMLButtonElement).style.background = surface}
                      onMouseLeave={ev => (ev.currentTarget as HTMLButtonElement).style.background = white}
                    >
                      <div style={{ width: 24, height: 24, borderRadius: 4, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700, background: isMatch ? '#DCFCE7' : isReview ? redBg : isMismatch ? amberBg : '#F3F4F6', color: outcomeColor }}>
                        {outcomeIcon}
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: 11, fontWeight: 600, color: ink, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{e.subject}</div>
                        <div style={{ fontSize: 10, color: faint, marginTop: 1 }}>{e.date}</div>
                      </div>
                      <Badge label={e.status} />
                    </button>
                  )
                })
              })()}
              <button onClick={() => onNav('reports')} style={{ width: '100%', padding: '8px 14px', border: 'none', background: surface, cursor: 'pointer', fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: navy, textAlign: 'left', borderTop: `1px solid ${borderLight}` }}>
                View history →
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

