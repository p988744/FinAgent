"""Query history management."""

from datetime import datetime
from typing import List, Optional, Tuple

from finagent.models.answers import LegalAnswer


class QueryHistory:
    """Manages query history for the REPL session."""

    def __init__(self):
        self._history: List[Tuple[str, Optional[LegalAnswer], datetime]] = []

    def add(self, query: str, answer: Optional[LegalAnswer]):
        """Add a query and its answer to history."""
        self._history.append((query, answer, datetime.now()))

    def get_all(self) -> List[Tuple[str, Optional[LegalAnswer], datetime]]:
        """Get all history entries."""
        return self._history

    def get_last(self) -> Optional[Tuple[str, Optional[LegalAnswer], datetime]]:
        """Get the last query."""
        return self._history[-1] if self._history else None

    def get_by_index(self, index: int) -> Optional[Tuple[str, Optional[LegalAnswer], datetime]]:
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
