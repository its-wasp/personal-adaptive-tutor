import { useAuth } from "../hooks/useAuth";

/**
 * Placeholder dashboard — we'll replace this with the knowledge graph,
 * progress overview, and recommendations in a later step. For now it
 * just proves auth works end-to-end.
 */
export default function Dashboard() {
  const { user, logout } = useAuth();

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

      <p className="mt-8 text-sm text-slate-500">
        Knowledge graph, progress, and recommendations will live here.
      </p>
    </div>
  );
}
