import { useGoogleLogin } from '@react-oauth/google'
import type { UserInfo } from '../types'
import {
  white,
  border,
  borderLight,
  navy,
  ink,
  muted,
  faint,
  green,
  greenBg,
} from '../constants/tokens'
import { SectionLabel, GoogleIcon, LogoutIcon } from '../components/primitives'

interface SettingsPageProps {
  user: UserInfo | null
  gmailToken: string | null
  onConnectGmail: (token: string) => void
  onDisconnectGmail: () => void
  onLogout: () => void
}

export function SettingsPage({
  user,
  gmailToken,
  onConnectGmail,
  onDisconnectGmail,
  onLogout,
}: SettingsPageProps) {
  const googleLogin = useGoogleLogin({
    scope: 'https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile',
    onSuccess: res => onConnectGmail(res.access_token),
    onError: err => console.error('Gmail connection failed', err),
  })

  return (
    <div style={{ padding: 28, flex: 1, maxWidth: 840 }}>
      {/* Page Title */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontFamily: 'Playfair Display, serif', fontSize: 32, fontWeight: 700, color: ink, margin: '0 0 8px' }}>
          Account & Settings
        </h1>
        <p style={{ fontSize: 13, color: muted, margin: 0 }}>
          Manage your account profile, persistent session, and Gmail inbox synchronization.
        </p>
      </div>

      {/* Account Profile Card */}
      <div style={{ background: white, border: `1px solid ${border}`, borderRadius: 4, padding: 24, marginBottom: 24 }}>
        <SectionLabel>Account Profile</SectionLabel>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginTop: 12, marginBottom: 20 }}>
          {user?.picture ? (
            <img src={user.picture} style={{ width: 48, height: 48, borderRadius: '50%', border: `1px solid ${border}`, flexShrink: 0 }} alt="" />
          ) : (
            <div style={{ width: 48, height: 48, borderRadius: '50%', background: navy, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, fontWeight: 700, color: white, flexShrink: 0 }}>
              {user?.name?.[0] || 'U'}
            </div>
          )}
          <div style={{ minWidth: 0 }}>
            <div style={{ fontSize: 16, fontWeight: 600, color: ink, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{user?.name || 'User'}</div>
            <div style={{ fontSize: 13, color: muted, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{user?.email || '—'}</div>
            <div style={{ fontSize: 11, color: faint, marginTop: 2 }}>
              Provider: <span style={{ textTransform: 'capitalize', fontWeight: 600 }}>{user?.provider || 'Supabase'}</span>
              {user?.id && <span> · ID: {user.id.slice(0, 8)}…</span>}
            </div>
          </div>
        </div>

        <div style={{ borderTop: `1px solid ${borderLight}`, paddingTop: 16, display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
          <div>
            <div style={{ fontSize: 12, fontWeight: 600, color: ink }}>Session Persistence</div>
            <div style={{ fontSize: 11, color: muted }}>Your session is stored securely in browser cookies and persists across reloads.</div>
          </div>
          <span style={{ fontSize: 11, fontWeight: 600, color: green, background: greenBg, padding: '3px 8px', borderRadius: 3, border: '1px solid #86EFAC', whiteSpace: 'nowrap' }}>
            Active Cookie Session
          </span>
        </div>
      </div>

      {/* Gmail Integration Card */}
      <div style={{ background: white, border: `1px solid ${border}`, borderRadius: 4, padding: 24, marginBottom: 24 }}>
        <SectionLabel>Gmail Integration</SectionLabel>
        <div style={{ marginTop: 12, marginBottom: 16 }}>
          <div style={{ fontSize: 15, fontWeight: 600, color: ink, marginBottom: 4 }}>
            Inbox Email Synchronization
          </div>
          <p style={{ fontSize: 12, color: muted, lineHeight: 1.6, margin: 0 }}>
            Connect your Gmail account to pull the latest shipping instructions and draft bills of lading automatically.
            If you signed up with a standard email account, Gmail remains unlinked until you explicitly connect it here.
          </p>
        </div>

        {gmailToken ? (
          <div style={{ background: '#F0FDF4', border: '1px solid #BBF7D0', borderRadius: 4, padding: 16, display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ width: 10, height: 10, borderRadius: '50%', background: green }} />
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: '#166534' }}>Gmail Inbox Connected</div>
                <div style={{ fontSize: 11, color: '#15803D' }}>Live inbox sync enabled for shipping operations.</div>
              </div>
            </div>
            <button
              onClick={onDisconnectGmail}
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: '#991B1B',
                background: white,
                border: '1px solid #FECACA',
                borderRadius: 4,
                padding: '6px 12px',
                cursor: 'pointer',
              }}
            >
              Disconnect Gmail
            </button>
          </div>
        ) : (
          <div style={{ background: '#FAF8F5', border: `1px solid ${borderLight}`, borderRadius: 4, padding: 18 }}>
            <div style={{ fontSize: 12, color: muted, marginBottom: 14 }}>
              No Gmail account is currently connected to this session. Your inbox will only contain manually uploaded shipments or cached records until connected.
            </div>
            <button
              type="button"
              onClick={() => googleLogin()}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                padding: '9px 16px',
                background: white,
                color: ink,
                border: `1px solid ${border}`,
                borderRadius: 4,
                fontSize: 12,
                fontWeight: 600,
                cursor: 'pointer',
                boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
              }}
            >
              <GoogleIcon /> Connect Gmail Account
            </button>
          </div>
        )}
      </div>

      {/* Database & Infrastructure Card */}
      <div style={{ background: white, border: `1px solid ${border}`, borderRadius: 4, padding: 24, marginBottom: 24 }}>
        <SectionLabel>Database & Storage</SectionLabel>
        <div style={{ marginTop: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0', borderBottom: `1px solid ${borderLight}` }}>
            <span style={{ fontSize: 12, color: muted }}>Primary Database</span>
            <span style={{ fontSize: 12, fontWeight: 600, color: navy }}>Supabase PostgreSQL (Multi-tenant)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0', borderBottom: `1px solid ${borderLight}` }}>
            <span style={{ fontSize: 12, color: muted }}>AI Comparison Engine</span>
            <span style={{ fontSize: 12, fontWeight: 600, color: navy }}>Claude Haiku via FastAPI</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0' }}>
            <span style={{ fontSize: 12, color: muted }}>Multi-Tenant Isolation</span>
            <span style={{ fontSize: 12, fontWeight: 600, color: green }}>Enabled (User Scoped)</span>
          </div>
        </div>
      </div>

      {/* Logout Danger Zone */}
      <div style={{ background: white, border: `1px solid ${border}`, borderRadius: 4, padding: 24 }}>
        <SectionLabel>Session Actions</SectionLabel>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 12 }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: ink }}>Log Out</div>
            <div style={{ fontSize: 11, color: muted }}>Ends your session and clears authentication cookies from this browser.</div>
          </div>
          <button
            onClick={onLogout}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              fontSize: 12,
              fontWeight: 600,
              color: '#B91C1C',
              background: '#FEF2F2',
              border: '1px solid #FECACA',
              borderRadius: 4,
              padding: '8px 16px',
              cursor: 'pointer',
            }}
          >
            <LogoutIcon /> Log Out
          </button>
        </div>
      </div>
    </div>
  )
}

