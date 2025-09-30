import time
import logging

class SessionService:
    def __init__(self):
        self.logger = logging.getLogger("SessionService")
        self.sessions = {}

    def get(self, conn_id):
        return self.sessions.setdefault(conn_id, {
            "last_partial": "",
            "last_progress_ts": time.monotonic(),
            "last_partial_ts": time.monotonic(),
            "pending_text": "",
            "last_ai_request": "",
            "ai_processing": False,
            "last_ai_response_time": 0,
        })

    def cleanup(self, conn_id):
        if conn_id in self.sessions:
            del self.sessions[conn_id]
