import { useState } from "react";
import toast from "react-hot-toast";
import { api } from "../../lib/api";

const LEVELS = [
  { value: "BEGINNER", label: "Beginner" },
  { value: "INTERMEDIATE", label: "Intermediate" },
  { value: "ADVANCED", label: "Advanced" },
];

/**
 * Dialog to start a new chat session. POSTs /chat/create which also
 * triggers the backend to generate the opening explanation (the LLM
 * call can take a few seconds — we keep the submit button disabled
 * so the user doesn't double-fire).
 */
export default function NewSessionModal({ onClose, onCreated }) {
  const [topicName, setTopicName] = useState("");
  const [description, setDescription] = useState("");
  const [level, setLevel] = useState("BEGINNER");
  const [creating, setCreating] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!topicName.trim() || creating) return;
    setCreating(true);
    try {
      const session = await api.post("/chat/create", {
        topic_name: topicName.trim(),
        topic_description: description.trim() || null,
        knowledge_level: level,
      });
      onCreated?.(session);
    } catch (err) {
      toast.error(err.detail || "Could not start session");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold">Start a new session</h2>
        <p className="mt-1 text-xs text-slate-500">
          Pick a topic and your current comfort level — the tutor will tailor the explanation.
        </p>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              Topic
            </label>
            <input
              type="text"
              required
              autoFocus
              value={topicName}
              onChange={(e) => setTopicName(e.target.value)}
              placeholder="e.g. Binary Search Trees"
              className="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              Description <span className="text-slate-400">(optional)</span>
            </label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Anything specific you want to focus on?"
              className="w-full resize-none rounded border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              Your level
            </label>
            <div className="flex gap-2">
              {LEVELS.map((l) => (
                <button
                  type="button"
                  key={l.value}
                  onClick={() => setLevel(l.value)}
                  className={
                    "flex-1 rounded border px-3 py-2 text-sm " +
                    (level === l.value
                      ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                      : "border-slate-300 text-slate-700 hover:bg-slate-50")
                  }
                >
                  {l.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={creating}
              className="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!topicName.trim() || creating}
              className="rounded bg-indigo-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-40"
            >
              {creating ? "Generating first lesson…" : "Start"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
