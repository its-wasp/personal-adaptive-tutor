import { memo } from "react";
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
 * Wrapped in React.memo so a growing message list doesn't re-render
 * every bubble when only the last one changes.
 */
function MessageBubble({ message, onQuizSubmitted }) {
  const isUser = message.role === "user";
  const isQuiz = message.message_type === "QUIZ";

  if (isQuiz) {
    return (
      <div className="flex justify-start">
        <div className="w-full max-w-2xl">
          <QuizCard
            messageId={message.id}
            quizId={message.quiz_data?.quiz_id || message.quiz_id}
            quizData={message.quiz_data}
            onSubmitted={onQuizSubmitted}
          />
        </div>
      </div>
    );
  }

  return (
    <div className={"flex " + (isUser ? "justify-end" : "justify-start")}>
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
    </div>
  );
}

export default memo(MessageBubble);
