"""
Unit tests for the session-ownership guards.

No database here: the repositories are mocked, because what's under test is the
authorization *decision*, not the query that backs it. The paired end-to-end
checks live in scripts/smoke_test.py, which drives two real accounts.

The property every case below defends: a resource belonging to someone else is
indistinguishable from one that does not exist. Anything that leaked a 403 for
"exists but not yours" would let an attacker enumerate valid ids.
"""
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.services.chat_service import ChatService
from app.services.errors import NotFoundError
from app.services.quiz_service import QuizService


def make_session(user_id, concept_node_id=None):
    session = MagicMock()
    session.user_id = user_id
    session.concept_node_id = concept_node_id
    session.conversation_summary = None
    return session


@pytest.fixture
def chat_service():
    service = ChatService(MagicMock())
    service.repo = MagicMock()
    return service


class TestChatSessionOwnership:
    def test_owner_gets_the_session(self, chat_service):
        owner = uuid4()
        session = make_session(owner)
        chat_service.repo.get_session.return_value = session

        assert chat_service._assert_owns_session(uuid4(), owner) is session

    def test_missing_session_raises(self, chat_service):
        chat_service.repo.get_session.return_value = None

        with pytest.raises(NotFoundError):
            chat_service._assert_owns_session(uuid4(), uuid4())

    def test_other_users_session_raises(self, chat_service):
        chat_service.repo.get_session.return_value = make_session(uuid4())

        with pytest.raises(NotFoundError):
            chat_service._assert_owns_session(uuid4(), uuid4())

    def test_string_and_uuid_owner_ids_compare_equal(self, chat_service):
        # user_id arrives as a UUID from the JWT but may be a string on the
        # model depending on driver; the guard compares stringified forms.
        owner = uuid4()
        chat_service.repo.get_session.return_value = make_session(str(owner))

        assert chat_service._assert_owns_session(uuid4(), owner)

    def test_missing_and_foreign_are_indistinguishable(self, chat_service):
        chat_service.repo.get_session.return_value = None
        with pytest.raises(NotFoundError) as missing:
            chat_service._assert_owns_session(uuid4(), uuid4())

        chat_service.repo.get_session.return_value = make_session(uuid4())
        with pytest.raises(NotFoundError) as foreign:
            chat_service._assert_owns_session(uuid4(), uuid4())

        assert str(missing.value) == str(foreign.value)


class TestChatEntryPoints:
    def test_get_conversation_rejects_other_users_session(self, chat_service):
        chat_service.repo.get_session.return_value = make_session(uuid4())

        with pytest.raises(NotFoundError):
            chat_service.get_conversation(uuid4(), uuid4())

    def test_send_message_rejects_other_users_session(self, chat_service):
        chat_service.repo.get_session.return_value = make_session(uuid4())

        with pytest.raises(NotFoundError):
            chat_service.send_message(uuid4(), uuid4(), "hello")

    def test_send_message_writes_nothing_when_rejected(self, chat_service):
        """Authorization must happen before the first insert, not after it."""
        chat_service.repo.get_session.return_value = None

        with pytest.raises(NotFoundError):
            chat_service.send_message(uuid4(), uuid4(), "hello")

        chat_service.repo.create_message.assert_not_called()

    def test_delete_session_returns_false_for_other_users_session(self, chat_service):
        chat_service.repo.get_session.return_value = make_session(uuid4())

        assert chat_service.delete_session(uuid4(), uuid4()) is False
        chat_service.repo.delete_session.assert_not_called()

    def test_delete_session_deletes_for_owner(self, chat_service):
        owner = uuid4()
        chat_service.repo.get_session.return_value = make_session(owner)

        assert chat_service.delete_session(uuid4(), owner) is True
        chat_service.repo.delete_session.assert_called_once()


class TestQuizOwnership:
    def _service(self, session):
        """QuizService filters on user_id in SQL, so stub the query chain."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = session
        service = QuizService(db)
        service.repo = MagicMock()
        return service

    def test_owned_session_returned(self):
        session = make_session(uuid4())
        assert self._service(session)._owned_session(uuid4(), uuid4()) is session

    def test_unowned_session_raises(self):
        # The user_id filter is in the WHERE clause, so a session owned by
        # somebody else simply doesn't come back.
        with pytest.raises(NotFoundError):
            self._service(None)._owned_session(uuid4(), uuid4())

    def test_submit_answer_rejects_unknown_quiz(self):
        service = self._service(None)
        service.repo.get_quiz.return_value = None

        with pytest.raises(NotFoundError):
            service.submit_answer(uuid4(), uuid4(), "A")

    def test_submit_answer_rejects_quiz_in_another_users_session(self):
        service = self._service(None)  # ownership query finds nothing
        quiz = MagicMock()
        quiz.chat_session_id = uuid4()
        service.repo.get_quiz.return_value = quiz

        with pytest.raises(NotFoundError):
            service.submit_answer(uuid4(), uuid4(), "A")

    def test_submit_answer_records_nothing_when_rejected(self):
        service = self._service(None)
        quiz = MagicMock()
        quiz.chat_session_id = uuid4()
        service.repo.get_quiz.return_value = quiz

        with pytest.raises(NotFoundError):
            service.submit_answer(uuid4(), uuid4(), "A")

        service.repo.create_attempt.assert_not_called()

    def test_generate_quiz_rejects_other_users_session(self):
        service = self._service(None)

        with pytest.raises(NotFoundError):
            service.generate_quiz(uuid4(), uuid4())
