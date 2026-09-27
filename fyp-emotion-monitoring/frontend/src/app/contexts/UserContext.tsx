import { createContext, useContext, useState, useEffect, useRef, type ReactNode } from "react";
import { getUser, saveUser, type UserProfile } from "../utils/userProfile";
import { supabase } from "../lib/supabase";

interface UserContextType {
  user: UserProfile;
  /** Persists to Supabase Auth (when configured) before updating local state.
   *  Throws on failure so callers can show an error instead of a false-positive toast. */
  updateUserProfile: (updates: Partial<UserProfile>) => Promise<void>;
  refreshUser: () => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile>(getUser());

  // The onAuthStateChange listener below needs the latest theme without
  // re-subscribing every time it changes — a ref sidesteps the stale-closure
  // issue the previous `user.theme` reference inside that effect had.
  const themeRef = useRef(user.theme);
  themeRef.current = user.theme;

  const updateUserProfile = async (updates: Partial<UserProfile>) => {
    const updated = { ...user, ...updates };

    if (supabase) {
      const { name, avatar, bio, email } = updates;
      const metadata: Record<string, unknown> = {};
      if (name !== undefined) metadata.name = name;
      if (avatar !== undefined) metadata.avatar_url = avatar;
      if (bio !== undefined) metadata.bio = bio;

      const authUpdates: { email?: string; data?: Record<string, unknown> } = {};
      if (Object.keys(metadata).length > 0) authUpdates.data = metadata;
      // Changing email is a distinct, confirmation-gated flow in Supabase —
      // only send it when it actually changed, so a plain name/bio edit
      // doesn't accidentally trigger a "confirm your new email" email.
      if (email !== undefined && email !== user.email) authUpdates.email = email;

      if (Object.keys(authUpdates).length > 0) {
        // Let this throw — callers (Profile.tsx) should catch it and tell
        // the user the save failed, rather than us swallowing it here and
        // updating local state as if it had actually persisted.
        const { error } = await supabase.auth.updateUser(authUpdates);
        if (error) throw error;
      }
    }

    saveUser(updated);
    setUser(updated);
  };

  const refreshUser = () => {
    setUser(getUser());
  };

  // Sync the local profile to whoever is actually logged in via Supabase.
  // Runs on mount (covers refresh with an existing session) and again on
  // every sign-in/sign-out/token-refresh/metadata-update, so switching
  // accounts can't leak the previous user's name/avatar/email into the new
  // session — and so a `supabase.auth.updateUser()` call above (which fires
  // its own USER_UPDATED event) is reflected here too, not just locally.
  useEffect(() => {
    if (!supabase) return; // dev mode — local profile is the only source anyway

    const { data: sub } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.user) {
        const real: UserProfile = {
          id: session.user.id,
          email: session.user.email ?? "",
          name:
              session.user.user_metadata?.name ??
              session.user.email?.split("@")[0] ??
              "User",
          avatar: session.user.user_metadata?.avatar_url ?? "",
          bio: session.user.user_metadata?.bio ?? "",
          createdAt: new Date(session.user.created_at).getTime(),
          theme: themeRef.current, // keep the locally-chosen theme; not an auth concern
        };
        saveUser(real);
        setUser(real);
      } else {
        // Signed out — clear so the next login (possibly a different
        // person on this browser) never sees a stale profile.
        localStorage.removeItem("emotionmonitor_user");
        setUser(getUser()); // falls back to DEFAULT_USER
      }
    });

    return () => sub.subscription.unsubscribe();
  }, []);

  return (
      <UserContext.Provider value={{ user, updateUserProfile, refreshUser }}>
        {children}
      </UserContext.Provider>
  );
}

export function useUser() {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error("useUser must be used within a UserProvider");
  }
  return context;
}
