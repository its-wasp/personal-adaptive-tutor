import { useApiGet } from "../../hooks/useApi";

/**
 * "Recommended next" card for the dashboard.
 *
 * Backend does the heavy lifting: /graph/{subject}/recommend returns a single
 * concept picked from the user's unlocked + not-yet-mastered set, biased
 * toward lowest-mastery and easiest-tier. We just render whatever it returns
 * and let the Dashboard hook up the click handler (so Dashboard owns the
 * "select concept → open detail panel" flow in one place).
 */
export default function RecommendedNext({ subject = "dsa", onPick }) {
  const { data, loading } = useApiGet(`/graph/${subject}/recommend`);

  if (loading) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <p className="text-xs uppercase tracking-wide text-slate-500">Recommended next</p>
        <p className="mt-2 text-sm text-slate-400">Figuring out what's next…</p>
      </div>
    );
  }

  // Backend returns {message: "..."} when there are no candidates.
  if (!data || data.message) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <p className="text-xs uppercase tracking-wide text-slate-500">Recommended next</p>
        <p className="mt-2 text-sm text-slate-600">
          {data?.message || "Nothing queued up — pick any concept from the graph."}
        </p>
      </div>
    );
  }

  const mastery = Math.round((data.current_mastery ?? 0) * 100);

  return (
    <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-4 shadow-sm">
      <p className="text-xs uppercase tracking-wide text-indigo-700">Recommended next</p>
      <h3 className="mt-1 text-base font-semibold text-slate-900">
        {data.display_name}
      </h3>
      {data.description && (
        <p className="mt-1 line-clamp-2 text-sm text-slate-600">{data.description}</p>
      )}
      <div className="mt-2 flex items-center gap-3 text-xs text-slate-600">
        <span>Tier {data.difficulty_tier}</span>
        <span>·</span>
        <span>Mastery {mastery}%</span>
      </div>
      <button
        onClick={() => onPick?.(data.id)}
        className="mt-3 w-full rounded bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
      >
        View
      </button>
    </div>
  );
}
