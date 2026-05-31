import { Link } from "react-router-dom";
import toast from "react-hot-toast";
import { api } from "../../lib/api";

/**
 * Sidebar with the user's chat sessions plus a "new" button.
 *
 * On mobile (< md) the sidebar renders as a slide-over overlay controlled
 * by the parent. On desktop it's always visible as a static sidebar.
 *
 * Delete is destructive so we confirm first. On delete we notify the
 * parent via onDeleted so it can evict the session from local state
 * and navigate away if the active one was just removed.
 */
export default function SessionList({ sessions, activeId, onNew, onDeleted, open, onClose }) {
  async function handleDelete(e, sessionId) {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm("Delete this session? This will remove all its messages.")) return;
    try {
      await api.delete(`/chat/${sessionId}`);
      onDeleted?.(sessionId);
      toast.success("Session deleted");
    } catch (err) {
      toast.error(err.detail || "Could not delete session");
    }
  }

  return (
    <>
      {/* Backdrop — mobile only, shown when sidebar is open */}
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/30 md:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={
          "fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-200 bg-slate-50 transition-transform duration-200 " +
          "md:static md:z-auto md:translate-x-0 " +
          (open ? "translate-x-0" : "-translate-x-full")
        }
      >
        <div className="flex items-center justify-between border-b border-slate-200 p-3">
          <Link
            to="/dashboard"
            className="text-sm text-slate-600 hover:text-slate-900"
          >
            ← Dashboard
          </Link>
          <div className="flex items-center gap-2">
            <button
              onClick={onNew}
              className="rounded bg-indigo-600 px-2 py-1 text-xs font-medium text-white hover:bg-indigo-700"
            >
              + New
            </button>
            {/* Close button — mobile only */}
            <button
              onClick={onClose}
              className="rounded p-1 text-slate-400 hover:text-slate-700 md:hidden"
              aria-label="Close sidebar"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {sessions.length === 0 && (
            <p className="p-4 text-xs text-slate-500">
              No sessions yet. Start one to begin learning.
            </p>
          )}

          <ul className="divide-y divide-slate-200">
            {sessions.map((s) => {
              const isActive = s.id === activeId;
              return (
                <li key={s.id}>
                  <Link
                    to={`/chat/${s.id}`}
                    onClick={onClose}
                    className={
                      "group block px-3 py-2.5 text-sm " +
                      (isActive ? "bg-white" : "hover:bg-white/60")
                    }
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <p
                          className={
                            "truncate font-medium " +
                            (isActive ? "text-indigo-700" : "text-slate-800")
                          }
                          title={s.title || s.topic_name}
                        >
                          {s.title || s.topic_name}
                        </p>
                        <p className="mt-0.5 truncate text-xs text-slate-500">
                          {s.topic_name} · {s.current_level}
                        </p>
                      </div>
                      <button
                        onClick={(e) => handleDelete(e, s.id)}
                        className="opacity-0 transition-opacity group-hover:opacity-100"
                        aria-label="Delete session"
                        title="Delete"
                      >
                        <span className="rounded px-1 text-xs text-slate-400 hover:bg-slate-200 hover:text-rose-600">
                          ✕
                        </span>
                      </button>
                    </div>
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      </aside>
    </>
  );
}
