import type { ReactNode } from 'react'
import {
  muted,
  borderLight,
  navy,
  amber,
  amberBg,
  amberBdr,
  green,
  greenBg,
  red,
  redBg,
  redBdr,
  white,
  border,
  ink,
  faint,
} from '../../constants/tokens'
import { emailTypeLabel } from '../../types'

// ─── SectionLabel ─────────────────────────────────────────────────────────────

export function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <span style={{ color: muted, fontSize: 13, fontWeight: 400 }}>—</span>
      <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.14em', textTransform: 'uppercase', color: muted }}>
        {children}
      </span>
    </div>
  )
}

// ─── Divider ──────────────────────────────────────────────────────────────────

export function Divider() {
  return <div style={{ height: 1, background: borderLight, margin: '20px 0' }} />
}

// ─── Spinner ──────────────────────────────────────────────────────────────────

export function Spinner({ size = 14, color = navy, className = '' }: { size?: number; color?: string; className?: string }) {
  return (
    <svg
      className={`animate-spin ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{
        display: 'inline-block',
        verticalAlign: 'middle',
        flexShrink: 0,
        animation: 'spin 0.8s linear infinite',
      }}
    >
      <circle
        cx="12"
        cy="12"
        r="10"
        stroke={color}
        strokeWidth="3"
        strokeOpacity="0.25"
      />
      <path
        d="M12 2a10 10 0 0 1 10 10"
        stroke={color}
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  )
}

// ─── Badge ────────────────────────────────────────────────────────────────────

export function Badge({ label }: { label: string }) {
  const map: Record<string, { bg: string; color: string; border: string }> = {
    'Document Comparison': { bg: '#EEF2FF', color: '#3730A3', border: '#C7D2FE' },
    'New SI Request':      { bg: greenBg,  color: green,     border: '#86EFAC' },
    'Invoice Query':       { bg: amberBg,  color: amber,     border: amberBdr },
    'General':             { bg: '#F3F4F6', color: '#4B5563', border: '#E5E7EB' },
    'Spam':                { bg: '#FFF1F2', color: '#9F1239', border: '#FECDD3' },
    'Mismatch':            { bg: amberBg,  color: '#92400E', border: amberBdr },
    'Needs Review':        { bg: redBg,    color: red,       border: redBdr },
    'Match':               { bg: greenBg,  color: green,     border: '#86EFAC' },
    'Classified':          { bg: '#F3F4F6', color: '#4B5563', border: '#E5E7EB' },
    'New':                 { bg: '#EFF6FF', color: '#1D4ED8', border: '#BFDBFE' },
    'Processing':          { bg: '#EFF6FF', color: '#1D4ED8', border: '#BFDBFE' },
    'Comparing':           { bg: '#EFF6FF', color: '#1D4ED8', border: '#BFDBFE' },
  }
  const s = map[label] || map['Classified']
  const dot = label === 'Mismatch' || label === 'Needs Review' || label === 'Match'
  const isProcessing = label === 'Processing' || label === 'Comparing'
  return (
    <span className="inline-flex items-center gap-1" style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase', padding: '3px 8px', border: `1px solid ${s.border}`, borderRadius: 3, background: s.bg, color: s.color }}>
      {dot && <span style={{ width: 5, height: 5, borderRadius: '50%', background: label === 'Match' ? green : label === 'Needs Review' ? red : '#D97706', display: 'inline-block' }} />}
      {isProcessing && <Spinner size={9} color="#1D4ED8" />}
      {emailTypeLabel(label)}
    </span>
  )
}

// ─── Icons ────────────────────────────────────────────────────────────────────

export function SettingsIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  )
}

export function SearchIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
      <circle cx="6.5" cy="6.5" r="4.5" stroke="currentColor" strokeWidth="1.4"/>
      <path d="M10 10l4 4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
    </svg>
  )
}

// ─── SearchInput ──────────────────────────────────────────────────────────────

export function SearchInput({ value, onChange, placeholder, maxWidth = 360, className }: {
  value: string
  onChange: (v: string) => void
  placeholder?: string
  maxWidth?: number
  className?: string
}) {
  return (
    <div className={className} style={{ position: 'relative', flex: 1, maxWidth }}>
      <span style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: faint }}>
        <SearchIcon />
      </span>
      <input
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder || 'Search…'}
        style={{ width: '100%', paddingLeft: 32, paddingRight: 12, paddingTop: 8, paddingBottom: 8, fontSize: 13, border: `1px solid ${border}`, borderRadius: 4, background: white, color: ink, outline: 'none', boxSizing: 'border-box' }}
      />
    </div>
  )
}

export function GoogleIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 18 18">
      <path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 01-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z"/>
      <path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 009 18z"/>
      <path fill="#FBBC05" d="M3.964 10.706A5.41 5.41 0 013.682 9c0-.593.102-1.17.282-1.706V4.962H.957A8.996 8.996 0 000 9c0 1.452.348 2.827.957 4.038l3.007-2.332z"/>
      <path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 00.957 4.962L3.964 7.294C4.672 5.163 6.656 3.58 9 3.58z"/>
    </svg>
  )
}

export function LogoutIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  )
}

export { Skeleton, InboxSkeleton, DashboardSkeleton, ReviewSkeleton } from './Skeleton'
export type { SkeletonProps } from './Skeleton'


