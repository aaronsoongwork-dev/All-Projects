import type { GmailEmail, ComparisonField, Page } from '../types'

// ─── Design Tokens ────────────────────────────────────────────────────────────

export const bg = '#EDEAE2'        // warm beige main bg
export const surface = '#F7F5EF'   // slightly warmer surface
export const white = '#FFFFFF'
export const navy = '#1B3652'
export const navyMid = '#264D76'
export const border = '#D8D3C8'
export const borderLight = '#E5E1D8'
export const ink = '#1A1612'
export const muted = '#6B6560'
export const faint = '#A8A298'
export const amber = '#B45309'
export const amberBg = '#FEF3C7'
export const amberBdr = '#F6D860'
export const green = '#166534'
export const greenBg = '#DCFCE7'
export const red = '#B91C1C'
export const redBg = '#FEE2E2'
export const redBdr = '#FECACA'

// ─── Breadcrumbs ──────────────────────────────────────────────────────────────

export const CRUMBS: Record<Page, string> = {
  dashboard: 'Dashboard',
  inbox: 'Inbox',
  'email-detail': 'Email Detail',
  processing: 'Processing',
  comparison: 'Comparison',
  review: 'Review',
  'review-detail': 'Review Detail',
  reports: 'Reports',
  upload: 'Upload & Compare',
  'upload-comparison': 'Upload Comparison',
  settings: 'Settings',
}

