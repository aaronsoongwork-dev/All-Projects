import { useRef, useState } from 'react'
import type { GmailEmail, ClassifyingState } from '../types'
import { emailTypeLabel } from '../types'
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
  red,
} from '../constants/tokens'
import { Badge, Spinner, SearchInput, InboxSkeleton } from '../components/primitives'
import { FilterDropdown, DEFAULT_FILTER_STATE, type FilterState } from '../components/FilterDropdown'

// 'Processing' isn't a real EmailType - it's a pseudo-group for emails that
// haven't been classified yet (type defaults to 'General' until classify
// actually runs), so they don't get lumped in among genuinely-General emails.
const GROUP_ORDER = ['Processing', 'Document Comparison', 'New SI Request', 'Invoice Query', 'General', 'Spam'] as const

function EmailRow({ e, onSelect, isLast, isComparing }: { e: GmailEmail; onSelect: (id: string) => void; isLast: boolean; isComparing?: boolean }) {
  const warn = e.status === 'Mismatch' || e.status === 'Needs Review'
  return (
    <tr
      onClick={() => onSelect(e.id)}
      style={{ cursor: 'pointer', background: 'white', borderBottom: !isLast ? `1px solid ${borderLight}` : 'none' }}
      onMouseEnter={ev => (ev.currentTarget as HTMLTableRowElement).style.background = surface}
      onMouseLeave={ev => (ev.currentTarget as HTMLTableRowElement).style.background = 'white'}
    >
      <td style={{ padding: '14px 16px', width: 16 }}>
        {warn && <span style={{ width: 7, height: 7, borderRadius: '50%', background: e.status === 'Needs Review' ? red : amber, display: 'block' }} />}
      </td>
      <td style={{ padding: '14px 16px' }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: ink, whiteSpace: 'nowrap', maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis' }}>{e.fromName}</div>
        <div style={{ fontSize: 11, color: muted, whiteSpace: 'nowrap', maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis' }}>{e.from}</div>
      </td>
      <td style={{ padding: '14px 16px', maxWidth: 300 }}>
        <div style={{ fontSize: 14, fontWeight: 500, color: ink, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{e.subject}</div>
        <div style={{ fontSize: 12, color: muted, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginTop: 2 }}>{e.snippet}</div>
      </td>
      <td style={{ padding: '14px 16px', whiteSpace: 'nowrap' }}>
        <Badge label={e.status === 'Processing' ? 'Processing' : e.type} />
      </td>
      <td style={{ padding: '14px 16px', whiteSpace: 'nowrap' }}>
        {isComparing ? (
          <Badge label="Comparing" />
        ) : e.status === 'Processing' ? (
          <Badge label="Processing" />
        ) : e.type === 'Document Comparison' ? (
          <Badge label={e.status} />
        ) : (
          <span style={{ color: faint, fontSize: 13 }}>—</span>
        )}
      </td>
      <td style={{ padding: '14px 16px', fontSize: 12, color: muted, whiteSpace: 'nowrap' }}>{e.date}</td>
    </tr>
  )
}

function EmailTable({ rows, onSelect, comparingIds }: { rows: GmailEmail[]; onSelect: (id: string) => void; comparingIds?: Set<string> }) {
  return (
    <div style={{ border: `1px solid ${border}`, borderRadius: 4, overflow: 'hidden', background: white }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
        <thead>
          <tr style={{ borderBottom: `1px solid ${borderLight}`, background: surface }}>
            {['', 'Sender', 'Subject', 'Classification', 'BL Status', 'Date'].map(h => (
              <th key={h} style={{ padding: '11px 16px', textAlign: 'left', fontSize: 10, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: muted }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((e, i) => <EmailRow key={e.id} e={e} onSelect={onSelect} isLast={i === rows.length - 1} isComparing={comparingIds?.has(e.id)} />)}
          {!rows.length && (
            <tr><td colSpan={6} style={{ padding: '48px 20px', textAlign: 'center', color: faint, fontSize: 14 }}>No emails match.</td></tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

interface InboxPageProps {
  emails: GmailEmail[]
  onSelect: (id: string) => void
  loading?: boolean
  classifying?: ClassifyingState
  apiError?: string | null
  onClearError?: () => void
  hasMore?: boolean
  onLoadMore?: () => void
  loadingMore?: boolean
  loadMoreNotice?: string | null
  onUploadEml?: (file: File) => void | Promise<void>
  comparingIds?: Set<string>
}

export function InboxPage({
  emails,
  onSelect,
  loading,
  classifying,
  apiError,
  onClearError,
  hasMore,
  onLoadMore,
  loadingMore,
  loadMoreNotice,
  onUploadEml,
  comparingIds,
}: InboxPageProps) {
  const [search, setSearch] = useState('')
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTER_STATE)
  const [uploadingEml, setUploadingEml] = useState(false)
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set())
  const emlInputRef = useRef<HTMLInputElement | null>(null)

  function toggleGroup(cat: string) {
    setCollapsedGroups(prev => {
      const next = new Set(prev)
      if (next.has(cat)) next.delete(cat)
      else next.add(cat)
      return next
    })
  }

  async function handleEmlSelected(file: File | undefined) {
    if (!file || !onUploadEml) return
    setUploadingEml(true)
    try {
      await onUploadEml(file)
    } finally {
      setUploadingEml(false)
      if (emlInputRef.current) emlInputRef.current.value = ''
    }
  }

  if (loading && emails.length === 0) {
    return <InboxSkeleton />
  }

  const isFiltered = search || filters.classifications.length || filters.blStatuses.length || filters.senderSearch

  const processed = emails
    .filter(e => {
      if (search && !e.subject.toLowerCase().includes(search.toLowerCase()) && !e.fromName.toLowerCase().includes(search.toLowerCase())) return false
      if (filters.senderSearch && !e.fromName.toLowerCase().includes(filters.senderSearch.toLowerCase()) && !e.from.toLowerCase().includes(filters.senderSearch.toLowerCase())) return false
      if (filters.classifications.length && !filters.classifications.includes(e.type)) return false
      if (filters.blStatuses.length && !filters.blStatuses.includes(e.status)) return false
      return true
    })
    .sort((a, b) => filters.dateSort === 'recent' ? b.timestamp - a.timestamp : a.timestamp - b.timestamp)

  const showGrouped = !isFiltered
  const progressPercent = classifying?.total ? Math.round((classifying.current / classifying.total) * 100) : 0

  return (
    <div style={{ padding: 28 }}>
      {/* Active AI Classification Progress Banner */}
      {classifying?.active && (
        <div style={{ background: '#EFF6FF', border: '1px solid #BFDBFE', borderRadius: 4, padding: '14px 20px', marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12, fontWeight: 600, color: '#1E40AF' }}>
              <Spinner size={14} color="#2563EB" />
              AI CLASSIFICATION IN PROGRESS: Analyzing emails with Claude Haiku ({classifying.current} of {classifying.total} completed)…
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

      {/* Loading More Emails Banner - shown up here (not just at the button
          down at the bottom of the list) since fetching + classifying 25
          more emails takes real time and deserves to be obvious. No real
          progress number to report (one atomic server call), so the bar is
          indeterminate rather than a fake percentage. */}
      {loadingMore && (
        <div style={{ background: '#EFF6FF', border: '1px solid #BFDBFE', borderRadius: 4, padding: '14px 20px', marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12, fontWeight: 600, color: '#1E40AF', marginBottom: 8 }}>
            <Spinner size={14} color="#2563EB" />
            Fetching and classifying your next 25 emails from Gmail…
          </div>
          <div style={{ width: '100%', height: 4, background: '#DBEAFE', borderRadius: 2, overflow: 'hidden', position: 'relative' }}>
            <div className="indeterminate-bar" style={{ background: '#2563EB' }} />
          </div>
        </div>
      )}

      {/* Explicit Backend Error Banner */}
      {(classifying?.error || apiError) && (
        <div style={{ background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: 4, padding: '12px 18px', marginBottom: 20, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: '#991B1B', fontWeight: 500 }}>
            <span style={{ fontSize: 14 }}>⚠</span>
            <span><strong>AI Backend Error:</strong> {classifying?.error || apiError}</span>
          </div>
          {onClearError && (
            <button onClick={onClearError} style={{ background: 'none', border: 'none', color: '#991B1B', cursor: 'pointer', fontSize: 12, fontWeight: 600 }}>✕ Dismiss</button>
          )}
        </div>
      )}

      {/* Controls */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginBottom: 24, alignItems: 'center' }}>
        <SearchInput className="inbox-search" value={search} onChange={setSearch} placeholder="Search emails…" />
        <FilterDropdown filters={filters} onChange={setFilters} />
        {onUploadEml && (
          <>
            <input
              ref={emlInputRef}
              type="file"
              accept=".eml,message/rfc822"
              style={{ display: 'none' }}
              onChange={e => handleEmlSelected(e.target.files?.[0])}
            />
            <button
              onClick={() => emlInputRef.current?.click()}
              disabled={uploadingEml}
              style={{
                fontSize: 11, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase',
                background: white, color: navy, border: `1px solid ${border}`, borderRadius: 4,
                padding: '8px 14px', cursor: uploadingEml ? 'not-allowed' : 'pointer',
                display: 'inline-flex', alignItems: 'center', gap: 6, opacity: uploadingEml ? 0.6 : 1,
              }}
            >
              {uploadingEml && <Spinner size={12} color={navy} />}
              {uploadingEml ? 'Uploading…' : '+ Upload .eml'}
            </button>
          </>
        )}
        {isFiltered && (
          <button
            onClick={() => { setSearch(''); setFilters(DEFAULT_FILTER_STATE) }}
            style={{ fontSize: 11, fontWeight: 600, color: muted, background: 'none', border: 'none', cursor: 'pointer', letterSpacing: '0.04em' }}
          >✕ Clear</button>
        )}
        <div style={{ marginLeft: 'auto', fontSize: 12, color: faint }}>{processed.length} email{processed.length !== 1 ? 's' : ''}</div>
      </div>

      {showGrouped ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
          {GROUP_ORDER.map(cat => {
            const group = cat === 'Processing'
              ? processed.filter(e => e.status === 'Processing')
              : processed.filter(e => e.type === cat && e.status !== 'Processing')
            if (!group.length) return null
            const collapsed = collapsedGroups.has(cat)
            return (
              <div key={cat}>
                <button
                  onClick={() => toggleGroup(cat)}
                  style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10, width: '100%', border: 'none', background: 'none', cursor: 'pointer', padding: 0, textAlign: 'left' }}
                >
                  <span style={{ fontSize: 9, color: muted, transform: collapsed ? 'rotate(-90deg)' : 'none', transition: 'transform 0.15s ease', display: 'inline-block' }}>▼</span>
                  {cat === 'Processing' ? <Spinner size={11} color={muted} /> : <span style={{ color: muted, fontSize: 13 }}>—</span>}
                  <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: muted }}>{cat === 'Processing' ? 'Classifying…' : emailTypeLabel(cat)}</span>
                  <span style={{ fontSize: 11, color: faint }}>({group.length})</span>
                </button>
                {!collapsed && <EmailTable rows={group} onSelect={onSelect} comparingIds={comparingIds} />}
              </div>
            )
          })}
        </div>
      ) : (
        <EmailTable rows={processed} onSelect={onSelect} comparingIds={comparingIds} />
      )}

      {hasMore && (
        <div style={{ marginTop: 28, padding: '20px 24px', border: `1px solid ${border}`, borderRadius: 6, background: white, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: ink }}>More emails available</div>
            <div style={{ fontSize: 12, color: muted, marginTop: 2 }}>Fetch and classify the next 25 messages from the shared Gmail inbox.</div>
          </div>
          <button
            onClick={onLoadMore}
            disabled={loadingMore}
            style={{
              padding: '12px 28px',
              fontSize: 12,
              fontWeight: 700,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              color: white,
              background: loadingMore ? borderLight : navy,
              border: 'none',
              borderRadius: 4,
              cursor: loadingMore ? 'not-allowed' : 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              flexShrink: 0,
            }}
          >
            {loadingMore && <Spinner size={12} color={navy} />}
            {loadingMore ? 'Loading…' : 'Load More Emails (25)'}
          </button>
          {loadMoreNotice && !loadingMore && (
            <div style={{ width: '100%', fontSize: 12, color: muted }}>{loadMoreNotice}</div>
          )}
        </div>
      )}
    </div>
  )
}

