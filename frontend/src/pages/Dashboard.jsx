import { useCallback, useMemo } from "react";
import { Link, Navigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useApiGet } from "../hooks/useApi";
import ConceptGrid from "../components/graph/ConceptGrid";
import ConceptDetail from "../components/graph/ConceptDetail";
import RecommendedNext from "../components/dashboard/RecommendedNext";

/**
 * Dashboard — tiered card grid of DSA concepts.
 *
 * We tried a force-directed graph here first. Looked cool, but in practice
 * nodes overlap, hit areas are tiny, and the layout shuffles on every
 * visit. The grid is deterministic, every card is a big click target,
 * and the tier columns double as a learning path.
 *
 * Selection lives in the URL (?concept=<uuid>) so navigating away and
 * back restores your place — previously the detail panel silently
 * disappeared on every dashboard revisit.
 */
export default function Dashboard() {
  const { user, profile, logout } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedId = searchParams.get("concept");

  // Skip graph fetch until we know onboarding is done.
  const needsOnboarding = profile && !profile.onboarding_completed;
  const { data: graph, loading, error } = useApiGet("/graph/dsa", {
    skip: needsOnboarding,
  });
  // Light-touch fetch for the review badge — skipped until onboarding is
  // done to match the graph call. Errors are swallowed: the badge is a
  // nice-to-have and shouldn't break the dashboard.
  const { data: reviewData } = useApiGet("/review/due", {
    skip: needsOnboarding,
  });
  const dueCount = reviewData?.stats?.due_now ?? 0;

  const setSelectedId = useCallback(
    (id) => {
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          if (id) next.set("concept", id);
          else next.delete("concept");
          return next;
        },
        { replace: true }
      );
    },
    [setSearchParams]
  );

  const lockedIds = useMemo(() => {
    if (!graph) return new Set();
    const masteryById = new Map(graph.nodes.map((n) => [n.id, n.mastery_level ?? 0]));
    const prereqsBy = new Map();
    for (const e of graph.edges) {
      if (e.relation_type !== "PREREQUISITE") continue;
      if (!prereqsBy.has(e.to_node_id)) prereqsBy.set(e.to_node_id, []);
      prereqsBy.get(e.to_node_id).push(e.from_node_id);
    }
    const locked = new Set();
    for (const n of graph.nodes) {
      const reqs = prereqsBy.get(n.id) || [];
      if (reqs.length && !reqs.every((id) => (masteryById.get(id) ?? 0) >= 0.6)) {
        locked.add(n.id);
      }
    }
    return locked;
  }, [graph]);

  const selected = useMemo(
    () => graph?.nodes.find((n) => n.id === selectedId) || null,
    [graph, selectedId]
  );

  if (needsOnboarding) {
    return <Navigate to="/onboarding" replace />;
  }

  return (
    <div className="flex h-screen flex-col bg-slate-50">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
        <div>
          <h1 className="text-lg font-semibold text-slate-900">
            {user?.name ? `Hi, ${user.name.split(" ")[0]}` : "Dashboard"}
          </h1>
          <p className="text-xs text-slate-500">
            Data Structures & Algorithms · pick a concept to start a session
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            to="/review"
            className={`relative rounded border px-3 py-1.5 text-sm font-medium ${
              dueCount > 0
                ? "border-amber-300 bg-amber-50 text-amber-800 hover:bg-amber-100"
                : "border-slate-300 bg-white text-slate-700 hover:bg-slate-100"
            }`}
          >
            Review
            {dueCount > 0 && (
              <span className="ml-1.5 inline-flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-amber-600 px-1 text-[10px] font-semibold text-white">
                {dueCount}
              </span>
            )}
          </Link>
          <Link
            to="/chat"
            className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100"
          >
            Sessions
          </Link>
          <button
            onClick={logout}
            className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100"
          >
            Log out
          </button>
        </div>
      </header>

      {/* Recommendation strip */}
      <div className="border-b border-slate-200 bg-slate-50 px-6 py-3">
        <div className="mx-auto max-w-5xl">
          <RecommendedNext subject="dsa" onPick={setSelectedId} />
        </div>
      </div>

      {/* Concept grid + detail panel */}
      <div className="flex flex-1 overflow-hidden">
        <div className="min-w-0 flex-1 overflow-auto">
          {loading && (
            <div className="flex h-full items-center justify-center text-sm text-slate-500">
              Loading concepts…
            </div>
          )}
          {error && (
            <div className="flex h-full items-center justify-center text-sm text-red-600">
              Couldn't load concepts: {error.detail}
            </div>
          )}
          {!loading && !error && graph && (
            <ConceptGrid
              graph={graph}
              selectedId={selectedId}
              onSelect={setSelectedId}
            />
          )}
        </div>

        {selected && (
          <div className="w-[340px] shrink-0">
            <ConceptDetail
              concept={selected}
              locked={lockedIds.has(selected.id)}
              onClose={() => setSelectedId(null)}
            />
          </div>
        )}
      </div>
    </div>
  );
}
