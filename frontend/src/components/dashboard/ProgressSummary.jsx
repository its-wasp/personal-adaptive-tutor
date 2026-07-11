import { useApiGet } from "../../hooks/useApi";

/**
 * Compact progress panel for the dashboard, backed by /analytics/me.
 *
 * That endpoint existed from early on but nothing rendered it, so the points
 * and accuracy the quiz flow had been accumulating were invisible outside the
 * database. Sits beside RecommendedNext: what to do next on the left, how it's
 * going so far on the right.
 *
 * Errors are swallowed on purpose — this is a summary panel, and a failed
 * analytics fetch shouldn't take the concept graph down with it.
 */
export default function ProgressSummary() {
  const { data, loading } = useApiGet("/analytics/me");

  if (loading) {
    return (
      <Shell>
        <p className="mt-2 text-sm text-slate-400">Adding up your progress…</p>
      </Shell>
    );
  }

  if (!data) return null;

  const attempted = data.total_quizzes_attempted ?? 0;

  if (attempted === 0) {
    return (
      <Shell>
        <p className="mt-2 text-sm text-slate-600">
          No quizzes yet. Answer one in any session and your points, accuracy
          and topic breakdown will show up here.
        </p>
      </Shell>
    );
  }

  return (
    <Shell>
      <dl className="mt-2 grid grid-cols-3 gap-3">
        <Stat label="Points" value={data.total_points ?? 0} />
        <Stat
          label="Accuracy"
          value={`${Math.round(data.overall_accuracy_percentage ?? 0)}%`}
          tone={accuracyTone(data.overall_accuracy_percentage)}
        />
        <Stat label="Quizzes" value={`${data.total_quizzes_correct ?? 0}/${attempted}`} />
      </dl>
      {data.topics?.length > 0 && (
        <p className="mt-2.5 truncate text-[11px] text-slate-500">
          Across {data.total_topics} topic{data.total_topics === 1 ? "" : "s"} ·
          strongest: {strongestTopic(data.topics)}
        </p>
      )}
    </Shell>
  );
}

function Shell({ children }) {
  return (
    <div className="h-full rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs uppercase tracking-wide text-slate-500">Your progress</p>
      {children}
    </div>
  );
}

function Stat({ label, value, tone }) {
  return (
    <div>
      <dd className={`text-xl font-semibold ${tone || "text-slate-900"}`}>{value}</dd>
      <dt className="text-[10px] uppercase tracking-wide text-slate-500">{label}</dt>
    </div>
  );
}

function accuracyTone(pct) {
  if (pct == null) return "text-slate-900";
  if (pct >= 75) return "text-emerald-600";
  if (pct >= 50) return "text-amber-600";
  return "text-rose-600";
}

function strongestTopic(topics) {
  // Only topics with an actual attempt behind them can claim to be strongest.
  const scored = topics.filter((t) => t.quizzes_attempted > 0);
  if (scored.length === 0) return "—";
  return scored.reduce((best, t) =>
    t.accuracy_percentage > best.accuracy_percentage ? t : best
  ).topic_name;
}
