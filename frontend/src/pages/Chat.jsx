import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import toast from "react-hot-toast";
import { api } from "../lib/api";
import { useAuth } from "../hooks/useAuth";
import { useApiGet } from "../hooks/useApi";
import SessionList from "../components/chat/SessionList";
import MessageBubble from "../components/chat/MessageBubble";
import ChatInput from "../components/chat/ChatInput";

// Modal is only mounted when the user clicks "New" — lazy-load it so
// the initial chat bundle stays small.
const NewSessionModal = lazy(() => import("../components/chat/NewSessionModal"));

/**
 * Chat page — the main learning experience.
 *
 * Layout: sessions sidebar + active conversation. The active session is
 * driven by the URL (/chat/:sessionId), so the sidebar, conversation
 * view, and browser history all stay in sync without extra state.
 *
 * Data:
 *   - sessions: fetched once via useApiGet, kept in local state so we
 *     can mutate it after create/delete without refetching.
 *   - conversation: fetched whenever :sessionId changes.
 *
 * Why a ref for the scroll container: we don't want to re-render on
 * every scroll or append — we just need to scroll to the bottom after
 * a message is added. A ref + useEffect on message count is enough.
 */
export default function Chat() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { profile } = useAuth();

  const [sessions, setSessions] = useState([]);
  const [messages, setMessages] = useState([]);
  const [loadingConv, setLoadingConv] = useState(false);
  const [sending, setSending] = useState(false);
  const [generatingQuiz, setGeneratingQuiz] = useState(false);
  const [showNewModal, setShowNewModal] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const scrollRef = useRef(null);
  // When the user sends a message we pin THAT message at the top of the
  // viewport so the tutor's reply fills the space below (ChatGPT-style).
  // `null` = no anchor → fall back to scroll-to-bottom behaviour.
  const anchorRef = useRef(null);

  // Gate: only logged-in users with completed onboarding can access chat.
  // Onboarding redirect is already handled in Dashboard, but coming
  // directly to /chat also needs the check.
  if (profile && !profile.onboarding_completed) {
    return <Navigate to="/onboarding" replace />;
  }

  // ----- sessions list -----
  const {
    data: sessionsData,
    loading: loadingSessions,
  } = useApiGet("/chat/sessions");

  useEffect(() => {
    if (sessionsData) setSessions(sessionsData);
  }, [sessionsData]);

  const activeSession = useMemo(
    () => sessions.find((s) => s.id === sessionId),
    [sessions, sessionId]
  );

  // ----- conversation for the active session -----
  useEffect(() => {
    if (!sessionId) {
      setMessages([]);
      return;
    }
    let cancelled = false;
    setLoadingConv(true);
    api
      .get(`/chat/${sessionId}/conversation`)
      .then((data) => {
        if (!cancelled) setMessages(data || []);
      })
      .catch((err) => {
        if (!cancelled) {
          if (err.status === 404) {
            toast.error("Session not found");
            navigate("/chat", { replace: true });
          } else {
            toast.error(err.detail || "Could not load conversation");
          }
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingConv(false);
      });
    return () => {
      cancelled = true;
    };
  }, [sessionId, navigate]);

  // Scroll behaviour on message count change:
  //   - if an anchor is set (user just sent) → pin that message to the top
  //   - otherwise → scroll to bottom (initial load, quiz inserts, etc.)
  // We clear the anchor once a reply has landed after it, so only ONE
  // send/reply cycle is pinned — subsequent additions scroll normally.
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    if (anchorRef.current) {
      const node = el.querySelector(`[data-msg-id="${anchorRef.current}"]`);
      if (node) {
        node.scrollIntoView({ block: "start", behavior: "smooth" });
        const anchorIdx = messages.findIndex((m) => m.id === anchorRef.current);
        if (anchorIdx >= 0 && anchorIdx < messages.length - 1) {
          anchorRef.current = null;
        }
        return;
      }
    }
    el.scrollTop = el.scrollHeight;
  }, [messages]);

  // Reset the anchor when the user switches sessions — otherwise we'd
  // try to pin a message that no longer exists in the DOM.
  useEffect(() => {
    anchorRef.current = null;
  }, [sessionId]);

  // ----- actions -----
  const handleNewCreated = useCallback((session) => {
    setSessions((prev) => [
      {
        id: session.id,
        topic_name: session.topic_name,
        title: session.title,
        current_level: session.current_level,
        concept_node_id: session.concept_node_id,
        created_at: new Date().toISOString(),
      },
      ...prev,
    ]);
    setShowNewModal(false);
    navigate(`/chat/${session.id}`);
  }, [navigate]);

  const handleDeleted = useCallback(
    (deletedId) => {
      setSessions((prev) => prev.filter((s) => s.id !== deletedId));
      if (deletedId === sessionId) {
        navigate("/chat", { replace: true });
      }
    },
    [sessionId, navigate]
  );

  const handleSend = useCallback(
    async (content) => {
      if (!sessionId) return;
      // Optimistic user message so the UI feels instant.
      const tempId = `tmp-${Date.now()}`;
      // Pin this message to the top as the tutor reply streams in below.
      anchorRef.current = tempId;
      setMessages((prev) => [
        ...prev,
        {
          id: tempId,
          role: "user",
          message_type: "GENERAL",
          content,
          created_at: new Date().toISOString(),
        },
      ]);
      setSending(true);
      try {
        const assistantMsg = await api.post("/chat/message", {
          chat_session_id: sessionId,
          content,
        });
        setMessages((prev) => [...prev, assistantMsg]);
      } catch (err) {
        // Remove the optimistic user message on failure.
        setMessages((prev) => prev.filter((m) => m.id !== tempId));
        toast.error(err.detail || "Could not send message");
      } finally {
        setSending(false);
      }
    },
    [sessionId]
  );

  const handleGenerateQuiz = useCallback(async () => {
    if (!sessionId || generatingQuiz) return;
    setGeneratingQuiz(true);
    try {
      const quiz = await api.post("/quiz/generate", { chat_session_id: sessionId });
      // Append a QUIZ message locally so we don't have to refetch the
      // whole conversation. Shape matches what /conversation returns.
      setMessages((prev) => [
        ...prev,
        {
          id: `quiz-${quiz.id}`,
          role: "assistant",
          message_type: "QUIZ",
          content: "Quiz generated",
          created_at: new Date().toISOString(),
          quiz_data: {
            quiz_id: quiz.id,
            question: quiz.question_text,
            options: quiz.options_json,
            difficulty: quiz.difficulty,
            points: quiz.points,
            hint: quiz.hint,
            explanation: quiz.explanation,
            correct_option: null, // hidden until submit
            selected_option: null,
            is_correct: null,
            points_awarded: null,
          },
          // Surfaced separately so QuizCard can use it even before
          // quiz_data.quiz_id is resolved on backend-driven messages.
          quiz_id: quiz.id,
        },
      ]);
    } catch (err) {
      toast.error(err.detail || "Could not generate quiz");
    } finally {
      setGeneratingQuiz(false);
    }
  }, [sessionId, generatingQuiz]);

  return (
    <div className="flex h-screen bg-slate-50">
      <SessionList
        sessions={sessions}
        activeId={sessionId}
        onNew={() => setShowNewModal(true)}
        onDeleted={handleDeleted}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="flex flex-1 flex-col">
        {sessionId ? (
          <>
            <header className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3">
              <div className="flex min-w-0 items-center gap-2">
                {/* Hamburger — mobile only */}
                <button
                  onClick={() => setSidebarOpen(true)}
                  className="rounded p-1 text-slate-500 hover:bg-slate-100 md:hidden"
                  aria-label="Open sidebar"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                    <line x1="3" y1="6" x2="21" y2="6" />
                    <line x1="3" y1="12" x2="21" y2="12" />
                    <line x1="3" y1="18" x2="21" y2="18" />
                  </svg>
                </button>
                <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h1 className="truncate text-sm font-semibold text-slate-900">
                    {activeSession?.title || activeSession?.topic_name || "Session"}
                  </h1>
                  {activeSession?.concept_node_id && (
                    <span
                      title="This session is linked to a concept on the knowledge graph — quiz results update your mastery."
                      className="inline-flex items-center gap-1 rounded-full bg-indigo-50 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-indigo-700 ring-1 ring-indigo-200"
                    >
                      <span className="h-1.5 w-1.5 rounded-full bg-indigo-500" />
                      Graph concept
                    </span>
                  )}
                </div>
                {activeSession && (
                  <p className="text-xs text-slate-500">
                    {activeSession.topic_name} · {activeSession.current_level}
                  </p>
                )}
                </div>
              </div>
              <button
                onClick={handleGenerateQuiz}
                disabled={generatingQuiz || loadingConv}
                className="rounded border border-indigo-300 bg-white px-3 py-1.5 text-xs font-medium text-indigo-700 hover:bg-indigo-50 disabled:opacity-40"
              >
                {generatingQuiz ? "Generating…" : "Generate quiz"}
              </button>
            </header>

            <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4">
              {loadingConv && messages.length === 0 ? (
                <p className="text-center text-sm text-slate-500">Loading conversation…</p>
              ) : (
                <div className="mx-auto flex max-w-4xl flex-col gap-3">
                  {messages.map((m) => (
                    <div key={m.id} data-msg-id={m.id}>
                      <MessageBubble
                        message={m}
                        onNextQuestion={handleGenerateQuiz}
                      />
                    </div>
                  ))}
                  {sending && (
                    <div className="flex justify-start">
                      <div className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm text-slate-500">
                        Tutor is thinking…
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="border-t border-slate-200 bg-white p-3">
              <div className="mx-auto max-w-4xl">
                <ChatInput onSend={handleSend} sending={sending} />
              </div>
            </div>
          </>
        ) : (
          <EmptyState
            loading={loadingSessions}
            hasSessions={sessions.length > 0}
            onNew={() => setShowNewModal(true)}
            onOpenSidebar={() => setSidebarOpen(true)}
          />
        )}
      </main>

      {showNewModal && (
        <Suspense fallback={null}>
          <NewSessionModal
            onClose={() => setShowNewModal(false)}
            onCreated={handleNewCreated}
          />
        </Suspense>
      )}
    </div>
  );
}

function EmptyState({ loading, hasSessions, onNew, onOpenSidebar }) {
  return (
    <div className="relative flex flex-1 items-center justify-center p-6">
      {/* Hamburger for mobile when no session is selected */}
      <button
        onClick={onOpenSidebar}
        className="absolute left-4 top-4 rounded p-1 text-slate-500 hover:bg-slate-100 md:hidden"
        aria-label="Open sidebar"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <line x1="3" y1="6" x2="21" y2="6" />
          <line x1="3" y1="12" x2="21" y2="12" />
          <line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>
      <div className="max-w-sm text-center">
        {loading ? (
          <p className="text-sm text-slate-500">Loading your sessions…</p>
        ) : hasSessions ? (
          <>
            <h2 className="text-base font-medium text-slate-900">Pick a session to continue</h2>
            <p className="mt-1 text-sm text-slate-500">
              Select one from the sidebar, or start a new topic.
            </p>
            <button
              onClick={onNew}
              className="mt-4 rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            >
              New session
            </button>
          </>
        ) : (
          <>
            <h2 className="text-base font-medium text-slate-900">No sessions yet</h2>
            <p className="mt-1 text-sm text-slate-500">
              Start a topic and the tutor will teach you at your level.
            </p>
            <button
              onClick={onNew}
              className="mt-4 rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            >
              Start your first session
            </button>
          </>
        )}
      </div>
    </div>
  );
}
