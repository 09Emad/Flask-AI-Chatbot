from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4


def now_iso():
    return datetime.now(timezone.utc).isoformat()


class SessionStore:
    def __init__(self):
        self._lock = Lock()
        self._sessions = {}

    def _new_session(self):
        session_id = uuid4().hex
        return {
            "id": session_id,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "messages": [],
        }

    def create(self):
        with self._lock:
            session = self._new_session()
            self._sessions[session["id"]] = session
            return session

    def get_or_create(self, session_id=None):
        with self._lock:
            if session_id and session_id in self._sessions:
                return self._sessions[session_id]
            session = self._new_session()
            self._sessions[session["id"]] = session
            return session

    def reset(self, session_id=None):
        with self._lock:
            if session_id and session_id in self._sessions:
                self._sessions[session_id]["messages"] = []
                self._sessions[session_id]["updated_at"] = now_iso()
                return self._sessions[session_id]
            session = self._new_session()
            self._sessions[session["id"]] = session
            return session

    def store_message(self, session, role, content):
        with self._lock:
            session["messages"].append(
                {
                    "role": role,
                    "content": content,
                    "timestamp": now_iso(),
                }
            )
            session["updated_at"] = now_iso()

    def summary(self, session):
        return {
            "id": session["id"],
            "created_at": session["created_at"],
            "updated_at": session["updated_at"],
            "message_count": len(session["messages"]),
        }

    def count(self):
        with self._lock:
            return len(self._sessions)

