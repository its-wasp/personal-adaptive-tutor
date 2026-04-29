import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

/**
 * Gate routes that require a logged-in user.
 * While AuthProvider is validating the token we show a neutral loader
 * so we don't redirect-to-login flash on a page refresh.
 */
export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center text-slate-500">
        Loading…
      </div>
    );
  }

  if (!user) {
    // Preserve attempted location so post-login we can send them back.
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
}
