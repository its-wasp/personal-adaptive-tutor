import { useMemo } from "react";

/**
 * Tiered card grid of DSA concepts — the dashboard's primary view.
 *
 * Concepts are grouped into horizontal rows by difficulty_tier (1 → 5),
 * reading top-to-bottom as a learning path. Each tier row is its own
 * responsive grid so cards within a tier align cleanly and share a
 * common height (auto-rows-fr) regardless of description length.
 * Every card is a real button (big click target, full keyboard
 * accessibility) and surfaces:
 *   - display name + short description
 *   - mastery bar (color-matched to the mastery scale)
 *   - prereq chips (names of parent concepts)
 *   - lock state when any prereq is below 0.6 mastery
 *
 * We replaced the force-directed graph with this after click-targeting
 * and layout non-determinism turned out to be a worse UX than a clean,
 * scannable grid. Prereq relationships stay visible via the chips
 * instead of drawn edges, which is both simpler to implement and
 * arguably more legible.
 */
export default function ConceptGrid({ graph, selectedId, onSelect }) {
  const { tiers, lockedIds, prereqNamesById } = useMemo(() => {
    const byTier = new Map();
    const nameById = new Map();
    const masteryById = new Map();
    for (const n of graph.nodes) {
      nameById.set(n.id, n.display_name);
      masteryById.set(n.id, n.mastery_level ?? 0);
      if (!byTier.has(n.difficulty_tier)) byTier.set(n.difficulty_tier, []);
      byTier.get(n.difficulty_tier).push(n);
    }

    const prereqIdsBy = new Map(); // node id -> [prereq node ids]
    for (const e of graph.edges) {
      if (e.relation_type !== "PREREQUISITE") continue;
      if (!prereqIdsBy.has(e.to_node_id)) prereqIdsBy.set(e.to_node_id, []);
      prereqIdsBy.get(e.to_node_id).push(e.from_node_id);
    }

    const locked = new Set();
    const prereqNames = new Map();
    for (const n of graph.nodes) {
      const reqs = prereqIdsBy.get(n.id) || [];
      prereqNames.set(
        n.id,
        reqs.map((id) => nameById.get(id)).filter(Boolean)
      );
      if (reqs.length && !reqs.every((id) => (masteryById.get(id) ?? 0) >= 0.6)) {
        locked.add(n.id);
      }
    }

    const tierList = [...byTier.entries()]
      .sort(([a], [b]) => a - b)
      .map(([tier, nodes]) => ({
        tier,
        nodes: nodes.sort((a, b) => a.display_name.localeCompare(b.display_name)),
      }));

    return { tiers: tierList, lockedIds: locked, prereqNamesById: prereqNames };
  }, [graph]);

  return (
    <div className="h-full overflow-auto p-6">
      <div className="mx-auto flex max-w-7xl flex-col gap-8">
        {tiers.map(({ tier, nodes }) => (
          <section key={tier}>
            <header className="mb-3 flex items-baseline gap-2 border-b border-slate-200 pb-1.5">
              <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {tierLabel(tier)}
              </h2>
              <p className="text-[10px] text-slate-400">
                · {nodes.length} concept{nodes.length === 1 ? "" : "s"}
              </p>
            </header>
            {/* auto-rows-fr equalizes card heights within each tier row so
                variable description / prereq counts don't break alignment. */}
            <div className="grid auto-rows-fr grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {nodes.map((n) => (
                <ConceptCard
                  key={n.id}
                  node={n}
                  locked={lockedIds.has(n.id)}
                  selected={n.id === selectedId}
                  prereqNames={prereqNamesById.get(n.id) || []}
                  onClick={() => onSelect(n.id)}
                />
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}

function ConceptCard({ node, locked, selected, prereqNames, onClick }) {
  const mastery = Math.round((node.mastery_level ?? 0) * 100);
  const barColor = masteryBarColor(node.mastery_level ?? 0);

  return (
    <button
      onClick={onClick}
      className={`group relative flex flex-col gap-2 rounded-lg border bg-white p-3 text-left shadow-sm transition ${
        selected
          ? "border-indigo-500 ring-2 ring-indigo-200"
          : "border-slate-200 hover:border-slate-300 hover:shadow"
      } ${locked ? "opacity-70" : ""}`}
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-900">{node.display_name}</h3>
        {locked && (
          <span title="Prerequisites not yet met" className="text-slate-400">
            {/* lock glyph */}
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
          </span>
        )}
      </div>

      {node.description && (
        <p className="line-clamp-2 text-xs text-slate-600">{node.description}</p>
      )}

      <div>
        <div className="flex items-center justify-between text-[10px] text-slate-500">
          <span>Mastery</span>
          <span className="font-medium text-slate-600">{mastery}%</span>
        </div>
        <div className="mt-0.5 h-1 overflow-hidden rounded-full bg-slate-200">
          <div
            className="h-full transition-all"
            style={{ width: `${Math.max(mastery, node.mastery_level > 0 ? 4 : 0)}%`, backgroundColor: barColor }}
          />
        </div>
      </div>

      {prereqNames.length > 0 && (
        <div className="flex flex-wrap gap-1 pt-0.5">
          <span className="text-[10px] text-slate-400">Needs:</span>
          {prereqNames.map((name) => (
            <span
              key={name}
              className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-600"
            >
              {name}
            </span>
          ))}
        </div>
      )}
    </button>
  );
}

function masteryBarColor(m) {
  if (m <= 0) return "#cbd5e1";
  if (m < 0.4) return "#f87171";
  if (m < 0.75) return "#fbbf24";
  return "#22c55e";
}

function tierLabel(tier) {
  // Human-readable names tied to the DSA seed's tier spread. If the seed
  // gains a 6th tier this will still render sensibly via the fallback.
  const map = {
    1: "Tier 1 · Foundations",
    2: "Tier 2 · Core",
    3: "Tier 3 · Intermediate",
    4: "Tier 4 · Advanced",
    5: "Tier 5 · Expert",
  };
  return map[tier] || `Tier ${tier}`;
}
