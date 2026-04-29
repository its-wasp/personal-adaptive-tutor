import { createContext, useCallback, useEffect, useMemo, useState } from "react";
import { api, tokenStore } from "../lib/api";

/**
 * Global auth state.
 *
 * Two distinct things live here:
 *   user    — identity (id, name, email, role) from /auth/me
 *   profile — preferences + onboarding_completed from /profile/me
 *
 * They come from different endpoints because identity is auth-owned and
 * profile is feature-owned. Keeping them separate avoids one endpoint
 * having to return everything.
 *
 * On mount: if we have a token, fetch both to hydrate. If either fails
 * (stale token), clear everything.
 */
export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch both in parallel — they're independent.
  const hydrate = useCallback(async () => {
    const [me, prof] = await Promise.all([
      api.get("/auth/me"),
      api.get("/profile/me"),
    ]);
    setUser(me);
    setProfile(prof);
  }, []);

  useEffect(() => {
    const token = tokenStore.get();
    if (!token) {
      setLoading(false);
      return;
    }
    hydrate()
      .catch(() => {
        // Any failure here means the token is bad — wipe and force re-login.
        tokenStore.clear();
        setUser(null);
        setProfile(null);
      })
      .finally(() => setLoading(false));
  }, [hydrate]);

  const login = useCallback(
    async (email, password) => {
      const res = await api.post("/auth/login", { email, password }, { auth: false });
      tokenStore.set(res.access_token);
      // After getting the token, fetch both identity + profile so the context
      // is fully hydrated before the caller navigates.
      await hydrate();
      return res.user;
    },
    [hydrate]
  );

  const signup = useCallback(
    async (name, email, password) => {
      const res = await api.post(
        "/auth/signup",
        { name, email, password },
        { auth: false }
      );
      tokenStore.set(res.access_token);
      await hydrate();
      return res.user;
    },
    [hydrate]
  );

  const logout = useCallback(() => {
    tokenStore.clear();
    setUser(null);
    setProfile(null);
  }, []);

  // Exposed so pages can refresh profile state (e.g. after onboarding completes)
  // without a full page reload.
  const refreshProfile = useCallback(async () => {
    const prof = await api.get("/profile/me");
    setProfile(prof);
    return prof;
  }, []);

  const value = useMemo(
    () => ({ user, profile, loading, login, signup, logout, refreshProfile }),
    [user, profile, loading, login, signup, logout, refreshProfile]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
