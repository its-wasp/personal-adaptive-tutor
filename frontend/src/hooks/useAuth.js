import { useContext } from "react";
import { AuthContext } from "../context/auth-context";

/**
 * Consume AuthContext. Throws if used outside <AuthProvider>.
 * Failing loudly beats silently returning `null` and causing
 * confusing downstream errors.
 */
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside <AuthProvider>");
  }
  return ctx;
}
