import { useState, useEffect } from 'react'
import {
  surface,
  white,
  border,
  borderLight,
  ink,
  muted,
  faint,
} from '../constants/tokens'
import { Badge, SearchInput } from '../components/primitives'
import { FilterDropdown, DEFAULT_FILTER_STATE, type FilterState } from '../components/FilterDropdown'
import { getComparisonsApi, type ComparisonRecord } from '../services/api'
import { fmtDate } from '../utils/date'

export function ReportsPage() {
  const [dbComparisons, setDbComparisons] = useState<ComparisonRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTER_STATE)

  useEffect(() => {
    setLoading(true)
    setError(null)
    getComparisonsApi(50)
      .then(data => {
        setDbComparisons(data || [])
      })
      .catch(err => {
        console.error('Failed to load comparison reports:', err)
        setError(err.message || 'Failed to connect to comparison reports service.')
      })
      .finally(() => setLoading(false))
  }, [])

  const isFiltered = !!search || filters.blStatuses.length > 0 || filters.dateSort !== 'recent'

  const processed = dbComparisons
    .filter(c => {
      if (search) {
        const q = search.toLowerCase()
        if (!(c.si_name || '').toLowerCase().includes(q) && !(c.bl_name || '').toLowerCase().includes(q)) return false
      }
      if (filters.blStatuses.length && !filters.blStatuses.includes(c.status)) return false
      return true
    })
    .sort((a, b) => {
      const ta = a.created_at ? new Date(a.created_at).getTime() : 0
      const tb = b.created_at ? new Date(b.created_at).getTime() : 0
      return filters.dateSort === 'recent' ? tb - ta : ta - tb
    })

  return (
    <div style={{ padding: 28 }}>
      {error && (
        <div style={{ background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: 4, padding: '12px 18px', marginBottom: 20, display: 'flex', alignItems: 'center', gap: 10, fontSize: 13, color: '#991B1B', fontWeight: 500 }}>
          <span style={{ fontSize: 16 }}>⚠</span>
          <span><strong>Failed to load reports:</strong> {error}</span>
        </div>
      )}

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginBottom: 20, alignItems: 'center' }}>
        <SearchInput value={search} onChange={setSearch} placeholder="Search reports…" />
        <FilterDropdown filters={filters} onChange={setFilters} showClassifications={false} showSender={false} />
        {isFiltered && (
          <button
            onClick={() => { setSearch(''); setFilters(DEFAULT_FILTER_STATE) }}
            style={{ fontSize: 11, fontWeight: 600, color: muted, background: 'none', border: 'none', cursor: 'pointer', letterSpacing: '0.04em' }}
          >✕ Clear</button>
        )}
        <div style={{ marginLeft: 'auto', fontSize: 12, color: faint }}>{processed.length} report{processed.length !== 1 ? 's' : ''}</div>
      </div>

      <div style={{ border: `1px solid ${border}`, borderRadius: 4, overflow: 'hidden', background: white }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
          <thead>
            <tr style={{ background: surface, borderBottom: `1px solid ${borderLight}` }}>
              {['Document / Subject', 'Type', 'Result', 'Date'].map(h => (
                <th key={h} style={{ padding: '10px 20px', textAlign: 'left', fontSize: 9, fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase', color: muted }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={4} style={{ padding: '36px 20px', textAlign: 'center', color: muted, fontSize: 13 }}>
                  Loading comparison reports…
                </td>
              </tr>
            ) : processed.length > 0 ? (
              processed.map((c, i) => (
                <tr key={c.id} style={{ borderBottom: i < processed.length - 1 ? `1px solid ${borderLight}` : 'none' }}>
                  <td style={{ padding: '13px 20px', fontWeight: 500, color: ink, maxWidth: 320, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {c.si_name || 'Shipping Instruction'} vs {c.bl_name || 'Bill of Lading'}
                  </td>
                  <td style={{ padding: '13px 20px' }}><Badge label="Document Comparison" /></td>
                  <td style={{ padding: '13px 20px' }}><Badge label={c.status} /></td>
                  <td style={{ padding: '13px 20px', fontSize: 11, color: faint }}>
                    {c.created_at ? fmtDate(new Date(c.created_at).getTime()) : 'Recent'}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={4} style={{ padding: '48px 20px', textAlign: 'center', color: muted, fontSize: 13 }}>
                  {dbComparisons.length === 0
                    ? <>No comparison reports found. Use <strong>Upload & Compare</strong> to process documents and generate reports.</>
                    : 'No reports match your search or filters.'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

