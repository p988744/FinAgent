"""Query history management."""

from datetime import datetime

from finagent.models.answers import LegalAnswer


class QueryHistory:
    """Manages query history for the REPL session."""

    def __init__(self):
        self._history: list[tuple[str, LegalAnswer | None, datetime]] = []

    def add(self, query: str, answer: LegalAnswer | None):
        """Add a query and its answer to history."""
        self._history.append((query, answer, datetime.now()))

    def get_all(self) -> list[tuple[str, LegalAnswer | None, datetime]]:
        """Get all history entries."""
        return self._history

    def get_last(self) -> tuple[str, LegalAnswer | None, datetime] | None:
        """Get the last query."""
        return self._history[-1] if self._history else None

    def get_by_index(self, index: int) -> tuple[str, LegalAnswer | None, datetime] | None:
        """Get a specific query by index (1-based)."""
        if 1 <= index <= len(self._history):
            return self._history[index - 1]
        return None

    def clear(self):
        """Clear all history."""
        self._history.clear()

    def __len__(self) -> int:
        """Get number of queries in history."""
        return len(self._history)
