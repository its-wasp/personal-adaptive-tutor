import { useRef, useState } from "react";

/**
 * Auto-growing textarea + send button. Enter sends, Shift+Enter adds a
 * newline. The `sending` flag disables input to prevent the user from
 * double-submitting while the tutor is generating a response.
 */
export default function ChatInput({ onSend, sending, disabled }) {
  const [text, setText] = useState("");
  const textareaRef = useRef(null);

  function handleSubmit(e) {
    e?.preventDefault();
    const content = text.trim();
    if (!content || sending || disabled) return;
    onSend(content);
    setText("");
    // Reset height so the textarea collapses back to one line after send.
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  function handleChange(e) {
    setText(e.target.value);
    // Auto-resize up to ~5 lines.
    const el = e.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-2">
      <textarea
        ref={textareaRef}
        value={text}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        disabled={disabled || sending}
        placeholder={disabled ? "Select a session to start chatting" : "Ask anything… (Enter to send)"}
        rows={1}
        className="min-h-[40px] flex-1 resize-none rounded border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none disabled:bg-slate-50"
      />
      <button
        type="submit"
        disabled={!text.trim() || sending || disabled}
        className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-40"
      >
        {sending ? "…" : "Send"}
      </button>
    </form>
  );
}
