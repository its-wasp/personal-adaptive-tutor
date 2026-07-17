"""
End-to-end smoke test for the adaptive-learning-v1 backend.

Hits every major endpoint in dependency order using a fresh test user.
Prints per-step PASS/FAIL and exits non-zero on first failure.

Usage (with backend already running via docker compose):
    python backend/scripts/smoke_test.py
    python backend/scripts/smoke_test.py --base-url http://localhost:8000
"""
import argparse
import sys
import time
import uuid
from typing import Optional

import requests


class SmokeTest:

    def __init__(self, base_url: str):
        self.base = base_url.rstrip("/")
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self.quiz_id: Optional[str] = None
        self.message_id: Optional[str] = None
        self.failures = 0

    # ---- helpers ----

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base}{path}"
        headers = kwargs.pop("headers", {})
        headers.update(self._headers())
        return requests.request(method, url, headers=headers, timeout=60, **kwargs)

    def _step(self, name: str, ok: bool, detail: str = ""):
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""))
        if not ok:
            self.failures += 1

    def _expect_status(self, name: str, resp: requests.Response, expected: int) -> bool:
        ok = resp.status_code == expected
        self._step(name, ok, "" if ok else f"expected {expected}, got {resp.status_code}")
        return ok

    def _expect_ok(self, name: str, resp: requests.Response) -> Optional[dict]:
        if resp.status_code >= 400:
            self._step(name, False, f"HTTP {resp.status_code} — {resp.text[:200]}")
            return None
        try:
            data = resp.json()
        except Exception:
            self._step(name, False, "non-JSON response")
            return None
        self._step(name, True)
        return data

    # ---- test sequence ----

    def test_health(self):
        print("\n== Health ==")
        self._expect_ok("GET /health", self._request("GET", "/health"))
        self._expect_ok("GET /health/db", self._request("GET", "/health/db"))

    def test_auth(self):
        print("\n== Auth ==")
        email = f"smoke_{uuid.uuid4().hex[:8]}@smoketest.com"
        password = "SmokeTest123!"

        signup = self._expect_ok(
            "POST /auth/signup",
            self._request("POST", "/auth/signup", json={
                "email": email,
                "password": password,
                "name": "Smoke Tester",
            }),
        )
        if not signup:
            return
        self.token = signup.get("access_token")
        self.user_id = signup.get("user", {}).get("id")
        self._step("signup returns access_token", bool(self.token))
        self._step("signup returns user id", bool(self.user_id))

        login = self._expect_ok(
            "POST /auth/login",
            self._request("POST", "/auth/login", json={"email": email, "password": password}),
        )
        if login and login.get("access_token"):
            self.token = login["access_token"]

    def test_onboarding(self):
        print("\n== Onboarding ==")
        self._expect_ok("GET /onboarding/status", self._request("GET", "/onboarding/status"))

        self._expect_ok(
            "POST /onboarding/preferences",
            self._request("POST", "/onboarding/preferences", json={
                "learning_style": "EXAMPLE_FIRST",
                "pace_preference": "MODERATE",
                "explanation_detail_level": "STANDARD",
                "preferred_code_complexity": "SIMPLE",
                "use_analogies": True,
            }),
        )

        quiz = self._expect_ok("GET /onboarding/placement", self._request("GET", "/onboarding/placement"))
        if quiz is None:
            return

        questions = quiz if isinstance(quiz, list) else quiz.get("questions", [])
        # Answer every question with 'A' to exercise the grading path
        answers = [{"question_index": q["index"], "selected_option": "A"} for q in questions]
        self._expect_ok(
            "POST /onboarding/placement/submit",
            self._request("POST", "/onboarding/placement/submit", json={"answers": answers}),
        )

    def test_profile(self):
        print("\n== Profile ==")
        self._expect_ok("GET /profile/me", self._request("GET", "/profile/me"))

    def test_knowledge_graph(self):
        print("\n== Knowledge graph ==")
        self._expect_ok("GET /graph/dsa", self._request("GET", "/graph/dsa"))
        self._expect_ok("GET /graph/dsa/recommend", self._request("GET", "/graph/dsa/recommend"))

    def test_chat_flow(self):
        print("\n== Chat ==")
        created = self._expect_ok(
            "POST /chat/create",
            self._request("POST", "/chat/create", json={
                "topic_name": "Arrays",
                "topic_description": "Basics of arrays",
                "knowledge_level": "BEGINNER",
            }),
        )
        if not created:
            return
        self.session_id = created["id"]

        self._expect_ok(
            "GET /chat/sessions",
            self._request("GET", "/chat/sessions"),
        )

        msg = self._expect_ok(
            "POST /chat/message",
            self._request("POST", "/chat/message", json={
                "chat_session_id": self.session_id,
                "content": "Can you give me an example of array indexing?",
            }),
        )
        if msg:
            self.message_id = msg.get("id")

        self._expect_ok(
            "GET /chat/{id}/conversation",
            self._request("GET", f"/chat/{self.session_id}/conversation"),
        )

    def test_quiz_flow(self):
        print("\n== Quiz ==")
        if not self.session_id:
            self._step("skip — no session", False, "chat flow failed")
            return

        quiz = self._expect_ok(
            "POST /quiz/generate",
            self._request("POST", "/quiz/generate", json={"chat_session_id": self.session_id}),
        )
        if not quiz:
            return
        self.quiz_id = quiz["id"]
        correct = quiz.get("correct_option") or "A"  # may be hidden; fall back to A

        self._expect_ok(
            "POST /quiz/submit",
            self._request("POST", "/quiz/submit", json={
                "quiz_id": self.quiz_id,
                "selected_option": correct,
            }),
        )

    def test_authorization_isolation(self):
        """
        Sign up a second learner and confirm they cannot touch the first one's
        data. Every cross-user attempt must answer 404 rather than 403 — a 403
        would confirm the id exists and turn these endpoints into an oracle for
        enumerating other people's sessions.
        """
        print("\n== Authorization isolation (second user) ==")
        if not self.session_id:
            self._step("skip — no session to probe", False, "chat flow failed")
            return

        owner_token = self.token
        victim_session = self.session_id
        victim_quiz = self.quiz_id
        victim_message = self.message_id

        intruder_email = f"intruder_{uuid.uuid4().hex[:8]}@smoketest.com"
        signup = self._expect_ok(
            "POST /auth/signup (second user)",
            self._request("POST", "/auth/signup", json={
                "email": intruder_email,
                "password": "SmokeTest123!",
                "name": "Intruder",
            }),
        )
        if not signup:
            self.token = owner_token
            return

        # Act as the second user for the probes below.
        self.token = signup["access_token"]

        self._expect_status(
            "GET another user's conversation -> 404",
            self._request("GET", f"/chat/{victim_session}/conversation"),
            404,
        )
        self._expect_status(
            "POST message into another user's session -> 404",
            self._request("POST", "/chat/message", json={
                "chat_session_id": victim_session,
                "content": "let me in",
            }),
            404,
        )
        self._expect_status(
            "POST quiz/generate on another user's session -> 404",
            self._request("POST", "/quiz/generate", json={"chat_session_id": victim_session}),
            404,
        )
        self._expect_status(
            "DELETE another user's session -> 404",
            self._request("DELETE", f"/chat/{victim_session}"),
            404,
        )
        if victim_quiz:
            self._expect_status(
                "POST quiz/submit for another user's quiz -> 404",
                self._request("POST", "/quiz/submit", json={
                    "quiz_id": victim_quiz,
                    "selected_option": "A",
                }),
                404,
            )
        if victim_message:
            self._expect_status(
                "POST feedback on another user's message -> 404",
                self._request("POST", "/feedback/", json={
                    "message_id": victim_message,
                    "is_helpful": True,
                }),
                404,
            )

        # The second user's own session list must not leak the first user's.
        sessions = self._expect_ok("GET /chat/sessions (second user)", self._request("GET", "/chat/sessions"))
        if sessions is not None:
            leaked = any(str(s.get("id")) == str(victim_session) for s in sessions)
            self._step("second user's session list excludes the first user's", not leaked)

        # Restore the original identity for the remaining tests.
        self.token = owner_token

    def test_quiz_answer_not_leaked(self):
        """A freshly generated quiz must not ship its own answer key."""
        print("\n== Quiz answer withholding ==")
        if not self.session_id:
            self._step("skip — no session", False, "chat flow failed")
            return

        quiz = self._expect_ok(
            "POST /quiz/generate (fresh)",
            self._request("POST", "/quiz/generate", json={"chat_session_id": self.session_id}),
        )
        if not quiz:
            return

        for field in ("correct_option", "explanation", "hint"):
            self._step(
                f"generate response omits {field}",
                field not in quiz or quiz[field] is None,
                f"leaked: {quiz.get(field)!r}",
            )

        convo = self._expect_ok(
            "GET conversation (unanswered quiz)",
            self._request("GET", f"/chat/{self.session_id}/conversation"),
        )
        if not convo:
            return

        unanswered = [
            m for m in convo
            if m.get("message_type") == "QUIZ"
            and (m.get("quiz_data") or {}).get("selected_option") is None
        ]
        self._step("found an unanswered quiz in the conversation", bool(unanswered))
        for m in unanswered:
            data = m["quiz_data"]
            self._step(
                "unanswered quiz hides correct_option",
                data.get("correct_option") is None,
                f"leaked: {data.get('correct_option')!r}",
            )
            self._step("unanswered quiz still carries quiz_id (answerable)", bool(data.get("quiz_id")))

    def test_feedback(self):
        print("\n== Feedback ==")
        if not self.message_id:
            self._step("skip — no message id", False, "chat flow failed")
            return

        self._expect_ok(
            "POST /feedback/",
            self._request("POST", "/feedback/", json={
                "message_id": self.message_id,
                "is_helpful": True,
                "feedback_category": "JUST_RIGHT",
            }),
        )

    def test_review(self):
        print("\n== Spaced repetition ==")
        self._expect_ok("GET /review/due", self._request("GET", "/review/due"))

    def test_analytics(self):
        print("\n== Analytics ==")
        self._expect_ok("GET /analytics/me", self._request("GET", "/analytics/me"))

    def test_delete_session(self):
        print("\n== Delete chat session (CRUD) ==")
        if not self.session_id:
            return

        self._expect_ok(
            "DELETE /chat/{id}",
            self._request("DELETE", f"/chat/{self.session_id}"),
        )
        # Second delete should 404
        resp = self._request("DELETE", f"/chat/{self.session_id}")
        self._step("DELETE twice returns 404", resp.status_code == 404, f"got {resp.status_code}")

    def run(self) -> int:
        start = time.time()
        print(f"Smoke test against {self.base}")
        self.test_health()
        self.test_auth()
        if not self.token:
            print("\nAborting — no auth token, downstream tests cannot run.")
            return 1
        self.test_onboarding()
        self.test_profile()
        self.test_knowledge_graph()
        self.test_chat_flow()
        self.test_quiz_flow()
        self.test_quiz_answer_not_leaked()
        self.test_authorization_isolation()
        self.test_feedback()
        self.test_review()
        self.test_analytics()
        self.test_delete_session()

        elapsed = time.time() - start
        print(f"\nDone in {elapsed:.1f}s — {self.failures} failure(s)")
        return 1 if self.failures else 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()
    sys.exit(SmokeTest(args.base_url).run())


if __name__ == "__main__":
    main()
