import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { Session as SupabaseSession } from "@supabase/supabase-js";

import { isSupabaseConfigured, supabase } from "../lib/supabase";
import { clearSessions } from "../utils/emotionEngine";

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  email: string | null;
  isDevMode: boolean;
  /** True once password is right but a TOTP code is still needed. */
  mfaRequired: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<{ needsConfirmation: boolean }>;
  signOut: () => Promise<void>;
  verifyMfa: (code: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const DEV_AUTH_KEY = "em_auth";
const DEV_EMAIL_KEY = "em_email";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<SupabaseSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [mfaRequired, setMfaRequired] = useState(false);

  const [devAuthed, setDevAuthed] = useState(
      () => localStorage.getItem(DEV_AUTH_KEY) === "true",
  );
  const [devEmail, setDevEmail] = useState(() => localStorage.getItem(DEV_EMAIL_KEY));

  // Checks whether the CURRENT session still needs a second factor —
  // used both right after password sign-in and on page load/refresh,
  // since a stored aal1 session shouldn't count as fully authenticated.
  const checkAal = async (): Promise<boolean> => {
    if (!supabase) return false;
    try {
      const { data, error } = await supabase.auth.mfa.getAuthenticatorAssuranceLevel();
      if (error) return false;
      return data.nextLevel === "aal2" && data.nextLevel !== data.currentLevel;
    } catch {
      return false;
    }
  };

  useEffect(() => {
    if (!supabase) {
      setIsLoading(false);
      return;
    }
    supabase.auth.getSession()
        .then(async ({ data }) => {
          setSession(data.session);
          if (data.session) setMfaRequired(await checkAal());
        })
        .catch(() => {})
        .finally(() => setIsLoading(false));

    const { data: sub } = supabase.auth.onAuthStateChange((_event, next) => {
      setSession(next);

      if (!next) {
        clearSessions();
        setMfaRequired(false);
        return;
      }

      // Don't await Supabase Auth calls inside onAuthStateChange.
      setTimeout(() => {
        void checkAal()
            .then((required) => {
              setMfaRequired(required);
            })
            .catch(() => {
              setMfaRequired(false);
            });
      }, 0);
    });

    return () => sub.subscription.unsubscribe();
  }, []);

  const signIn = async (email: string, password: string) => {
    if (!supabase) {
      localStorage.setItem(DEV_AUTH_KEY, "true");
      localStorage.setItem(DEV_EMAIL_KEY, email);
      setDevAuthed(true);
      setDevEmail(email);
      return;
    }

    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw new Error(error.message);

    // Password was correct — now find out if a TOTP code is still needed
    // before this session counts as fully authenticated.
    setMfaRequired(await checkAal());
  };

  const verifyMfa = async (code: string) => {
    if (!supabase) return;

    const { data: factorsData, error: factorsError } = await supabase.auth.mfa.listFactors();
    if (factorsError) throw new Error(factorsError.message);

    const factor = factorsData?.totp?.[0];
    if (!factor) throw new Error("No authenticator app is set up on this account.");

    const { data: challenge, error: challengeError } = await supabase.auth.mfa.challenge({
      factorId: factor.id,
    });
    if (challengeError) throw new Error(challengeError.message);

    const { error: verifyError } = await supabase.auth.mfa.verify({
      factorId: factor.id,
      challengeId: challenge.id,
      code,
    });
    if (verifyError) throw new Error("Invalid code — try again.");

    setMfaRequired(false);
  };

  const signUp = async (email: string, password: string) => {
    if (!supabase) {
      await signIn(email, password);
      return { needsConfirmation: false };
    }

    const { data, error } = await supabase.auth.signUp({ email, password });
    if (error) throw new Error(error.message);
    return { needsConfirmation: !data.session };
  };

  const signOut = async () => {
    clearSessions();
    setMfaRequired(false);
    if (!supabase) {
      localStorage.removeItem(DEV_AUTH_KEY);
      localStorage.removeItem(DEV_EMAIL_KEY);
      setDevAuthed(false);
      setDevEmail(null);
      return;
    }
    await supabase.auth.signOut();
  };

  const value: AuthContextType = {
    // Not authenticated until BOTH a session exists AND mfa (if required) is cleared
    isAuthenticated: isSupabaseConfigured ? (session !== null && !mfaRequired) : devAuthed,
    isLoading,
    email: isSupabaseConfigured ? (session?.user.email ?? null) : devEmail,
    isDevMode: !isSupabaseConfigured,
    mfaRequired,
    signIn,
    signUp,
    signOut,
    verifyMfa,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}