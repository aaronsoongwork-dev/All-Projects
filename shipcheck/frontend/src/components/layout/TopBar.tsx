import { useState, useEffect } from 'react'
import { white, border, muted, faint, navy } from '../../constants/tokens'
import { Spinner } from '../primitives'

interface TopBarProps {
  crumb: string
  onRefresh?: () => void
  loading?: boolean
  classifying?: { active: boolean; current: number; total: number; error: string | null }
}

export function TopBar({
  crumb,
  onRefresh,
  loading,
  classifying,
}: TopBarProps) {
  // Fixed to Malaysia time (GMT+8) regardless of the viewer's own machine,
  // same as every other displayed date/time in the app.
  const now = new Date()
  const timeStr = now.toLocaleTimeString([], { timeZone: 'Asia/Kuala_Lumpur', hour: '2-digit', minute: '2-digit', second: '2-digit' })
  const dateStr = now.toLocaleDateString([], { timeZone: 'Asia/Kuala_Lumpur', weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' }).toUpperCase()
  const [, setTick] = useState(0)
  useEffect(() => { const t = setInterval(() => setTick(n => n + 1), 1000); return () => clearInterval(t) }, [])

  return (
    <div className="app-topbar" style={{ height: 44, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, padding: '0 16px 0 24px', background: white, borderBottom: `1px solid ${border}` }}>
      <div style={{ fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', color: muted, fontWeight: 500, flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        — {crumb}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexShrink: 0 }}>
        {classifying?.active && (
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 11, fontWeight: 600, color: '#1E40AF', background: '#EFF6FF', border: '1px solid #BFDBFE', padding: '3px 9px', borderRadius: 4 }}>
            <Spinner size={10} color="#2563EB" />
            AI CLASSIFYING ({classifying.current}/{classifying.total})
          </div>
        )}
        {classifying?.error && (
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 11, fontWeight: 600, color: '#991B1B', background: '#FEF2F2', border: '1px solid #FECACA', padding: '3px 8px', borderRadius: 4 }}>
            <span>⚠</span> AI BACKEND ERROR
          </div>
        )}
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={loading || classifying?.active}
            style={{
              fontSize: 11,
              fontWeight: 600,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              color: navy,
              border: `1px solid ${border}`,
              borderRadius: 4,
              padding: '4px 12px',
              background: 'none',
              cursor: 'pointer',
              opacity: loading || classifying?.active ? 0.5 : 1,
            }}
          >
            {loading ? 'Loading…' : '↺ Refresh'}
          </button>
        )}
        <div className="topbar-clock" style={{ fontSize: 11, color: faint, letterSpacing: '0.06em', whiteSpace: 'nowrap' }}>
          <span style={{ color: muted, fontWeight: 500 }}>{timeStr}</span> · {dateStr}
        </div>
      </div>
    </div>
  )
}

