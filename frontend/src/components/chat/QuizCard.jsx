import { useState } from "react";
import toast from "react-hot-toast";
import { api } from "../../lib/api";
import MarkdownRenderer from "../shared/MarkdownRenderer";

/**
 * Inline quiz — renders 4 options, lets the user pick one, submits on click,
 * then shows the result (correct/wrong + explanation + hint).
 *
 * After submission the correct option is always highlighted green and a wrong
 * pick is highlighted red. The correct_option is only known client-side after
 * submit (the server withholds it until then to prevent peeking).
 *
 * `quizData` matches what the /chat/{id}/conversation endpoint returns
 * when a message is a QUIZ type. It may already contain a prior attempt
 * (selected_option, is_correct, points_awarded) — if so, we render in
 * the completed state directly so the user sees their past answer when
 * they reopen a session.
 */
export default function QuizCard({ messageId, quizId, quizData, onSubmitted, onNextQuestion }) {
  const alreadyAnswered = quizData?.selected_option != null;

  const [selected, setSelected] = useState(quizData?.selected_option || null);
  const [submitted, setSubmitted] = useState(alreadyAnswered);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(
    alreadyAnswered
      ? {
          correct: quizData.is_correct,
          correct_option: quizData.correct_option,
          points_awarded: quizData.points_awarded,
          explanation: quizData.explanation,
          hint: quizData.is_correct ? null : quizData.hint,
        }
      : null
  );

  // After submit, result.correct_option is the authoritative source.
  // Before submit (reloaded from conversation), quizData.correct_option works.
  const correctOption = result?.correct_option ?? quizData?.correct_option;

  async function handleSubmit() {
    if (!selected || submitting || submitted) return;
    setSubmitting(true);
    try {
      const res = await api.post("/quiz/submit", {
        quiz_id: quizId,
        selected_option: selected,
      });
      setResult(res);
      setSubmitted(true);
      onSubmitted?.(res);
    } catch (err) {
      toast.error(err.detail || "Could not submit answer");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="rounded-lg border border-indigo-200 bg-indigo-50/50 p-4">
      <div className="mb-2 flex items-center gap-2">
        <span className="rounded bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-700">
          Quiz
        </span>
        {quizData?.difficulty && (
          <span className="text-xs text-slate-500">{quizData.difficulty}</span>
        )}
        {quizData?.points != null && (
          <span className="text-xs text-slate-500">· {quizData.points} pts</span>
        )}
      </div>

      <p className="mb-3 font-medium text-slate-900">{quizData?.question}</p>

      <div className="space-y-2">
        {quizData?.options &&
          Object.entries(quizData.options).map(([letter, text]) => {
            const isSelected = selected === letter;
            const isCorrect = submitted && correctOption === letter;
            const isWrongPick = submitted && isSelected && !result?.correct;

            const base = "w-full rounded border px-3 py-2 text-left text-sm transition ";
            let state = "border-slate-300 hover:bg-white";
            if (submitted) {
              if (isCorrect) state = "border-emerald-400 bg-emerald-50 text-emerald-900";
              else if (isWrongPick) state = "border-rose-400 bg-rose-50 text-rose-900";
              else state = "border-slate-200 text-slate-600";
            } else if (isSelected) {
              state = "border-indigo-500 bg-white";
            }

            return (
              <button
                type="button"
                key={letter}
                disabled={submitted || submitting}
                onClick={() => setSelected(letter)}
                className={base + state}
              >
                <span className="mr-2 font-semibold">{letter}.</span>
                {text}
              </button>
            );
          })}
      </div>

      {!submitted && (
        <div className="mt-3 flex justify-end">
          <button
            type="button"
            disabled={!selected || submitting}
            onClick={handleSubmit}
            className="rounded bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-40"
          >
            {submitting ? "Submitting…" : "Submit answer"}
          </button>
        </div>
      )}

      {submitted && result && (
        <div
          className={
            "mt-3 rounded border p-3 text-sm " +
            (result.correct
              ? "border-emerald-200 bg-emerald-50 text-emerald-800"
              : "border-rose-200 bg-rose-50 text-rose-800")
          }
        >
          <p className="font-medium">
            {result.correct ? "Correct!" : "Not quite."}
            {result.points_awarded > 0 && (
              <span className="ml-2 text-xs">+{result.points_awarded} pts</span>
            )}
          </p>
          {result.hint && !result.correct && (
            <p className="mt-1 text-xs italic opacity-80">Hint: {result.hint}</p>
          )}
          {result.explanation && (
            <div className="mt-2 text-slate-700">
              <MarkdownRenderer>{result.explanation}</MarkdownRenderer>
            </div>
          )}
          {onNextQuestion && (
            <button
              type="button"
              onClick={onNextQuestion}
              className="mt-3 w-full rounded border border-indigo-300 bg-white px-3 py-1.5 text-sm font-medium text-indigo-700 hover:bg-indigo-50"
            >
              Next question
            </button>
          )}
        </div>
      )}
    </div>
  );
}
