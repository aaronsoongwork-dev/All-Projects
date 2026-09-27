import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL ?? "";
const anonKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY ?? "";

/**
 * True when Supabase credentials are present in .env.
 *
 * When false the app runs in local dev mode: Login accepts any credentials
 * and the backend (with DISABLE_AUTH=true) serves requests without a token.
 * This lets the team work on the app before the Supabase project exists —
 * see .env.example.
 */
export const isSupabaseConfigured = Boolean(url && anonKey);

/**
 * Null when unconfigured, so every call site has to make a deliberate
 * decision about the dev path rather than blowing up on a null client.
 */
export const supabase: SupabaseClient | null = isSupabaseConfigured
  ? createClient(url, anonKey, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
      },
    })
  : null;

/**
 * The JWT the backend verifies, or null in dev mode.
 *
 * Read fresh on every request rather than cached: supabase-js rotates the
 * access token in the background, and a stale one means a 401 mid-session.
 */
export async function getAccessToken(): Promise<string | null> {
  if (!supabase) return null;
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}
