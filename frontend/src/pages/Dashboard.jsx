import { Link, Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

/**
 * Placeholder dashboard — we'll replace this with the knowledge graph,
 * progress overview, and recommendations in a later step. For now it
 * just proves auth works end-to-end.
 *
 * Gates on onboarding: if the user hasn't finished onboarding we bounce
 * them there. Profile is already hydrated by AuthProvider so this is
 * a synchronous check.
 */
export default function Dashboard() {
  const { user, profile, logout } = useAuth();

  if (profile && !profile.onboarding_completed) {
    return <Navigate to="/onboarding" replace />;
  }

  return (
    <div className="mx-auto max-w-3xl p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <button
          onClick={logout}
          className="rounded border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-100"
        >
          Log out
        </button>
      </div>

      <div className="mt-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <p className="text-sm text-slate-500">Logged in as</p>
        <p className="mt-1 text-lg font-medium">{user?.name || "—"}</p>
        <p className="text-sm text-slate-600">{user?.email}</p>
      </div>

      <div className="mt-6 flex gap-3">
        <Link
          to="/chat"
          className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          Start learning
        </Link>
      </div>

      <p className="mt-8 text-sm text-slate-500">
        Knowledge graph, progress, and recommendations will live here.
      </p>
    </div>
  );
}
