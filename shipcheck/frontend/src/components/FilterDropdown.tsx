import { useState } from 'react'
import { surface, white, border, borderLight, navy, ink, muted } from '../constants/tokens'
import { emailTypeLabel } from '../types'

export const DEFAULT_CLASSIFICATIONS = ['Document Comparison', 'New SI Request', 'Invoice Query', 'General', 'Spam'] as const
export const DEFAULT_BL_STATUSES = ['Match', 'Mismatch', 'Needs Review'] as const

export interface FilterState {
  classifications: string[]
  blStatuses: string[]
  senderSearch: string
  dateSort: 'recent' | 'old'
}

export const DEFAULT_FILTER_STATE: FilterState = { classifications: [], blStatuses: [], senderSearch: '', dateSort: 'recent' }

interface FilterDropdownProps {
  filters: FilterState
  onChange: (f: FilterState) => void
  showClassifications?: boolean
  showSender?: boolean
  classificationOptions?: readonly string[]
  statusOptions?: readonly string[]
  statusLabel?: string
  senderLabel?: string
  senderPlaceholder?: string
}

// Shared by Inbox, Review, and Reports - each page shows only the sections
// that make sense for its data (e.g. Reports has no per-item sender, and
// every row is already a BL comparison so there's nothing to classify).
export function FilterDropdown({
  filters,
  onChange,
  showClassifications = true,
  showSender = true,
  classificationOptions = DEFAULT_CLASSIFICATIONS,
  statusOptions = DEFAULT_BL_STATUSES,
  statusLabel = 'BL Status',
  senderLabel = 'Sender',
  senderPlaceholder = 'Filter by sender name or email…',
}: FilterDropdownProps) {
  const [open, setOpen] = useState(false)

  const activeCount = (showClassifications ? filters.classifications.length : 0) + filters.blStatuses.length +
    (showSender && filters.senderSearch ? 1 : 0) + (filters.dateSort !== 'recent' ? 1 : 0)

  function toggleSet(key: 'classifications' | 'blStatuses', val: string) {
    const cur = filters[key]
    onChange({ ...filters, [key]: cur.includes(val) ? cur.filter(x => x !== val) : [...cur, val] })
  }

  return (
    <div style={{ position: 'relative' }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          fontSize: 12, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase',
          padding: '7px 14px', borderRadius: 4, cursor: 'pointer',
          border: `1px solid ${activeCount > 0 ? navy : border}`,
          background: activeCount > 0 ? navy : white,
          color: activeCount > 0 ? white : muted,
        }}
      >
        <span>⊞ Filter</span>
        {activeCount > 0 && (
          <span style={{ fontSize: 10, fontWeight: 700, minWidth: 16, height: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 8, background: 'rgba(255,255,255,0.25)', color: white, padding: '0 4px' }}>{activeCount}</span>
        )}
        <span style={{ fontSize: 10, opacity: 0.6 }}>{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <>
          {/* backdrop */}
          <div style={{ position: 'fixed', inset: 0, zIndex: 99 }} onClick={() => setOpen(false)} />
          {/* panel */}
          <div className="filter-panel" style={{ position: 'absolute', top: 'calc(100% + 6px)', left: 0, zIndex: 100, width: 320, background: white, border: `1px solid ${border}`, borderRadius: 6, boxShadow: '0 8px 24px rgba(0,0,0,0.10)', overflow: 'hidden' }}>
            {showClassifications && (
              <div style={{ padding: '14px 16px', borderBottom: `1px solid ${borderLight}` }}>
                <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: muted, marginBottom: 10 }}>Classification</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {classificationOptions.map(c => (
                    <label key={c} style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13, color: ink }}>
                      <input
                        type="checkbox"
                        checked={filters.classifications.includes(c)}
                        onChange={() => toggleSet('classifications', c)}
                        style={{ accentColor: navy, width: 14, height: 14 }}
                      />
                      {emailTypeLabel(c)}
                    </label>
                  ))}
                </div>
              </div>
            )}

            <div style={{ padding: '14px 16px', borderBottom: `1px solid ${borderLight}` }}>
              <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: muted, marginBottom: 10 }}>{statusLabel}</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {statusOptions.map(s => {
                  const active = filters.blStatuses.includes(s)
                  return (
                    <button
                      key={s}
                      onClick={() => toggleSet('blStatuses', s)}
                      style={{ fontSize: 11, fontWeight: 600, padding: '4px 10px', borderRadius: 3, border: `1px solid ${active ? navy : border}`, background: active ? navy : 'none', color: active ? white : muted, cursor: 'pointer', letterSpacing: '0.04em' }}
                    >{s}</button>
                  )
                })}
              </div>
            </div>

            {showSender && (
              <div style={{ padding: '14px 16px', borderBottom: `1px solid ${borderLight}` }}>
                <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: muted, marginBottom: 10 }}>{senderLabel}</div>
                <input
                  value={filters.senderSearch}
                  onChange={e => onChange({ ...filters, senderSearch: e.target.value })}
                  placeholder={senderPlaceholder}
                  style={{ width: '100%', fontSize: 13, padding: '7px 10px', border: `1px solid ${border}`, borderRadius: 4, background: surface, color: ink, outline: 'none', boxSizing: 'border-box' }}
                />
              </div>
            )}

            <div style={{ padding: '14px 16px', borderBottom: `1px solid ${borderLight}` }}>
              <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: muted, marginBottom: 10 }}>Date</div>
              <div style={{ display: 'flex', gap: 6 }}>
                {(['recent', 'old'] as const).map(opt => (
                  <button
                    key={opt}
                    onClick={() => onChange({ ...filters, dateSort: opt })}
                    style={{ fontSize: 11, fontWeight: 600, padding: '5px 14px', borderRadius: 3, border: `1px solid ${filters.dateSort === opt ? navy : border}`, background: filters.dateSort === opt ? navy : 'none', color: filters.dateSort === opt ? white : muted, cursor: 'pointer', letterSpacing: '0.04em', textTransform: 'capitalize' }}
                  >{opt === 'recent' ? 'Recent first' : 'Oldest first'}</button>
                ))}
              </div>
            </div>

            <div style={{ padding: '10px 16px', display: 'flex', justifyContent: 'flex-end' }}>
              <button
                onClick={() => { onChange(DEFAULT_FILTER_STATE); setOpen(false) }}
                style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', padding: '5px 12px', border: `1px solid ${border}`, borderRadius: 3, background: 'none', color: muted, cursor: 'pointer' }}
              >Clear all</button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
