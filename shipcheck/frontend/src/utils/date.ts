// Every displayed date/time is rendered in a fixed timezone (Malaysia, GMT+8,
// no DST) rather than the raw sender's own timezone offset or the viewer's
// browser locale - otherwise the same email can show a different-looking
// time to different people, or show a raw offset like "-0700 (PDT)" verbatim
// from whichever mail client the original sender used.
const DISPLAY_TIMEZONE = 'Asia/Kuala_Lumpur'

function ymdInZone(ts: number, timeZone: string): string {
  return new Intl.DateTimeFormat('en-CA', { timeZone, year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date(ts))
}

/**
 * Formats a timestamp (epoch ms) the way the inbox list shows it: a time
 * for today, "Yesterday", a weekday within the last week, or a short date -
 * always evaluated in Malaysia time regardless of the underlying data's
 * original timezone or the viewer's own machine.
 */
export function fmtDate(ts: number): string {
  const nowTs = Date.now()
  const todayKey = ymdInZone(nowTs, DISPLAY_TIMEZONE)
  const dateKey = ymdInZone(ts, DISPLAY_TIMEZONE)

  if (dateKey === todayKey) {
    return new Intl.DateTimeFormat('en-US', { timeZone: DISPLAY_TIMEZONE, hour: '2-digit', minute: '2-digit' }).format(new Date(ts))
  }

  const yesterdayKey = ymdInZone(nowTs - 86400000, DISPLAY_TIMEZONE)
  if (dateKey === yesterdayKey) return 'Yesterday'

  if (nowTs - ts < 604800000) {
    return new Intl.DateTimeFormat('en-US', { timeZone: DISPLAY_TIMEZONE, weekday: 'short' }).format(new Date(ts))
  }

  return new Intl.DateTimeFormat('en-US', { timeZone: DISPLAY_TIMEZONE, day: 'numeric', month: 'short' }).format(new Date(ts))
}

/**
 * Full date + time (e.g. for detail views), also fixed to Malaysia time.
 */
export function fmtDateTime(ts: number): string {
  return new Intl.DateTimeFormat('en-US', {
    timeZone: DISPLAY_TIMEZONE,
    day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  }).format(new Date(ts))
}
