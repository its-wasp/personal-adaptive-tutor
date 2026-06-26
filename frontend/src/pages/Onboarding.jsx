import { useEffect, useMemo, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { api } from "../lib/api";
import { useAuth } from "../hooks/useAuth";

/**
 * Three-step onboarding:
 *   1. Preferences — how the learner likes to be taught
 *   2. Placement  — 10 MCQs that seed initial mastery
 *   3. Results    — score + assessed level, then into /dashboard
 *
 * The backend marks `onboarding_completed = true` inside submit_placement,
 * so we call refreshProfile() before navigating to the dashboard — otherwise
 * the dashboard would bounce the user right back here.
 */

const STEP_PREFERENCES = "preferences";
const STEP_PLACEMENT = "placement";
const STEP_RESULTS = "results";

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

export default function Onboarding() {
  const { profile, loading, refreshProfile } = useAuth();
  const navigate = useNavigate();

  const [step, setStep] = useState(STEP_PREFERENCES);
  const [prefs, setPrefs] = useState({
    learning_style: "VISUAL",
    pace_preference: "MODERATE",
    explanation_detail_level: "STANDARD",
    use_analogies: true,
  });
  const [savingPrefs, setSavingPrefs] = useState(false);

  const [questions, setQuestions] = useState([]);
  const [loadingQuiz, setLoadingQuiz] = useState(false);
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState({}); // index -> "A"|"B"|"C"|"D"
  const [submittingPlacement, setSubmittingPlacement] = useState(false);

  const [results, setResults] = useState(null);

  // If the user already finished onboarding, don't let them re-run it.
  //
  // Evaluated here but applied at the bottom of the component: returning
  // early from this position skipped the useEffect and useMemo declared
  // further down, so the render after `profile` arrived called fewer hooks
  // than the one before it and React threw.
  const alreadyOnboarded =
    !loading && profile?.onboarding_completed && step !== STEP_RESULTS;

  async function handleSubmitPrefs(e) {
    e.preventDefault();
    setSavingPrefs(true);
    try {
      await api.post("/onboarding/preferences", prefs);
      setStep(STEP_PLACEMENT);
    } catch (err) {
      toast.error(err.detail || "Could not save preferences");
    } finally {
      setSavingPrefs(false);
    }
  }

  // Lazily load the placement questions when we enter that step.
  useEffect(() => {
    if (step !== STEP_PLACEMENT || questions.length > 0) return;
    let cancelled = false;
    setLoadingQuiz(true);
    api
      .get("/onboarding/placement")
      .then((data) => {
        if (!cancelled) setQuestions(data.questions || []);
      })
      .catch((err) => {
        if (!cancelled) toast.error(err.detail || "Could not load placement quiz");
      })
      .finally(() => {
        if (!cancelled) setLoadingQuiz(false);
      });
    return () => {
      cancelled = true;
    };
  }, [step, questions.length]);

  function selectAnswer(questionIndex, option) {
    setAnswers((prev) => ({ ...prev, [questionIndex]: option }));
  }

  async function handleSubmitPlacement() {
    const payload = {
      answers: questions.map((q) => ({
        question_index: q.index,
        // Default unanswered to "A" — backend just grades what it gets.
        selected_option: answers[q.index] || "A",
      })),
    };
    setSubmittingPlacement(true);
    try {
      const data = await api.post("/onboarding/placement/submit", payload);
      setResults(data);
      // Refresh profile so onboarding_completed flips to true in context
      // before we navigate — prevents a redirect back to /onboarding.
      await refreshProfile();
      setStep(STEP_RESULTS);
    } catch (err) {
      toast.error(err.detail || "Could not submit placement");
    } finally {
      setSubmittingPlacement(false);
    }
  }

  const answeredCount = useMemo(
    () => Object.keys(answers).length,
    [answers]
  );

  // Safe here: every hook above has already run.
  if (alreadyOnboarded) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="mx-auto min-h-full max-w-2xl p-6">
      <Header step={step} />

      {step === STEP_PREFERENCES && (
        <PreferencesStep
          prefs={prefs}
          setPrefs={setPrefs}
          submitting={savingPrefs}
          onSubmit={handleSubmitPrefs}
        />
      )}

      {step === STEP_PLACEMENT && (
        <PlacementStep
          loading={loadingQuiz}
          questions={questions}
          currentQ={currentQ}
          setCurrentQ={setCurrentQ}
          answers={answers}
          onAnswer={selectAnswer}
          answeredCount={answeredCount}
          submitting={submittingPlacement}
          onSubmit={handleSubmitPlacement}
        />
      )}

      {step === STEP_RESULTS && results && (
        <ResultsStep results={results} onContinue={() => navigate("/dashboard", { replace: true })} />
      )}
    </div>
  );
}

function Header({ step }) {
  const steps = [
    { id: STEP_PREFERENCES, label: "Preferences" },
    { id: STEP_PLACEMENT, label: "Placement" },
    { id: STEP_RESULTS, label: "Results" },
  ];
  const currentIdx = steps.findIndex((s) => s.id === step);

  return (
    <div className="mb-8">
      <h1 className="text-2xl font-semibold">Let's personalize your tutor</h1>
      <p className="mt-1 text-sm text-slate-600">
        A couple of quick questions so explanations feel like they were written for you.
      </p>
      <div className="mt-5 flex items-center gap-2">
        {steps.map((s, i) => (
          <div key={s.id} className="flex flex-1 items-center gap-2">
            <div
              className={
                "flex h-7 w-7 items-center justify-center rounded-full text-xs font-medium " +
                (i <= currentIdx
                  ? "bg-indigo-600 text-white"
                  : "bg-slate-200 text-slate-500")
              }
            >
              {i + 1}
            </div>
            <span
              className={
                "text-sm " +
                (i <= currentIdx ? "text-slate-800" : "text-slate-400")
              }
            >
              {s.label}
            </span>
            {i < steps.length - 1 && (
              <div className="ml-1 h-px flex-1 bg-slate-200" />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function PreferencesStep({ prefs, setPrefs, submitting, onSubmit }) {
  function set(field, value) {
    setPrefs((p) => ({ ...p, [field]: value }));
  }

  return (
    <form onSubmit={onSubmit} className="space-y-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <RadioGroup
        label="How do you like to learn?"
        name="learning_style"
        options={LEARNING_STYLES}
        value={prefs.learning_style}
        onChange={(v) => set("learning_style", v)}
      />

      <RadioGroup
        label="What pace works for you?"
        name="pace_preference"
        options={PACE_OPTIONS}
        value={prefs.pace_preference}
        onChange={(v) => set("pace_preference", v)}
      />

      <div>
        <p className="mb-2 text-sm font-medium text-slate-700">How detailed should explanations be?</p>
        <div className="flex gap-2">
          {DETAIL_OPTIONS.map((o) => (
            <button
              type="button"
              key={o.value}
              onClick={() => set("explanation_detail_level", o.value)}
              className={
                "flex-1 rounded border px-3 py-2 text-sm " +
                (prefs.explanation_detail_level === o.value
                  ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                  : "border-slate-300 text-slate-700 hover:bg-slate-50")
              }
            >
              {o.label}
            </button>
          ))}
        </div>
      </div>

      <label className="flex items-center gap-3 text-sm text-slate-700">
        <input
          type="checkbox"
          checked={prefs.use_analogies}
          onChange={(e) => set("use_analogies", e.target.checked)}
          className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
        />
        Use analogies from everyday life where they help
      </label>

      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded bg-indigo-600 py-2 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
      >
        {submitting ? "Saving…" : "Continue to placement quiz"}
      </button>
    </form>
  );
}

function RadioGroup({ label, name, options, value, onChange }) {
  return (
    <div>
      <p className="mb-2 text-sm font-medium text-slate-700">{label}</p>
      <div className="grid gap-2 sm:grid-cols-2">
        {options.map((o) => (
          <label
            key={o.value}
            className={
              "cursor-pointer rounded border px-3 py-2 text-sm " +
              (value === o.value
                ? "border-indigo-500 bg-indigo-50"
                : "border-slate-300 hover:bg-slate-50")
            }
          >
            <input
              type="radio"
              name={name}
              value={o.value}
              checked={value === o.value}
              onChange={() => onChange(o.value)}
              className="sr-only"
            />
            <span className="block font-medium text-slate-800">{o.label}</span>
            {o.hint && <span className="block text-xs text-slate-500">{o.hint}</span>}
          </label>
        ))}
      </div>
    </div>
  );
}

function PlacementStep({
  loading,
  questions,
  currentQ,
  setCurrentQ,
  answers,
  onAnswer,
  answeredCount,
  submitting,
  onSubmit,
}) {
  if (loading) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-6 text-center text-slate-500 shadow-sm">
        Loading placement quiz…
      </div>
    );
  }

  if (questions.length === 0) return null;

  const q = questions[currentQ];
  const selected = answers[q.index];
  const isLast = currentQ === questions.length - 1;

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between text-xs text-slate-500">
        <span>
          Question {currentQ + 1} of {questions.length}
        </span>
        <span>Tier {q.tier}</span>
      </div>

      <h2 className="text-lg font-medium text-slate-900">{q.question}</h2>

      <div className="mt-4 space-y-2">
        {Object.entries(q.options).map(([letter, text]) => {
          const isSelected = selected === letter;
          return (
            <button
              type="button"
              key={letter}
              onClick={() => onAnswer(q.index, letter)}
              className={
                "w-full rounded border px-3 py-2 text-left text-sm transition " +
                (isSelected
                  ? "border-indigo-500 bg-indigo-50"
                  : "border-slate-300 hover:bg-slate-50")
              }
            >
              <span className="mr-2 font-semibold text-slate-700">{letter}.</span>
              {text}
            </button>
          );
        })}
      </div>

      <div className="mt-6 flex items-center justify-between">
        <button
          type="button"
          disabled={currentQ === 0}
          onClick={() => setCurrentQ((i) => Math.max(0, i - 1))}
          className="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-40"
        >
          Back
        </button>

        <span className="text-xs text-slate-500">
          {answeredCount} / {questions.length} answered
        </span>

        {!isLast ? (
          <button
            type="button"
            disabled={!selected}
            onClick={() => setCurrentQ((i) => Math.min(questions.length - 1, i + 1))}
            className="rounded bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-40"
          >
            Next
          </button>
        ) : (
          <button
            type="button"
            disabled={submitting || answeredCount < questions.length}
            onClick={onSubmit}
            className="rounded bg-indigo-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-40"
          >
            {submitting ? "Submitting…" : "Submit"}
          </button>
        )}
      </div>
    </div>
  );
}

function ResultsStep({ results, onContinue }) {
  const { correct_answers, total_questions, score_percentage, assessed_level } = results;

  const levelStyles = {
    BEGINNER: "bg-amber-50 text-amber-700 border-amber-200",
    INTERMEDIATE: "bg-sky-50 text-sky-700 border-sky-200",
    ADVANCED: "bg-emerald-50 text-emerald-700 border-emerald-200",
  };

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-xl font-semibold">You're all set!</h2>
      <p className="mt-1 text-sm text-slate-600">
        Here's a quick snapshot. We'll keep refining this as you learn.
      </p>

      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <div className="rounded border border-slate-200 p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Score</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">
            {correct_answers} / {total_questions}
          </p>
          <p className="text-sm text-slate-500">{score_percentage}%</p>
        </div>
        <div className={"rounded border p-4 " + (levelStyles[assessed_level] || "border-slate-200")}>
          <p className="text-xs uppercase tracking-wide opacity-70">Starting level</p>
          <p className="mt-1 text-2xl font-semibold">{assessed_level}</p>
          <p className="text-sm opacity-80">Your knowledge graph is primed with this as the baseline.</p>
        </div>
      </div>

      <button
        onClick={onContinue}
        className="mt-6 w-full rounded bg-indigo-600 py-2 font-medium text-white hover:bg-indigo-700"
      >
        Go to dashboard
      </button>
    </div>
  );
}
