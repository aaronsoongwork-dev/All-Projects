import type { GmailEmail, EmailType, EmailStatus, UserInfo, AttachmentRef } from '../types'
import { fmtDate } from '../utils/date'

export async function delay(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

export async function gmailFetch(token: string, path: string, retries = 5, backoff = 800): Promise<any> {
  for (let attempt = 0; attempt <= retries; attempt++) {
    const r = await fetch(`https://gmail.googleapis.com/gmail/v1/${path}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (r.ok) return r.json()

    // Gmail returns rate-limit errors as 403 (not just 429) with a reason
    // like "rateLimitExceeded"/"userRateLimitExceeded" in the error body -
    // read it so a burst of concurrent requests can back off and retry
    // instead of surfacing a bare, unexplained "Gmail API 403".
    let reason = ''
    let message = ''
    try {
      const body = await r.clone().json()
      reason = body?.error?.errors?.[0]?.reason || ''
      message = body?.error?.message || ''
    } catch {
      // non-JSON error body - fall through with whatever we have
    }

    const isRateLimited = r.status === 429 || (r.status === 403 && /rateLimitExceeded|quotaExceeded/i.test(reason))
    if (isRateLimited && attempt < retries) {
      const wait = backoff * Math.pow(2, attempt) + Math.random() * 300
      await delay(wait)
      continue
    }

    throw new Error(`Gmail API ${r.status}${reason ? ` (${reason})` : ''}${message ? `: ${message}` : ''}`)
  }
}

export async function fetchInBatches<T, R>(items: T[], fn: (item: T) => Promise<R>, concurrency = 5): Promise<R[]> {
  const results: R[] = new Array(items.length)
  let index = 0
  async function worker() {
    while (index < items.length) {
      const i = index++
      results[i] = await fn(items[i])
    }
  }
  const workers = Array.from({ length: Math.min(concurrency, items.length) }, () => worker())
  await Promise.all(workers)
  return results
}

export async function getUserInfo(token: string): Promise<UserInfo> {
  const r = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
    headers: { Authorization: `Bearer ${token}` },
  })
  const d = await r.json()
  return { email: d.email, name: d.name, picture: d.picture, provider: 'google' }
}

export function decodeBase64(str: string) {
  try {
    return decodeURIComponent(
      atob(str.replace(/-/g, '+').replace(/_/g, '/'))
        .split('').map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join('')
    )
  } catch { return '' }
}

export function extractBody(payload: any): string {
  if (!payload) return ''
  if (payload.body?.data) return decodeBase64(payload.body.data)
  if (payload.parts) {
    for (const p of payload.parts) {
      if (p.mimeType === 'text/plain' && p.body?.data) return decodeBase64(p.body.data)
    }
    for (const p of payload.parts) { const n = extractBody(p); if (n) return n }
  }
  return ''
}

export function parseHeader(headers: { name: string; value: string }[], name: string) {
  return headers.find(h => h.name.toLowerCase() === name.toLowerCase())?.value || ''
}

export function classify(subject: string, snippet: string, body: string): EmailType {
  const t = `${subject} ${snippet} ${body}`.toLowerCase()
  if (t.includes('bill of lading') || t.includes('b/l') ||
    (t.includes('bl') && (t.includes('draft') || t.includes('confirm') || t.includes('shipping instruction'))) ||
    (t.includes('draft') && t.includes('lading'))) return 'Document Comparison'
  if (t.includes('invoice') || t.includes('remittance')) return 'Invoice Query'
  if (t.includes('shipping instruction') && !t.includes('bill of lading')) return 'New SI Request'
  if (t.includes('unsubscribe') || t.includes('promotion') || t.includes('special offer')) return 'Spam'
  return 'General'
}

export function parseFrom(from: string) {
  const m = from.match(/^(.*?)\s*<(.+?)>$/)
  return m ? { name: m[1].replace(/"/g, '').trim() || m[2], email: m[2] } : { name: from, email: from }
}

export function extractAttachmentRefs(payload: any): AttachmentRef[] {
  const refs: AttachmentRef[] = []
  function walk(node: any) {
    if (!node) return
    if (node.filename && node.filename.length > 0 && node.body?.attachmentId) {
      refs.push({ filename: node.filename, attachmentId: node.body.attachmentId })
    }
    if (node.parts) {
      for (const p of node.parts) walk(p)
    }
  }
  walk(payload)
  return refs
}

function base64UrlToBytes(base64url: string): Uint8Array {
  const base64 = base64url.replace(/-/g, '+').replace(/_/g, '/')
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
  return bytes
}

/**
 * Fetches a single Gmail attachment's raw bytes as a File.
 */
export async function fetchAttachment(token: string, messageId: string, ref: AttachmentRef): Promise<File> {
  const res = await gmailFetch(token, `users/me/messages/${messageId}/attachments/${ref.attachmentId}`)
  const bytes = base64UrlToBytes(res.data)
  return new File([bytes.buffer as ArrayBuffer], ref.filename)
}

/**
 * Fetches all of a message's attachments as Files, bounded concurrency.
 */
export async function fetchMessageAttachments(token: string, messageId: string, refs: AttachmentRef[]): Promise<File[]> {
  return fetchInBatches(refs, ref => fetchAttachment(token, messageId, ref), 5)
}

/**
 * Looks up a message's attachment refs directly (for emails that were loaded
 * from the backend cache rather than a fresh Gmail page fetch, and so never
 * had their attachmentRefs captured).
 */
export async function fetchMessageAttachmentRefs(token: string, messageId: string): Promise<AttachmentRef[]> {
  const msg = await gmailFetch(token, `users/me/messages/${messageId}?format=full`)
  return extractAttachmentRefs(msg.payload)
}

export interface GmailPageResult {
  emails: GmailEmail[]
  nextPageToken?: string
}

export async function fetchEmailsPage(token: string, pageToken?: string, maxResults = 25): Promise<GmailPageResult> {
  const pageParam = pageToken ? `&pageToken=${encodeURIComponent(pageToken)}` : ''
  const list = await gmailFetch(token, `users/me/messages?maxResults=${maxResults}&q=in:inbox${pageParam}`)
  const ids: string[] = (list.messages || []).map((m: any) => m.id)
  const emails = await fetchInBatches(ids, async id => {
    const msg = await gmailFetch(token, `users/me/messages/${id}?format=full`)
    const headers = msg.payload?.headers || []
    const subject = parseHeader(headers, 'subject') || '(no subject)'
    const from = parseHeader(headers, 'from')
    const { name: fromName, email: fromEmail } = parseFrom(from)
    const dateStr = parseHeader(headers, 'date')
    const timestamp = dateStr ? new Date(dateStr).getTime() : Number(msg.internalDate) || Date.now()
    const snippet = msg.snippet || ''
    const body = extractBody(msg.payload)
    const attachmentRefs = extractAttachmentRefs(msg.payload)
    const hasAttachments = attachmentRefs.length > 0
    return {
      id,
      threadId: msg.threadId,
      from: fromEmail,
      fromName,
      subject,
      snippet,
      date: fmtDate(timestamp),
      timestamp,
      type: 'General',
      status: 'Processing',
      hasAttachments,
      attachmentRefs,
      body: body.slice(0, 2000),
    } as GmailEmail
  }, 5)
  return {
    emails: emails.sort((a, b) => b.timestamp - a.timestamp),
    nextPageToken: list.nextPageToken,
  }
}

