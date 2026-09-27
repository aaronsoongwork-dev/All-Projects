import { useState, useEffect, useCallback, useRef } from 'react'
import type { Page, GmailEmail, UserInfo, ComparisonField, ClassifyingState } from '../types'
import { emailTypeLabel } from '../types'
import { bg, CRUMBS } from '../constants/tokens'
import { Sidebar } from '../components/layout/Sidebar'
import { TopBar } from '../components/layout/TopBar'
import { useToasts, ToastContainer } from '../components/Toast'
import {
  supabase,
  signOutSupabase,
  setSupabaseCustomToken,
  getSupabaseCustomToken,
  clearSupabaseCustomToken,
} from '../services/supabase'
import {
  getCachedEmailsApi,
  syncUserWithBackendApi,
  syncGmailInboxApi,
  compareEmailFromGmailApi,
  uploadEmlApi,
  getComparisonsApi,
  mapEmailRecordToGmailEmail,
} from '../services/api'
import { fetchInBatches, getUserInfo } from '../services/gmail'

// Pages
import { LoginPage } from '../pages/LoginPage'
import { DashboardPage } from '../pages/DashboardPage'
import { InboxPage } from '../pages/InboxPage'
import { EmailDetailPage } from '../pages/EmailDetailPage'
import { ProcessingPage } from '../pages/ProcessingPage'
import { ComparisonPage } from '../pages/ComparisonPage'
import { ReviewPage } from '../pages/ReviewPage'
import { ReviewDetailPage } from '../pages/ReviewDetailPage'
import { ReportsPage } from '../pages/ReportsPage'
import { UploadPage } from '../pages/UploadPage'
import { UploadComparisonPage } from '../pages/UploadComparisonPage'
import { SettingsPage } from '../pages/SettingsPage'

const GMAIL_TOKEN_STORAGE_KEY = 'shipcheck_gmail_token'
const PAGE_STORAGE_KEY = 'shipcheck_page'
const SELECTED_EMAIL_STORAGE_KEY = 'shipcheck_selected_email_id'
const SELECTED_REVIEW_STORAGE_KEY = 'shipcheck_selected_review_id'
const UPLOAD_RESULT_STORAGE_KEY = 'shipcheck_upload_result'

const RESTORABLE_PAGES: Page[] = [
  'dashboard', 'inbox', 'email-detail', 'comparison', 'review',
  'review-detail', 'reports', 'upload', 'upload-comparison', 'settings',
]

function readStoredGmailToken(): string | null {
  try {
    return sessionStorage.getItem(GMAIL_TOKEN_STORAGE_KEY)
  } catch {
    return null
  }
}

// Which page/detail-item the user was on survives a refresh via
// sessionStorage, the same way the Gmail token already does - so reloading
// the tab doesn't unexpectedly bounce back to the dashboard.
function readStoredPage(): Page {
  try {
    const raw = sessionStorage.getItem(PAGE_STORAGE_KEY) as Page | null
    return raw && RESTORABLE_PAGES.includes(raw) ? raw : 'dashboard'
  } catch {
    return 'dashboard'
  }
}

function readStoredId(key: string): string {
  try {
    return sessionStorage.getItem(key) || ''
  } catch {
    return ''
  }
}

function readStoredUploadResult(): { fields: ComparisonField[]; siName: string; blName: string } | null {
  try {
    const raw = sessionStorage.getItem(UPLOAD_RESULT_STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export default function App() {
  // The Google OAuth access token only lives ~1hr and has no refresh token
  // (implicit flow, no backend token exchange) - but persisting it to
  // sessionStorage at least survives a page reload within the same tab,
  // instead of silently losing Gmail connectivity on every refresh.
  const [gmailToken, setGmailTokenState] = useState<string | null>(readStoredGmailToken)
  const setGmailToken = useCallback((token: string | null) => {
    setGmailTokenState(token)
    try {
      if (token) sessionStorage.setItem(GMAIL_TOKEN_STORAGE_KEY, token)
      else sessionStorage.removeItem(GMAIL_TOKEN_STORAGE_KEY)
    } catch {
      // sessionStorage unavailable (private mode, etc.) - token just won't survive reloads
    }
  }, [])
  const [user, setUser] = useState<UserInfo | null>(null)
  const [emails, setEmails] = useState<GmailEmail[]>([])
  const emailsRef = useRef<GmailEmail[]>(emails)
  emailsRef.current = emails
  const [loading, setLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [nextPageToken, setNextPageToken] = useState<string | null>(null)
  const [page, setPage] = useState<Page>(readStoredPage)
  const [selectedEmailId, setSelectedEmailId] = useState(() => readStoredId(SELECTED_EMAIL_STORAGE_KEY))
  const [selectedReviewId, setSelectedReviewId] = useState(() => readStoredId(SELECTED_REVIEW_STORAGE_KEY))
  const [uploadResult, setUploadResult] = useState<{ fields: ComparisonField[]; siName: string; blName: string } | null>(readStoredUploadResult)

  // Persist navigation state across reloads (mirrors the Gmail token pattern above).
  useEffect(() => {
    try { sessionStorage.setItem(PAGE_STORAGE_KEY, page) } catch { /* sessionStorage unavailable */ }
  }, [page])
  useEffect(() => {
    try {
      if (selectedEmailId) sessionStorage.setItem(SELECTED_EMAIL_STORAGE_KEY, selectedEmailId)
      else sessionStorage.removeItem(SELECTED_EMAIL_STORAGE_KEY)
    } catch { /* sessionStorage unavailable */ }
  }, [selectedEmailId])
  useEffect(() => {
    try {
      if (selectedReviewId) sessionStorage.setItem(SELECTED_REVIEW_STORAGE_KEY, selectedReviewId)
      else sessionStorage.removeItem(SELECTED_REVIEW_STORAGE_KEY)
    } catch { /* sessionStorage unavailable */ }
  }, [selectedReviewId])
  useEffect(() => {
    try {
      if (uploadResult) sessionStorage.setItem(UPLOAD_RESULT_STORAGE_KEY, JSON.stringify(uploadResult))
      else sessionStorage.removeItem(UPLOAD_RESULT_STORAGE_KEY)
    } catch { /* sessionStorage unavailable */ }
  }, [uploadResult])
  const [classifying, setClassifying] = useState<ClassifyingState>({
    active: false,
    current: 0,
    total: 0,
    error: null,
  })
  const [apiError, setApiError] = useState<string | null>(null)
  const [loadMoreNotice, setLoadMoreNotice] = useState<string | null>(null)
  const [authChecking, setAuthChecking] = useState(true)
  const { toasts, pushToast, dismissToast } = useToasts()

  // 1. Check for active Supabase cookie session on initial mount
  useEffect(() => {
    async function checkSession() {
      try {
        let activeUser: UserInfo | null = null
        const { data: { session } } = await supabase.auth.getSession()
        if (session?.user) {
          const u = session.user
          activeUser = {
            id: u.id,
            email: u.email || '',
            name: u.user_metadata?.full_name || u.email?.split('@')[0] || 'User',
            provider: 'supabase',
          }
          setUser(activeUser)
        } else {
          // Check if custom Supabase JWT is in cookie
          const customToken = getSupabaseCustomToken()
          if (customToken) {
            try {
              const base64Url = customToken.split('.')[1]
              const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
              const payload = JSON.parse(decodeURIComponent(atob(base64).split('').map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join('')))
              if (payload.exp * 1000 > Date.now()) {
                activeUser = {
                  id: payload.sub,
                  email: payload.email,
                  name: payload.user_metadata?.full_name || payload.email.split('@')[0],
                  picture: payload.user_metadata?.avatar_url,
                  provider: 'google',
                }
                setUser(activeUser)
              } else {
                clearSupabaseCustomToken()
              }
            } catch {
              clearSupabaseCustomToken()
            }
          }
        }

        // Unblock auth checking immediately if a user is found so the skeleton layout renders
        if (activeUser) {
          setAuthChecking(false)
          // Any authenticated user can sync the shared inbox now - it goes
          // through the backend's own Gmail connection, not this browser's.
          loadGmailEmails()
        } else {
          setAuthChecking(false)
        }
      } catch (err) {
        console.error('Session check failed:', err)
        setAuthChecking(false)
      }
    }
    checkSession()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Tracks emails currently mid-comparison so the UI can show a spinner only
  // while a request is genuinely in flight - never inferred from status
  // alone, otherwise an email that never got auto-compared (e.g. classified
  // in an earlier session, before auto-compare existed, or whose Gmail
  // attachment fetch silently failed) would show "Comparing…" forever with
  // nothing actually running and no way to retry.
  const [comparingIds, setComparingIds] = useState<Set<string>>(new Set())

  // Per-email compare failure reasons, so EmailDetailPage (which doesn't
  // render the global apiError banner) can show exactly why a specific
  // email's comparison didn't run, instead of a click that looks like a
  // no-op.
  const [compareErrors, setCompareErrors] = useState<Record<string, string>>({})

  // Fetches an email's Gmail attachments via the backend's shared server-side
  // Gmail connection (not this browser's own token - every team member can
  // trigger this regardless of who's logged in) and runs the compare
  // pipeline against them. Used both as the automatic post-classify trigger
  // and as the manual "Compare Now" retry button.
  const compareEmailNow = useCallback(async (email: GmailEmail) => {
    setCompareErrors(prev => {
      if (!(email.id in prev)) return prev
      const { [email.id]: _drop, ...rest } = prev
      return rest
    })
    if (email.id.startsWith('eml_')) {
      // Uploaded directly (not synced from Gmail) - already compared server-side at upload time if possible.
      return null
    }
    setComparingIds(prev => new Set(prev).add(email.id))
    try {
      const result = await compareEmailFromGmailApi(email.id)
      setEmails(prev => prev.map(e => (
        e.id === email.id ? { ...e, status: result.status, fields: result.fields, comparisonId: result.comparison_id } : e
      )))
      return result
    } catch (err: any) {
      console.warn(`Compare failed for email ${email.id}:`, err)
      // A client-side timeout doesn't mean the comparison failed - the
      // backend keeps extracting/comparing regardless of whether this
      // request gave up waiting, so it likely finished; check back shortly.
      const isTimeout = /timed out/i.test(err.message || '')
      const msg = isTimeout
        ? "This is taking a while - it's likely still finishing on the server. Check back in a moment or try again."
        : (err.message || String(err))
      setApiError(`Comparison for "${email.subject.slice(0, 40)}": ${msg}`)
      setCompareErrors(prev => ({ ...prev, [email.id]: msg }))
      return null
    } finally {
      setComparingIds(prev => {
        const next = new Set(prev)
        next.delete(email.id)
        return next
      })
    }
  }, [])

  // Sweeps the full email list for any Document Comparison email still
  // sitting at "New" - whether it just synced, came back from the cache on
  // initial load, or was uploaded as .eml - and auto-compares it. Runs once
  // per email id (tracked in a ref, not state, so it doesn't itself
  // retrigger this effect) so a failed attempt doesn't loop forever; the
  // "Compare Now" button on EmailDetailPage covers manual retry.
  const autoCompareAttempted = useRef<Set<string>>(new Set())
  useEffect(() => {
    const candidates = emails.filter(e =>
      e.type === 'Document Comparison' &&
      e.status === 'New' &&
      e.hasAttachments &&
      !e.id.startsWith('eml_') &&
      !autoCompareAttempted.current.has(e.id)
    )
    if (!candidates.length) return
    candidates.forEach(e => autoCompareAttempted.current.add(e.id))
    fetchInBatches(candidates, compareEmailNow, 8)
  }, [emails, compareEmailNow])

  // Loads the shared inbox: instant cache read, then a live sync via the
  // backend's shared server-side Gmail connection (one team refresh token -
  // works the same for every team member, regardless of whose browser this
  // is or whether they've ever personally logged into Gmail here).
  // Classification happens server-side as part of the sync itself, so the
  // returned records already have real email_type/status.
  const loadGmailEmails = useCallback(async (): Promise<{ ok: boolean; newCount: number }> => {
    setLoading(true)
    setApiError(null)
    try {
      // 1. Instant cache retrieval from Supabase Postgres (<100ms)
      try {
        const cached = await getCachedEmailsApi(500)
        if (cached && cached.length > 0) {
          setEmails(cached)
          // Unblock UI immediately so the user can interact with their inbox with 0 load time
          setLoading(false)
        }
      } catch (err) {
        console.warn('Cache retrieval note:', err)
      }

      // 2. Live sync of the latest 25 messages via the shared Gmail connection
      const res = await syncGmailInboxApi(undefined, 25)
      setNextPageToken(res.next_page_token || null)
      const synced = res.emails.map(mapEmailRecordToGmailEmail)
      const prevIds = new Set(emailsRef.current.map(e => e.id))
      const newCount = synced.filter(e => !prevIds.has(e.id)).length
      setEmails(prev => {
        const byId = new Map(prev.map(e => [e.id, e]))
        for (const e of synced) byId.set(e.id, e)
        // Newly-seen ids go to the front, everything else keeps its position
        const fresh = synced.filter(e => !prevIds.has(e.id))
        return [...fresh, ...prev.map(e => byId.get(e.id)!)]
      })
      return { ok: true, newCount }
    } catch (err: any) {
      // A client-side timeout doesn't mean the sync failed - the backend
      // keeps classifying in its thread pool regardless of whether this
      // request gave up waiting, so it likely finished; the data just
      // isn't reflected here yet. Hitting Refresh will pick it up from cache.
      const isTimeout = /timed out/i.test(err.message || '')
      setApiError(isTimeout
        ? `Gmail sync is taking a while - it's likely still finishing on the server. Try Refresh again in a moment.`
        : `Failed to sync emails: ${err.message || String(err)}`)
      return { ok: false, newCount: 0 }
    } finally {
      setLoading(false)
    }
  }, [])

  // Pagination through the shared inbox
  const loadMoreEmails = useCallback(async () => {
    if (!nextPageToken || loadingMore) return
    setLoadingMore(true)
    setApiError(null)
    setLoadMoreNotice(null)
    try {
      const res = await syncGmailInboxApi(nextPageToken, 25)
      setNextPageToken(res.next_page_token || null)

      const synced = res.emails.map(mapEmailRecordToGmailEmail)
      const existingIds = new Set(emailsRef.current.map(e => e.id))
      const trulyNew = synced.filter(e => !existingIds.has(e.id))

      if (trulyNew.length > 0) {
        setEmails(prev => [...trulyNew, ...prev])
      } else if (!res.next_page_token) {
        setLoadMoreNotice("You've reached the end of your inbox - no more emails to load.")
      } else {
        setLoadMoreNotice('No new emails in that batch (already synced) - the rest of your inbox may still have more.')
      }
    } catch (err: any) {
      const isTimeout = /timed out/i.test(err.message || '')
      setApiError(isTimeout
        ? `Loading more emails is taking a while - it's likely still finishing on the server. Try again in a moment.`
        : `Failed to load more emails: ${err.message || String(err)}`)
    } finally {
      setLoadingMore(false)
    }
  }, [nextPageToken, loadingMore])

  // Handlers
  async function handleGoogleLogin(t: string) {
    setGmailToken(t)
    setPage('dashboard')
    setLoading(true)
    let u: UserInfo = { email: 'user@gmail.com', name: 'Google User', provider: 'google' }
    try {
      u = await getUserInfo(t)
      setUser(u)
    } catch {
      setUser(u)
    }

    // Automatically sync Google user into Supabase auth.users & store cookie session
    try {
      const syncRes = await syncUserWithBackendApi({
        email: u.email,
        name: u.name,
        picture: u.picture,
        provider: 'google',
      })
      setSupabaseCustomToken(syncRes.token)
      setUser({
        id: syncRes.user_id,
        email: syncRes.email,
        name: syncRes.name || u.name,
        picture: u.picture,
        provider: 'google',
      })
    } catch (err) {
      console.warn('Backend user sync notice:', err)
    }

    loadGmailEmails()
  }

  function handleSupabaseLogin(userInfo: UserInfo) {
    setUser(userInfo)
    setPage('dashboard')
    loadGmailEmails()
  }

  async function handleLogout() {
    try {
      await signOutSupabase()
    } catch (err) {
      console.error('Logout error:', err)
    }
    clearSupabaseCustomToken()
    setUser(null)
    setGmailToken(null)
    setEmails([])
    setNextPageToken(null)
    setPage('dashboard')
    setSelectedEmailId('')
    setSelectedReviewId('')
    setUploadResult(null)
  }

  function selectEmail(id: string) {
    setSelectedEmailId(id)
    setPage('email-detail')
  }

  // Manual "Refresh" button in the top bar - loadGmailEmails() itself also
  // runs silently on login/mount, so the toast lives here rather than inside
  // it (we don't want a popup every time the app loads).
  async function handleManualRefresh() {
    const toastId = pushToast('Refreshing inbox…', 'info')
    const { ok, newCount } = await loadGmailEmails()
    if (ok) {
      pushToast(newCount > 0 ? `Inbox refreshed — ${newCount} new email${newCount !== 1 ? 's' : ''}.` : 'Inbox refreshed — no new emails.', 'success', { id: toastId })
    } else {
      pushToast('Failed to refresh inbox — see the error banner for details.', 'error', { id: toastId })
    }
  }

  // Uploads a raw .eml file: backend parses/classifies/auto-compares it,
  // then it's added straight into the inbox list like a synced Gmail message.
  // A toast tracks the whole lifecycle (uploading -> already-uploaded /
  // success / failure) since this used to look like it silently did nothing,
  // especially re-uploading the same file (the backend recognizes it by
  // content hash and just returns the existing record with no visible change
  // to the list).
  async function handleUploadEml(file: File) {
    const toastId = pushToast(`Uploading "${file.name}"…`, 'info')
    try {
      const { record, wasDuplicate } = await uploadEmlApi(file)
      const mapped = mapEmailRecordToGmailEmail(record)
      setEmails(prev => {
        const exists = prev.some(e => e.id === mapped.id)
        return exists ? prev.map(e => (e.id === mapped.id ? mapped : e)) : [mapped, ...prev]
      })
      if (wasDuplicate) {
        pushToast(`"${file.name}" was already uploaded — showing the existing result.`, 'error', { id: toastId, autoDismissMs: 5000 })
      } else {
        pushToast(`"${file.name}" uploaded and classified as ${emailTypeLabel(mapped.type)}.`, 'success', { id: toastId })
      }
    } catch (err: any) {
      pushToast(`Failed to upload "${file.name}": ${err.message || String(err)}`, 'error', { id: toastId })
      setApiError(`EML upload failed: ${err.message || String(err)}`)
    }
  }

  // Opens the comparison report for an email whose auto-compare already ran.
  // If the fields aren't in local state yet (e.g. after a page reload),
  // fetches the saved ComparisonRecord for this email first.
  async function openComparison(id: string) {
    const email = emails.find(e => e.id === id)
    if (email && !email.fields) {
      try {
        const records = await getComparisonsApi(1, 0, id)
        if (records[0]) {
          setEmails(prev => prev.map(e => (
            e.id === id ? { ...e, fields: records[0].fields, comparisonId: records[0].id } : e
          )))
        }
      } catch (err) {
        console.warn(`Failed to fetch comparison for email ${id}:`, err)
      }
    }
    setPage('comparison')
  }

  // Show nothing or blank beige during initial session restore
  if (authChecking) {
    return <div style={{ minHeight: '100vh', background: bg }} />
  }

  // If not logged in, always show LoginPage
  if (!user) {
    return (
      <LoginPage
        onGoogleLogin={handleGoogleLogin}
        onSupabaseLogin={handleSupabaseLogin}
      />
    )
  }

  const selectedEmail = emails.find(e => e.id === selectedEmailId)
  const sidebarAccent: 'success' | 'error' | null = toasts.some(t => t.type === 'error')
    ? 'error'
    : toasts.some(t => t.type === 'success')
    ? 'success'
    : null

  return (
    <div className="app-shell" style={{ background: bg }}>
      <Sidebar
        page={page}
        onNav={setPage}
        user={user}
        emails={emails}
        onLogout={handleLogout}
        accent={sidebarAccent}
      />
      <div className="app-main">
        <TopBar
          crumb={CRUMBS[page] || 'ShipCheck Operations'}
          onRefresh={page === 'inbox' ? handleManualRefresh : undefined}
          loading={loading}
          classifying={classifying}
        />
        <main className="app-page-content">
          {page === 'dashboard' && (
            <DashboardPage
              emails={emails}
              user={user}
              onNav={setPage}
              onSelect={selectEmail}
              loading={loading}
              classifying={classifying}
              apiError={apiError}
              comparingIds={comparingIds}
            />
          )}
          {page === 'inbox' && (
            <InboxPage
              emails={emails}
              onSelect={selectEmail}
              loading={loading}
              classifying={classifying}
              apiError={apiError}
              onClearError={() => { setApiError(null); setClassifying(prev => ({ ...prev, error: null })) }}
              hasMore={!!nextPageToken}
              onLoadMore={loadMoreEmails}
              loadingMore={loadingMore}
              loadMoreNotice={loadMoreNotice}
              onUploadEml={handleUploadEml}
              comparingIds={comparingIds}
            />
          )}
          {page === 'email-detail' && selectedEmail && (
            <EmailDetailPage
              email={selectedEmail}
              onBack={() => setPage('inbox')}
              isComparing={comparingIds.has(selectedEmail.id)}
              gmailConnected={true}
              onGoToSettings={() => setPage('settings')}
              compareError={compareErrors[selectedEmail.id] || null}
              onProcess={async () => {
                if (selectedEmail.status === 'New' || selectedEmail.status === 'Processing') {
                  const result = await compareEmailNow(selectedEmail)
                  if (!result) return
                  setPage('comparison')
                } else {
                  openComparison(selectedEmail.id)
                }
              }}
            />
          )}
          {page === 'processing' && (
            <ProcessingPage onDone={() => setPage('comparison')} />
          )}
          {page === 'comparison' && (
            <ComparisonPage
              onBack={() => setPage('email-detail')}
              onGoToUpload={() => setPage('upload')}
              subject={selectedEmail?.subject}
              fields={selectedEmail?.fields}
            />
          )}
          {page === 'review' && (
            <ReviewPage
              emails={emails}
              onSelect={id => { setSelectedReviewId(id); setPage('review-detail') }}
              loading={loading}
            />
          )}
          {page === 'review-detail' && (
            <ReviewDetailPage
              id={selectedReviewId}
              emails={emails}
              user={user}
              onBack={() => setPage('review')}
              onResolve={(id, status) => {
                setEmails(prev => prev.map(e => e.id === id ? { ...e, status } : e))
                setPage('review')
              }}
            />
          )}
          {page === 'reports' && (
            <ReportsPage />
          )}
          {page === 'upload' && (
            <UploadPage
              onCompare={(fields, siName, blName) => {
                setUploadResult({ fields, siName, blName })
                setPage('upload-comparison')
              }}
            />
          )}
          {page === 'upload-comparison' && uploadResult && (
            <UploadComparisonPage
              result={uploadResult.fields}
              siName={uploadResult.siName}
              blName={uploadResult.blName}
              onBack={() => setPage('upload')}
            />
          )}
          {page === 'settings' && (
            <SettingsPage
              user={user}
              gmailToken={gmailToken}
              onConnectGmail={t => {
                setGmailToken(t)
              }}
              onDisconnectGmail={() => {
                setGmailToken(null)
              }}
              onLogout={handleLogout}
            />
          )}
        </main>
      </div>
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  )
}
