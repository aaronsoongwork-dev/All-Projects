import { createClient, type Session, type User } from '@supabase/supabase-js'

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || 'https://pgindmkanyxakjmqlvcc.supabase.co'
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

/**
 * Cookie-backed storage adapter for Supabase client.
 * Ensures session tokens persist across browser restarts and page refreshes.
 */
const cookieStorage = {
  getItem: (key: string): string | null => {
    if (typeof document === 'undefined') return null
    const name = encodeURIComponent(key) + '='
    const parts = document.cookie.split('; ')
    for (const part of parts) {
      if (part.indexOf(name) === 0) {
        return decodeURIComponent(part.substring(name.length))
      }
    }
    return null
  },
  setItem: (key: string, value: string): void => {
    if (typeof document === 'undefined') return
    const maxAge = 60 * 60 * 24 * 30 // 30 days
    const secure = window.location.protocol === 'https:' ? '; Secure' : ''
    document.cookie = `${encodeURIComponent(key)}=${encodeURIComponent(value)}; path=/; max-age=${maxAge}; SameSite=Lax${secure}`
  },
  removeItem: (key: string): void => {
    if (typeof document === 'undefined') return
    document.cookie = `${encodeURIComponent(key)}=; path=/; max-age=0; SameSite=Lax`
  },
}

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    storage: cookieStorage,
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
  },
})

export function setSupabaseCustomToken(token: string): void {
  cookieStorage.setItem('sb-access-token', token)
}

export function getSupabaseCustomToken(): string | null {
  return cookieStorage.getItem('sb-access-token')
}

export function clearSupabaseCustomToken(): void {
  cookieStorage.removeItem('sb-access-token')
}

/**
 * Returns current access token if logged in with Supabase, or null.
 */
export async function getSupabaseAccessToken(): Promise<string | null> {
  try {
    const custom = getSupabaseCustomToken()
    if (custom) return custom
    const { data: { session } } = await supabase.auth.getSession()
    return session?.access_token || null
  } catch {
    return null
  }
}

/**
 * Sign in with email and password.
 */
export async function signInWithEmail(email: string, password: string): Promise<{ user: User | null; session: Session | null; error: string | null }> {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })
  return {
    user: data.user,
    session: data.session,
    error: error ? error.message : null,
  }
}

/**
 * Sign up with email and password.
 */
export async function signUpWithEmail(email: string, password: string, fullName?: string): Promise<{ user: User | null; session: Session | null; error: string | null }> {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: {
        full_name: fullName || email.split('@')[0],
      },
    },
  })
  return {
    user: data.user,
    session: data.session,
    error: error ? error.message : null,
  }
}

/**
 * Signs the user out of Supabase and clears auth cookies.
 */
export async function signOutSupabase(): Promise<void> {
  await supabase.auth.signOut()
}

/**
 * Gets the current active session.
 */
export async function getCurrentSession(): Promise<Session | null> {
  const { data: { session } } = await supabase.auth.getSession()
  return session
}

/**
 * Gets the current active user.
 */
export async function getCurrentUser(): Promise<User | null> {
  const { data: { user } } = await supabase.auth.getUser()
  return user
}

