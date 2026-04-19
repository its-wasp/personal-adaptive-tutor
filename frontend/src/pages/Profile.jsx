import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import toast from "react-hot-toast";
import { api } from "../lib/api";
import { useApiGet } from "../hooks/useApi";
import MarkdownRenderer from "../components/shared/MarkdownRenderer";

/**
 * Profile page — view and edit learner preferences.
 *
 * This page makes the personalization engine legible: users can see their
 * current settings, the evolving learner summary the tutor has built, and
 * their mastery strengths/weaknesses. Editing preferences is the "U" in
 * CRUD and the main post-onboarding control surface for personalization.
 */

const LEARNING_STYLES = [
  { value: "VISUAL", label: "Visual", hint: "Diagrams, trees, step-by-step pictures" },
  { value: "READING", label: "Reading", hint: "Clear written explanations" },
  { value: "EXAMPLE_FIRST", label: "Example-first", hint: "Show me code, then explain" },
  { value: "THEORY_FIRST", label: "Theory-first", hint: "Explain the idea, then show code" },
];

const PACE_OPTIONS = [
  { value: "QUICK", label: "Quick", hint: "Give me the essentials" },
  { value: "MODERATE", label: "Moderate", hint: "Balanced depth" },
  { value: "DETAILED", label: "Detailed", hint: "Walk me through everything" },
];

const DETAIL_OPTIONS = [
  { value: "CONCISE", label: "Concise" },
  { value: "STANDARD", label: "Standard" },
  { value: "VERBOSE", label: "Verbose" },
];

const CODE_COMPLEXITY = [
  { value: "SIMPLE", label: "Simple", hint: "Beginner-friendly with comments" },
  { value: "MODERATE", label: "Moderate", hint: "Clean, idiomatic code" },
  { value: "ADVANCED", label: "Advanced", hint: "Production-quality patterns" },
];

export default function Profile() {
  const { data: profile, loading, error, refetch } = useApiGet("/profile/me");

  const [prefs, setPrefs] = useState(null);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);

  // Seed the form once profile loads.
  useEffect(() => {
    if (profile && !prefs) {
      setPrefs({
        learning_style: profile.learning_style || "VISUAL",
        pace_preference: profile.pace_preference || "MODERATE",
        explanation_detail_level: profile.explanation_detail_level || "STANDARD",
        preferred_code_complexity: profile.preferred_code_complexity || "SIMPLE",
        analogy_preference: profile.use_analogies ?? true,
      });
    }
  }, [profile, prefs]);

  function updatePref(key, value) {
    setPrefs((p) => ({ ...p, [key]: value }));
    setDirty(true);
  }

  async function handleSave() {
    if (!dirty || saving) return;
    setSaving(true);
    try {
      await api.put("/profile/me/preferences", prefs);
      toast.success("Preferences saved");
      setDirty(false);
      refetch();
    } catch (err) {
      toast.error(err.detail || "Could not save preferences");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex h-screen flex-col bg-slate-50">
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
        <div>
          <h1 className="text-lg font-semibold text-slate-900">Profile</h1>
          <p className="text-xs text-slate-500">
            Your learning preferences and tutor memory
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
        <div className="mx-auto max-w-3xl px-6 py-6">
          {loading && <p className="text-sm text-slate-500">Loading profile…</p>}
          {error && (
            <p className="text-sm text-red-600">
              Couldn't load profile: {error.detail}
            </p>
          )}

          {profile && prefs && (
            <div className="flex flex-col gap-6">
              {/* Stats strip */}
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <StatCard label="Sessions" value={profile.total_sessions} />
                <StatCard label="Streak" value={`${profile.streak_days}d`} />
                <StatCard label="Strengths" value={profile.strengths?.length ?? 0} />
                <StatCard label="Weak areas" value={profile.weaknesses?.length ?? 0} />
              </div>

              {/* Mastery highlights */}
              {(profile.strengths?.length > 0 || profile.weaknesses?.length > 0) && (
                <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                  <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Mastery highlights
                  </h2>
                  {profile.strengths?.length > 0 && (
                    <div className="mb-2">
                      <span className="text-xs font-medium text-emerald-700">Strong in: </span>
                      {profile.strengths.map((s) => (
                        <span key={s} className="mr-1.5 rounded bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700">
                          {s}
                        </span>
                      ))}
                    </div>
                  )}
                  {profile.weaknesses?.length > 0 && (
                    <div>
                      <span className="text-xs font-medium text-amber-700">Needs work: </span>
                      {profile.weaknesses.map((w) => (
                        <span key={w} className="mr-1.5 rounded bg-amber-50 px-2 py-0.5 text-xs text-amber-700">
                          {w}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Learner summary — what the tutor "knows" */}
              {profile.learner_summary && (
                <div className="rounded-lg border border-indigo-200 bg-indigo-50/60 p-4 shadow-sm">
                  <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-indigo-700">
                    What the tutor knows about you
                  </h2>
                  <div className="text-sm text-slate-700">
                    <MarkdownRenderer>{profile.learner_summary}</MarkdownRenderer>
                  </div>
                  <p className="mt-2 text-[10px] text-slate-400">
                    This summary evolves automatically as you study. It shapes every response the tutor gives you.
                  </p>
                </div>
              )}

              {/* Preferences form */}
              <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                <h2 className="mb-4 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Learning preferences
                </h2>

                <div className="flex flex-col gap-5">
                  <OptionGroup
                    label="Learning style"
                    options={LEARNING_STYLES}
                    value={prefs.learning_style}
                    onChange={(v) => updatePref("learning_style", v)}
                  />

                  <OptionGroup
                    label="Pace"
                    options={PACE_OPTIONS}
                    value={prefs.pace_preference}
                    onChange={(v) => updatePref("pace_preference", v)}
                  />

                  <OptionGroup
                    label="Explanation detail"
                    options={DETAIL_OPTIONS}
                    value={prefs.explanation_detail_level}
                    onChange={(v) => updatePref("explanation_detail_level", v)}
                  />

                  <OptionGroup
                    label="Code complexity"
                    options={CODE_COMPLEXITY}
                    value={prefs.preferred_code_complexity}
                    onChange={(v) => updatePref("preferred_code_complexity", v)}
                  />

                  <div>
                    <p className="mb-1.5 text-xs font-medium text-slate-600">Analogies</p>
                    <label className="inline-flex cursor-pointer items-center gap-2 text-sm text-slate-700">
                      <input
                        type="checkbox"
                        checked={prefs.analogy_preference}
                        onChange={(e) => updatePref("analogy_preference", e.target.checked)}
                        className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                      />
                      Include real-world analogies in explanations
                    </label>
                  </div>
                </div>

                <div className="mt-5 flex items-center gap-3">
                  <button
                    onClick={handleSave}
                    disabled={!dirty || saving}
                    className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-40"
                  >
                    {saving ? "Saving…" : "Save preferences"}
                  </button>
                  {dirty && (
                    <span className="text-xs text-slate-400">Unsaved changes</span>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
      <p className="text-[10px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}

function OptionGroup({ label, options, value, onChange }) {
  return (
    <div>
      <p className="mb-1.5 text-xs font-medium text-slate-600">{label}</p>
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            title={opt.hint}
            className={`rounded border px-3 py-1.5 text-xs font-medium transition ${
              value === opt.value
                ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                : "border-slate-200 text-slate-600 hover:border-slate-300"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}
