import { useState } from 'react'
import { useGoogleLogin } from '@react-oauth/google'
import { signInWithEmail, signUpWithEmail } from '../services/supabase'
import type { UserInfo } from '../types'
import {
  bg,
  white,
  border,
  borderLight,
  navy,
  ink,
  muted,
  faint,
  amberBg,
  amberBdr,
  green,
} from '../constants/tokens'
import { SectionLabel, GoogleIcon, Spinner } from '../components/primitives'

const hasClientId = !!import.meta.env.VITE_GOOGLE_CLIENT_ID

function GoogleLoginButton({ onLogin }: { onLogin: (token: string) => void }) {
  const googleLogin = useGoogleLogin({
    scope: 'https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile',
    onSuccess: res => onLogin(res.access_token),
    onError: err => console.error('Google login failed', err),
  })
  return (
    <button
      onClick={() => googleLogin()}
      type="button"
      style={{
        width: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 10,
        padding: '11px 20px',
        background: white,
        color: ink,
        border: `1px solid ${border}`,
        borderRadius: 4,
        fontSize: 12,
        fontWeight: 600,
        cursor: 'pointer',
      }}
    >
      <GoogleIcon /> Continue with Google (Syncs Gmail)
    </button>
  )
}

interface LoginPageProps {
  onGoogleLogin: (token: string) => void
  onSupabaseLogin: (user: UserInfo) => void
}

export function LoginPage({ onGoogleLogin, onSupabaseLogin }: LoginPageProps) {
  const [tab, setTab] = useState<'signin' | 'signup'>('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [infoMsg, setInfoMsg] = useState<string | null>(null)

  async function handleEmailAuth(e: React.FormEvent) {
    e.preventDefault()
    if (!email || !password) {
      setErrorMsg('Please enter both email and password.')
      return
    }
    setErrorMsg(null)
    setInfoMsg(null)
    setLoading(true)

    try {
      if (tab === 'signin') {
        const { user, error } = await signInWithEmail(email, password)
        if (error) {
          setErrorMsg(error)
        } else if (user) {
          onSupabaseLogin({
            id: user.id,
            email: user.email || email,
            name: user.user_metadata?.full_name || email.split('@')[0],
            provider: 'supabase',
          })
        }
      } else {
        const { user, session, error } = await signUpWithEmail(email, password, fullName)
        if (error) {
          setErrorMsg(error)
        } else if (user && session) {
          onSupabaseLogin({
            id: user.id,
            email: user.email || email,
            name: user.user_metadata?.full_name || fullName || email.split('@')[0],
            provider: 'supabase',
          })
        } else if (user && !session) {
          setInfoMsg('Account created! If email confirmation is enabled, please check your inbox to confirm your account.')
        }
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Authentication error occurred.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: bg, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
      {/* Brand Header */}
      <div style={{ marginBottom: 28, textAlign: 'center' }}>
        <div style={{ fontFamily: 'Playfair Display, serif', fontSize: 36, fontWeight: 700, color: ink, lineHeight: 1 }}>
          Ship<em style={{ color: navy }}>Check</em>
        </div>
        <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.14em', textTransform: 'uppercase', color: faint, marginTop: 6 }}>
          Shipping Operations Platform
        </div>
      </div>

      {/* Main Login / Signup Card */}
      <div style={{ width: '100%', maxWidth: 400, border: `1px solid ${border}`, borderRadius: 4, background: white, overflow: 'hidden', boxShadow: '0 4px 20px rgba(0,0,0,0.04)' }}>
        {/* Tabs */}
        <div style={{ display: 'flex', borderBottom: `1px solid ${borderLight}`, background: '#FAF8F5' }}>
          <button
            type="button"
            onClick={() => { setTab('signin'); setErrorMsg(null); setInfoMsg(null) }}
            style={{
              flex: 1,
              padding: '12px',
              border: 'none',
              background: tab === 'signin' ? white : 'transparent',
              borderBottom: tab === 'signin' ? `2px solid ${navy}` : '2px solid transparent',
              fontSize: 12,
              fontWeight: tab === 'signin' ? 700 : 500,
              color: tab === 'signin' ? navy : muted,
              cursor: 'pointer',
              letterSpacing: '0.04em',
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setTab('signup'); setErrorMsg(null); setInfoMsg(null) }}
            style={{
              flex: 1,
              padding: '12px',
              border: 'none',
              background: tab === 'signup' ? white : 'transparent',
              borderBottom: tab === 'signup' ? `2px solid ${navy}` : '2px solid transparent',
              fontSize: 12,
              fontWeight: tab === 'signup' ? 700 : 500,
              color: tab === 'signup' ? navy : muted,
              cursor: 'pointer',
              letterSpacing: '0.04em',
            }}
          >
            Create Account
          </button>
        </div>

        <div style={{ padding: '24px 32px 28px' }}>
          <SectionLabel>{tab === 'signin' ? 'Account Login' : 'New Registration'}</SectionLabel>
          <div style={{ fontFamily: 'Playfair Display, serif', fontSize: 20, fontWeight: 700, color: ink, marginBottom: 4 }}>
            {tab === 'signin' ? 'Welcome back' : 'Get started with ShipCheck'}
          </div>
          <p style={{ fontSize: 11, color: muted, marginBottom: 20, lineHeight: 1.5 }}>
            {tab === 'signin'
              ? 'Enter your credentials to access your multi-tenant shipping records.'
              : 'Create an account to store and analyze shipping documents.'}
          </p>

          {errorMsg && (
            <div style={{ fontSize: 11, color: '#991B1B', background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: 4, padding: '9px 12px', marginBottom: 16 }}>
              {errorMsg}
            </div>
          )}

          {infoMsg && (
            <div style={{ fontSize: 11, color: '#166534', background: '#DCFCE7', border: '1px solid #86EFAC', borderRadius: 4, padding: '9px 12px', marginBottom: 16 }}>
              {infoMsg}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleEmailAuth} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {tab === 'signup' && (
              <div>
                <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: muted, marginBottom: 4 }}>Full Name</label>
                <input
                  type="text"
                  placeholder="e.g. Sarah Jenkins"
                  value={fullName}
                  onChange={e => setFullName(e.target.value)}
                  style={{ width: '100%', padding: '9px 12px', border: `1px solid ${border}`, borderRadius: 4, fontSize: 13, background: '#FCFBF9' }}
                />
              </div>
            )}

            <div>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: muted, marginBottom: 4 }}>Email Address</label>
              <input
                type="email"
                required
                placeholder="name@company.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                style={{ width: '100%', padding: '9px 12px', border: `1px solid ${border}`, borderRadius: 4, fontSize: 13, background: '#FCFBF9' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: muted, marginBottom: 4 }}>Password</label>
              <input
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                style={{ width: '100%', padding: '9px 12px', border: `1px solid ${border}`, borderRadius: 4, fontSize: 13, background: '#FCFBF9' }}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                width: '100%',
                padding: '11px',
                background: navy,
                color: white,
                border: 'none',
                borderRadius: 4,
                fontSize: 12,
                fontWeight: 700,
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.7 : 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
                marginTop: 4,
              }}
            >
              {loading && <Spinner size={12} color={white} />}
              {tab === 'signin' ? 'Sign In' : 'Create Account'}
            </button>
          </form>

          {/* Divider */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '20px 0' }}>
            <div style={{ flex: 1, height: 1, background: borderLight }} />
            <span style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: faint }}>or</span>
            <div style={{ flex: 1, height: 1, background: borderLight }} />
          </div>

          {/* Alternative Auth Methods */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {hasClientId ? (
              <GoogleLoginButton onLogin={onGoogleLogin} />
            ) : (
              <div style={{ fontSize: 11, color: '#92400E', background: amberBg, border: `1px solid ${amberBdr}`, borderRadius: 4, padding: '9px 12px' }}>
                Google OAuth Client ID not configured.
              </div>
            )}
          </div>

          {/* Scope note */}
          <div style={{ marginTop: 22, paddingTop: 16, borderTop: `1px solid ${borderLight}` }}>
            <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase', color: muted, marginBottom: 8 }}>Included Capabilities</div>
            {['Cookie-persisted multi-tenant sessions', 'Supabase Postgres document sync', 'Optional Gmail automated inbox pipeline'].map(f => (
              <div key={f} style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 11, color: muted, marginBottom: 5 }}>
                <span style={{ color: green, fontWeight: 700 }}>✓</span> {f}
              </div>
            ))}
          </div>
        </div>
      </div>

      <p style={{ fontSize: 10, color: faint, marginTop: 20, textAlign: 'center', maxWidth: 360, lineHeight: 1.5 }}>
        ShipCheck stores your records securely in Supabase PostgreSQL. Cookies are used to safely maintain your active session.
      </p>
    </div>
  )
}

