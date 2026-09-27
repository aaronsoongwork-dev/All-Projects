import { useState } from 'react'
import type { ReactElement } from 'react'
import type { Page, GmailEmail, UserInfo } from '../../types'
import { navy, ink } from '../../constants/tokens'
import { LogoutIcon, SettingsIcon } from '../primitives'

interface SidebarProps {
  page: Page
  onNav: (p: Page) => void
  user: UserInfo | null
  emails: GmailEmail[]
  onLogout: () => void
  accent?: 'success' | 'error' | null
}

const ACCENT_COLOR = { success: '#22C55E', error: '#EF4444' } as const

function DashboardIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 16 16" fill="none">
      <rect x="1.5" y="1.5" width="5.5" height="5.5" rx="1" stroke="currentColor" strokeWidth="1.3" />
      <rect x="9" y="1.5" width="5.5" height="5.5" rx="1" stroke="currentColor" strokeWidth="1.3" />
      <rect x="1.5" y="9" width="5.5" height="5.5" rx="1" stroke="currentColor" strokeWidth="1.3" />
      <rect x="9" y="9" width="5.5" height="5.5" rx="1" stroke="currentColor" strokeWidth="1.3" />
    </svg>
  )
}

function InboxIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 16 16" fill="none">
      <rect x="1.5" y="3" width="13" height="10" rx="1.5" stroke="currentColor" strokeWidth="1.3" />
      <path d="M2 4l6 5 6-5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function UploadIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 16 16" fill="none">
      <path d="M8 10.5V2M8 2L4.5 5.5M8 2l3.5 3.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M2 11v2a1 1 0 001 1h10a1 1 0 001-1v-2" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function ReviewIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 16 16" fill="none">
      <circle cx="8" cy="8" r="6.2" stroke="currentColor" strokeWidth="1.3" />
      <path d="M5.3 8.2l1.8 1.8 3.6-3.8" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function ReportsIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 16 16" fill="none">
      <path d="M2 14V7M8 14V2M14 14V9.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  )
}

const NAV_ICONS: Record<Page, () => ReactElement> = {
  dashboard: DashboardIcon,
  inbox: InboxIcon,
  upload: UploadIcon,
  review: ReviewIcon,
  reports: ReportsIcon,
  settings: SettingsIcon,
  'email-detail': DashboardIcon,
  processing: DashboardIcon,
  comparison: DashboardIcon,
  'review-detail': ReviewIcon,
  'upload-comparison': UploadIcon,
}

export function Sidebar({ page, onNav, user, emails, onLogout, accent }: SidebarProps) {
  const unread = emails.filter(e => e.status === 'New').length
  const reviewCount = emails.filter(e => e.status === 'Needs Review').length
  const accentColor = accent ? ACCENT_COLOR[accent] : 'transparent'

  // Mobile-only: the sidebar collapses to a logo-only rail and expands into
  // an overlay when the logo is tapped. Has no visual effect on desktop -
  // the CSS driving it is scoped to the mobile media query.
  const [mobileExpanded, setMobileExpanded] = useState(false)

  const nav: { id: Page; label: string; count?: number }[] = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'inbox', label: 'Inbox', count: unread || undefined },
    { id: 'upload', label: 'Upload & Compare' },
    { id: 'review', label: 'Review', count: reviewCount || undefined },
    { id: 'reports', label: 'Reports' },
    { id: 'settings', label: 'Settings' },
  ]

  return (
    <>
      <aside
        className={`app-sidebar${mobileExpanded ? ' is-expanded' : ''}`}
        style={{
          background: navy,
          borderRight: `3px solid ${accentColor}`,
          boxShadow: accent ? `inset -8px 0 16px -12px ${accentColor}` : 'none',
          transition: 'border-color 0.3s ease, box-shadow 0.3s ease',
        }}
      >
        {/* Logo - doubles as the mobile expand/collapse toggle */}
        <button
          className="sidebar-logo-btn"
          onClick={() => setMobileExpanded(o => !o)}
          style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '28px 20px 20px', border: 'none', background: 'none', cursor: 'pointer', width: '100%', textAlign: 'left' }}
        >
          <img src="/logo.png" alt="" style={{ height: 32, width: 'auto', flexShrink: 0 }} />
          <div className="sidebar-brand-text">
            <div style={{ fontFamily: 'Playfair Display, serif', color: 'white', fontSize: 16, fontWeight: 700, lineHeight: 1, whiteSpace: 'nowrap' }}>ShipCheck</div>
          </div>
        </button>

        {/* Mobile-only icon rail: lets you jump straight to a page without
            expanding the sidebar first. Hidden on desktop and while expanded. */}
        <nav className="sidebar-rail-nav">
          {nav.map(({ id, label, count }) => {
            const active = page === id
            const Icon = NAV_ICONS[id]
            return (
              <button
                key={id}
                onClick={() => onNav(id)}
                title={label}
                style={{
                  position: 'relative', width: 36, height: 36, display: 'flex', alignItems: 'center', justifyContent: 'center',
                  border: 'none', borderRadius: 6, cursor: 'pointer',
                  background: active ? 'rgba(245,158,11,0.18)' : 'none',
                  color: active ? '#F59E0B' : 'rgba(255,255,255,0.55)',
                }}
              >
                <Icon />
                {count ? (
                  <span style={{ position: 'absolute', top: -2, right: -2, fontSize: 9, fontWeight: 700, minWidth: 14, height: 14, display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 7, background: '#F59E0B', color: ink, padding: '0 3px' }}>{count}</span>
                ) : null}
              </button>
            )
          })}
          <button
            onClick={() => onNav('settings')}
            title={user?.name || 'Account'}
            style={{ marginTop: 'auto', marginBottom: 16, width: 30, height: 30, borderRadius: '50%', border: 'none', cursor: 'pointer', overflow: 'hidden', flexShrink: 0, padding: 0 }}
          >
            {user?.picture
              ? <img src={user.picture} style={{ width: '100%', height: '100%', objectFit: 'cover' }} alt="" />
              : <div style={{ width: '100%', height: '100%', borderRadius: '50%', background: 'rgba(255,255,255,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 600, color: 'white' }}>{user?.name?.[0] || 'U'}</div>
            }
          </button>
        </nav>

        <div className="sidebar-collapsible">
          <div style={{ height: 1, background: 'rgba(255,255,255,0.08)', margin: '0 20px' }} />

          {/* Nav */}
          <nav style={{ flex: 1, padding: '16px 0' }}>
            <div style={{ fontSize: 9, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.3)', padding: '0 20px', marginBottom: 8, fontWeight: 600 }}>Navigation</div>
            {nav.map(({ id, label, count }) => {
              const active = page === id
              return (
                <button
                  key={id}
                  onClick={() => { onNav(id); setMobileExpanded(false) }}
                  style={{
                    width: '100%', display: 'flex', alignItems: 'center', gap: 10,
                    padding: '9px 20px', border: 'none', background: 'none',
                    cursor: 'pointer', textAlign: 'left', position: 'relative',
                    borderLeft: active ? '2px solid #F59E0B' : '2px solid transparent',
                  }}
                >
                  <span style={{ fontSize: 14, fontWeight: active ? 600 : 400, color: active ? 'white' : 'rgba(255,255,255,0.5)', flex: 1, whiteSpace: 'nowrap' }}>{label}</span>
                  {count ? (
                    <span style={{ fontSize: 10, fontWeight: 700, minWidth: 18, height: 18, display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 3, background: '#F59E0B', color: ink, padding: '0 4px' }}>{count}</span>
                  ) : null}
                </button>
              )
            })}
          </nav>

          <div style={{ height: 1, background: 'rgba(255,255,255,0.08)', margin: '0 20px' }} />

          {/* User Section & Logout */}
          <div style={{ padding: '14px 20px 20px' }}>
            {user && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                {user.picture
                  ? <img src={user.picture} style={{ width: 26, height: 26, borderRadius: '50%' }} alt="" />
                  : <div style={{ width: 26, height: 26, borderRadius: '50%', background: 'rgba(255,255,255,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 600, color: 'white' }}>{user.name?.[0] || 'U'}</div>
                }
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontSize: 12, fontWeight: 500, color: 'white', lineHeight: 1.2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{user.name}</div>
                  <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{user.email}</div>
                </div>
              </div>
            )}
            <button
              onClick={onLogout}
              title="Log Out"
              style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.25)', borderRadius: 3, cursor: 'pointer', color: '#FCA5A5', fontSize: 11, padding: '6px 7px' }}
            >
              <LogoutIcon /> Log Out
            </button>
          </div>
        </div>
      </aside>
      <div className={`sidebar-backdrop${mobileExpanded ? ' is-open' : ''}`} onClick={() => setMobileExpanded(false)} />
    </>
  )
}

