"""Keyboard event handler for CLI interruptions."""

import threading
import sys
import termios
import tty
from typing import Optional, Callable


class KeyboardHandler:
    """
    Handle keyboard events during long-running tasks.

    Listens for ESC key press to allow user to interrupt operations.
    """

    def __init__(self):
        """Initialize keyboard handler."""
        self._stop_listening = threading.Event()
        self._listener_thread: Optional[threading.Thread] = None
        self._interrupt_callback: Optional[Callable] = None
        self._is_listening = False

    def start_listening(self, interrupt_callback: Callable[[], None]):
        """
        Start listening for ESC key press.

        Args:
            interrupt_callback: Function to call when ESC is pressed
        """
        if self._is_listening:
            return

        self._stop_listening.clear()
        self._interrupt_callback = interrupt_callback
        self._is_listening = True

        # Start listener thread
        self._listener_thread = threading.Thread(
            target=self._listen_for_esc,
            daemon=True,
            name="KeyboardListener"
        )
        self._listener_thread.start()

    def stop_listening(self):
        """Stop listening for keyboard events."""
        if not self._is_listening:
            return

        self._stop_listening.set()
        self._is_listening = False

        if self._listener_thread:
            self._listener_thread.join(timeout=0.5)
            self._listener_thread = None

    def _listen_for_esc(self):
        """Listen for ESC key press in a separate thread."""
        # Save original terminal settings
        old_settings = None

        try:
            # Only works on Unix-like systems
            if not sys.stdin.isatty():
                return

            old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())

            while not self._stop_listening.is_set():
                # Check if input is available (non-blocking)
                import select

                if select.select([sys.stdin], [], [], 0.1)[0]:
                    char = sys.stdin.read(1)

                    # ESC key is '\x1b'
                    if char == '\x1b':
                        if self._interrupt_callback:
                            self._interrupt_callback()
                        break

        except (termios.error, AttributeError, OSError):
            # Not a TTY or not supported on this platform
            pass
        finally:
            # Restore terminal settings
            if old_settings:
                try:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                except (termios.error, OSError):
                    pass


class CancellationToken:
    """
    Thread-safe cancellation token for interrupting long-running operations.
    """

    def __init__(self):
        """Initialize cancellation token."""
        self._cancelled = threading.Event()
        self._handler = KeyboardHandler()

    def is_cancelled(self) -> bool:
        """Check if operation has been cancelled."""
        return self._cancelled.is_set()

    def cancel(self):
        """Cancel the operation."""
        self._cancelled.set()
        self._handler.stop_listening()

    def start_listening(self):
        """Start listening for ESC key to cancel operation."""
        self._handler.start_listening(self.cancel)

    def stop_listening(self):
        """Stop listening for keyboard events."""
        self._handler.stop_listening()

    def __enter__(self):
        """Context manager entry."""
        self.start_listening()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_listening()
        return False


def with_cancellation(func: Callable) -> Callable:
    """
    Decorator to add ESC key cancellation to a function.

    The decorated function should periodically check `token.is_cancelled()`.

    Example:
        @with_cancellation
        def long_task(token: CancellationToken):
            for i in range(100):
                if token.is_cancelled():
                    raise KeyboardInterrupt("Task cancelled by user")
                # Do work...
    """
    def wrapper(*args, **kwargs):
        token = CancellationToken()
        with token:
            # Pass token as first argument
            return func(token, *args, **kwargs)

    return wrapper
