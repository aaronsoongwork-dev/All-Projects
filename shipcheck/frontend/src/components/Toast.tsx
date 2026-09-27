import { useCallback, useState } from 'react'
import { white, ink, muted, green, greenBg, red, redBg, redBdr, navy } from '../constants/tokens'
import { Spinner } from './primitives'

export interface ToastItem {
  id: string
  message: string
  type: 'info' | 'success' | 'error'
}

/**
 * Small toast queue. `pushToast` with an explicit `id` updates that toast in
 * place instead of stacking a new one - used to turn an "Uploading…" toast
 * into its own "✓ Uploaded" / "✗ Failed" result once the request settles,
 * rather than showing two separate popups for one action.
 */
export function useToasts() {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const dismissToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const pushToast = useCallback((
    message: string,
    type: ToastItem['type'] = 'info',
    opts?: { id?: string; autoDismissMs?: number }
  ) => {
    const id = opts?.id || Math.random().toString(36).slice(2)
    setToasts(prev => {
      const item: ToastItem = { id, message, type }
      return prev.some(t => t.id === id) ? prev.map(t => (t.id === id ? item : t)) : [...prev, item]
    })
    const duration = opts?.autoDismissMs ?? (type === 'info' ? 0 : type === 'error' ? 6000 : 4000)
    if (duration > 0) {
      setTimeout(() => dismissToast(id), duration)
    }
    return id
  }, [dismissToast])

  return { toasts, pushToast, dismissToast }
}

export function ToastContainer({ toasts, onDismiss }: { toasts: ToastItem[]; onDismiss: (id: string) => void }) {
  if (!toasts.length) return null
  return (
    <div style={{ position: 'fixed', bottom: 20, right: 20, zIndex: 1000, display: 'flex', flexDirection: 'column', gap: 8, maxWidth: 360 }}>
      {toasts.map(t => {
        const style = t.type === 'error'
          ? { bg: redBg, bdr: redBdr, color: red }
          : t.type === 'success'
          ? { bg: greenBg, bdr: '#86EFAC', color: green }
          : { bg: '#EFF6FF', bdr: '#BFDBFE', color: navy }
        return (
          <div
            key={t.id}
            style={{
              display: 'flex', alignItems: 'center', gap: 10,
              background: white, border: `1px solid ${style.bdr}`, borderLeft: `3px solid ${style.color}`,
              borderRadius: 4, padding: '10px 12px', boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
            }}
          >
            {t.type === 'info' ? (
              <Spinner size={14} color={style.color} />
            ) : (
              <span style={{ fontSize: 14, fontWeight: 700, color: style.color, flexShrink: 0 }}>{t.type === 'success' ? '✓' : '✗'}</span>
            )}
            <span style={{ fontSize: 12, color: ink, flex: 1, lineHeight: 1.4 }}>{t.message}</span>
            <button
              onClick={() => onDismiss(t.id)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: muted, fontSize: 12, padding: 0, flexShrink: 0 }}
            >✕</button>
          </div>
        )
      })}
    </div>
  )
}
