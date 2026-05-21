import { useState } from "react";
import toast from "react-hot-toast";
import { useNavigate } from "react-router-dom";
import { api } from "../../lib/api";

/**
 * Side panel shown when a concept node is selected on the graph.
 *
 * Owns its own "start session" flow: builds a ChatCreateDTO from the
 * concept + user mastery, calls /chat/create, and navigates on success.
 * Keeping this local (instead of hoisting to Dashboard) means the panel
 * can be reused from anywhere that has a concept + user.
 *
 * Level selection: we bias the level off mastery — low mastery → BEGINNER,
 * mid → INTERMEDIATE, high → ADVANCED — but let the learner override. The
 * backend will personalise further via learner profile + RAG.
 */
export default function ConceptDetail({ concept, locked, onClose }) {
  const navigate = useNavigate();
  const [level, setLevel] = useState(() => suggestedLevel(concept.mastery_level));
  const [creating, setCreating] = useState(false);

  const handleStart = async () => {
    if (creating) return;
    setCreating(true);
    try {
      const session = await api.post("/chat/create", {
        topic_name: concept.display_name,
        topic_description: concept.description || null,
        knowledge_level: level,
        concept_node_id: concept.id,
      });
      navigate(`/chat/${session.id}`);
    } catch (err) {
      toast.error(err.detail || "Could not start session");
    } finally {
      setCreating(false);
    }
  };

  const mastery = Math.round((concept.mastery_level ?? 0) * 100);

  return (
    <aside className="flex h-full w-full flex-col gap-4 overflow-y-auto border-l border-slate-200 bg-white p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">
            {concept.display_name}
          </h2>
          <p className="text-xs uppercase tracking-wide text-slate-500">
            Tier {concept.difficulty_tier} · {concept.estimated_minutes || "—"} min
          </p>
        </div>
        <button
          onClick={onClose}
          className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
          aria-label="Close"
        >
          ×
        </button>
      </div>

      {concept.description && (
        <p className="text-sm leading-relaxed text-slate-600">
          {concept.description}
        </p>
      )}

      <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span>Mastery</span>
          <span className="font-medium text-slate-700">{mastery}%</span>
        </div>
        <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-slate-200">
          <div
            className="h-full bg-indigo-500 transition-all"
            style={{ width: `${mastery}%` }}
          />
        </div>
        {locked && (
          <p className="mt-2 text-xs text-amber-700">
            Prerequisites not yet met — you can still start a session, but the
            tutor will assume foundational gaps.
          </p>
        )}
      </div>

      {concept.tags?.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {concept.tags.map((t) => (
            <span
              key={t}
              className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600"
            >
              {t}
            </span>
          ))}
        </div>
      )}

      <div>
        <p className="mb-1.5 text-xs font-medium text-slate-500">Start at level</p>
        <div className="grid grid-cols-3 gap-1.5">
          {["BEGINNER", "INTERMEDIATE", "ADVANCED"].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setLevel(lvl)}
              className={`rounded border px-2 py-1.5 text-xs font-medium transition ${
                level === lvl
                  ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                  : "border-slate-200 text-slate-600 hover:border-slate-300"
              }`}
            >
              {lvl[0] + lvl.slice(1).toLowerCase()}
            </button>
          ))}
        </div>
      </div>

      <button
        onClick={handleStart}
        disabled={creating}
        className="mt-auto rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
      >
        {creating ? "Starting session…" : "Start session"}
      </button>
    </aside>
  );
}

function suggestedLevel(mastery) {
  const m = mastery ?? 0;
  if (m < 0.25) return "BEGINNER";
  if (m < 0.7) return "INTERMEDIATE";
  return "ADVANCED";
}
