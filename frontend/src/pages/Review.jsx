import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { api } from "../lib/api";
import { useApiGet } from "../hooks/useApi";

/**
 * Review page — the spaced-repetition return loop.
 *
 * Backend (`/review/due`) already runs the SM-2 schedule: mastery updates
 * push `next_review_at` forward on correct answers and yank it back to
 * tomorrow on incorrect ones. This page just surfaces what's currently
 * due and lets the learner start a concept-linked session for each one.
 *
 * "Start review" = create a new chat session pinned to the concept at
 * a level biased off current mastery. The actual mastery/SM-2 update
 * happens when the learner completes a quiz inside that session — we
 * don't try to short-circuit that here, because a single quiz question
 * is the minimum evidence we need for an honest rating.
 */
export default function Review() {
  const navigate = useNavigate();
  const { data, loading, error } = useApiGet("/review/due");
  const [startingId, setStartingId] = useState(null);

  const startReview = async (review) => {
    if (startingId) return;
    setStartingId(review.concept_node_id);
    try {
      const session = await api.post("/chat/create", {
        topic_name: review.concept_name,
        // Description is optional — backend will still retrieve RAG
        // content via concept_node_id, which is the stronger signal.
        topic_description: null,
        knowledge_level: suggestedLevel(review.mastery_level),
        concept_node_id: review.concept_node_id,
      });
      navigate(`/chat/${session.id}`);
    } catch (err) {
      toast.error(err.detail || "Could not start review session");
      setStartingId(null);
    }
  };

  return (
    <div className="flex h-screen flex-col bg-slate-50">
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
        <div>
          <h1 className="text-lg font-semibold text-slate-900">Review</h1>
          <p className="text-xs text-slate-500">
            Spaced repetition · concepts due based on your last quiz performance
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            to="/dashboard"
            className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100"
          >
            Dashboard
          </Link>
          <Link
            to="/chat"
            className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100"
          >
            Sessions
          </Link>
        </div>
      </header>

      <div className="flex-1 overflow-auto">
        <div className="mx-auto max-w-4xl px-6 py-6">
          {loading && <p className="text-sm text-slate-500">Checking your review queue…</p>}
          {error && (
            <p className="text-sm text-red-600">
              Couldn't load review queue: {error.detail}
            </p>
          )}

          {data && (
            <>
              <StatsStrip stats={data.stats} />

              {data.reviews.length === 0 ? (
                <EmptyState stats={data.stats} />
              ) : (
                <ul className="mt-4 flex flex-col gap-3">
                  {data.reviews.map((r) => (
                    <ReviewCard
                      key={r.concept_node_id}
                      review={r}
                      starting={startingId === r.concept_node_id}
                      onStart={() => startReview(r)}
                    />
                  ))}
                </ul>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function StatsStrip({ stats }) {
  return (
    <div className="grid grid-cols-3 gap-3">
      <Stat label="Due now" value={stats.due_now} tone={stats.due_now > 0 ? "warn" : "ok"} />
      <Stat label="Upcoming" value={stats.upcoming_reviews} />
      <Stat label="Concepts studied" value={stats.total_concepts_studied} />
    </div>
  );
}

function Stat({ label, value, tone = "ok" }) {
  const toneClasses =
    tone === "warn"
      ? "border-amber-200 bg-amber-50"
      : "border-slate-200 bg-white";
  return (
    <div className={`rounded-lg border p-3 shadow-sm ${toneClasses}`}>
      <p className="text-[10px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}

function ReviewCard({ review, starting, onStart }) {
  const mastery = Math.round((review.mastery_level ?? 0) * 100);
  const overdue = review.days_overdue > 0;

  return (
    <li className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <h3 className="truncate text-sm font-semibold text-slate-900">
            {review.concept_name}
          </h3>
          {overdue && (
            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-medium text-amber-800">
              {review.days_overdue}d overdue
            </span>
          )}
        </div>
        <div className="mt-1.5 flex items-center gap-3 text-[11px] text-slate-500">
          <span>Mastery {mastery}%</span>
          <span>·</span>
          <span>Interval {formatInterval(review.review_interval_days)}</span>
          <span>·</span>
          <span>Last reviewed {formatLastReviewed(review.last_reviewed_at)}</span>
        </div>
        <div className="mt-2 h-1 overflow-hidden rounded-full bg-slate-200">
          <div
            className="h-full bg-indigo-500 transition-all"
            style={{ width: `${Math.max(mastery, 4)}%` }}
          />
        </div>
      </div>
      <button
        onClick={onStart}
        disabled={starting}
        className="shrink-0 rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
      >
        {starting ? "Starting…" : "Start review"}
      </button>
    </li>
  );
}

function EmptyState({ stats }) {
  const studied = stats.total_concepts_studied;
  return (
    <div className="mt-6 rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center">
      <h2 className="text-base font-medium text-slate-900">
        Nothing due right now
      </h2>
      <p className="mt-1 text-sm text-slate-500">
        {studied === 0
          ? "Take a quiz in any session and concepts will appear here on their review schedule."
          : `${stats.upcoming_reviews} concept${stats.upcoming_reviews === 1 ? "" : "s"} scheduled for later. Check back after each next_review_at window.`}
      </p>
      <Link
        to="/dashboard"
        className="mt-4 inline-block rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
      >
        Back to dashboard
      </Link>
    </div>
  );
}

// ── helpers ──

function suggestedLevel(mastery) {
  const m = mastery ?? 0;
  if (m < 0.25) return "BEGINNER";
  if (m < 0.7) return "INTERMEDIATE";
  return "ADVANCED";
}

function formatInterval(days) {
  if (days == null) return "—";
  if (days < 1) return "<1 day";
  if (days < 2) return "1 day";
  return `${Math.round(days)} days`;
}

function formatLastReviewed(iso) {
  if (!iso) return "never";
  const then = new Date(iso);
  const diffMs = Date.now() - then.getTime();
  const diffDays = Math.floor(diffMs / 86400000);
  if (diffDays <= 0) return "today";
  if (diffDays === 1) return "yesterday";
  if (diffDays < 30) return `${diffDays}d ago`;
  const months = Math.floor(diffDays / 30);
  return `${months}mo ago`;
}
