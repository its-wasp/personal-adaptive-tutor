import { memo, useState } from "react";
import MarkdownRenderer from "../shared/MarkdownRenderer";
import QuizCard from "./QuizCard";

/**
 * One message in the conversation. Styling branches on `role`:
 *   user      → right-aligned indigo bubble
 *   assistant → left-aligned white bubble, rendered as markdown
 *
 * Special case: assistant messages of type QUIZ render a QuizCard
 * instead of text. The actual quiz body lives in `quiz_data`.
 *
 * Assistant messages may also carry `personalization_reasons` — a small
 * snapshot of the profile/RAG signals that shaped the response. We
 * surface them in a subtle collapsible pill so the hidden personalization
 * machinery is legible without distracting from the message itself.
 *
 * Wrapped in React.memo so a growing message list doesn't re-render
 * every bubble when only the last one changes.
 */
function MessageBubble({ message, onQuizSubmitted, onNextQuestion }) {
  const isUser = message.role === "user";
  const isQuiz = message.message_type === "QUIZ";

  if (isQuiz) {
    return (
      <div className="flex justify-start">
        <div className="w-full max-w-2xl">
          <QuizCard
            quizId={message.quiz_data?.quiz_id || message.quiz_id}
            quizData={message.quiz_data}
            onSubmitted={onQuizSubmitted}
            onNextQuestion={onNextQuestion}
          />
        </div>
      </div>
    );
  }

  const reasons = !isUser ? message.personalization_reasons : null;

  return (
    <div className={"flex flex-col " + (isUser ? "items-end" : "items-start")}>
      <div
        className={
          "max-w-2xl rounded-lg px-4 py-3 shadow-sm " +
          (isUser
            ? "bg-indigo-600 text-white"
            : "border border-slate-200 bg-white text-slate-800")
        }
      >
        {isUser ? (
          <p className="whitespace-pre-wrap text-sm">{message.content}</p>
        ) : (
          <MarkdownRenderer>{message.content}</MarkdownRenderer>
        )}
      </div>
      {reasons && reasons.length > 0 && <WhyThisResponse reasons={reasons} />}
    </div>
  );
}

/**
 * Collapsible pill shown below an assistant bubble. Default state is
 * collapsed so it doesn't compete with the message content — the goal
 * is to make personalization *discoverable*, not loud.
 */
function WhyThisResponse({ reasons }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="mt-1 ml-1 max-w-2xl">
      <button
        onClick={() => setOpen((v) => !v)}
        className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-400 hover:text-indigo-600"
      >
        <span aria-hidden="true">{open ? "▾" : "▸"}</span>
        Why this response
        <span className="rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-500">
          {reasons.length}
        </span>
      </button>
      {open && (
        <ul className="mt-1.5 space-y-1.5 rounded-md border border-indigo-100 bg-indigo-50/60 p-2.5 text-[11px]">
          {reasons.map((r, i) => (
            <li key={i} className="flex gap-2">
              <span className="shrink-0 rounded bg-white px-1.5 py-0.5 font-medium text-indigo-700 ring-1 ring-indigo-200">
                {r.label}
              </span>
              <span className="text-slate-600">{r.detail}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default memo(MessageBubble);
