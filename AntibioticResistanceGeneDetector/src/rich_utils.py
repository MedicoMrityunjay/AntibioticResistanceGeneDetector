"""
Helpers for optional Rich integration: provides a Console, Progress factory,
and Rich logging handler setup. Designed to fall back gracefully when
`rich` is not installed or disabled.
"""
from typing import Optional
import logging

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
    from rich.table import Table
    from rich.logging import RichHandler
    RICH_AVAILABLE = True
except Exception:
    # Rich isn't available in the environment; provide minimal fallbacks
    RICH_AVAILABLE = False
    Console = None
    Progress = None
    Table = None
    RichHandler = None


class DummyConsole:
    """
    Minimal Console-compatible fallback used when Rich is unavailable.

    The object implements a small subset of the Rich Console API used by
    the project (``print``, ``rule``, and ``status``) and intentionally
    keeps behavior simple so it is safe in non-interactive environments.
    """

    def __init__(self, quiet: bool = False):
        self.quiet = quiet

    def print(self, *args, **kwargs):
        if not self.quiet:
            print(*args)

    def rule(self, *args, **kwargs):
        if not self.quiet:
            print("-" * 40)

    def status(self, message: str):
        # Return a dummy context manager
        class _Ctx:
            def __enter__(self_inner):
                if not self.quiet:
                    print(message)

            def __exit__(self_inner, exc_type, exc, tb):
                return False

        return _Ctx()


def get_console(rich_enabled: bool = True, quiet: bool = False):
    """
    Return a console-like object for user-facing output.

    Parameters
    ----------
    rich_enabled : bool, optional
        Whether to prefer Rich output when available (default: True).
    quiet : bool, optional
        If True, return a console that suppresses printing.

    Returns
    -------
    Console-like
        Either a ``rich.console.Console`` instance (when Rich is available
        and enabled) or a :class:`DummyConsole` instance.
    """
    # If quiet mode requested, always return dummy console to suppress output
    if quiet:
        return DummyConsole(quiet=True)
    if not rich_enabled or not RICH_AVAILABLE:
        return DummyConsole(quiet=quiet)
    try:
        return Console()
    except Exception:
        return DummyConsole(quiet=quiet)


def get_progress(rich_enabled: bool = True, console: Optional[object] = None, **kwargs):
    """
    Construct a Rich :class:`rich.progress.Progress` instance when available.

    Parameters
    ----------
    rich_enabled : bool, optional
        Whether Rich-based progress should be used.
    console : object, optional
        Optional Console to attach to the progress instance.
    **kwargs
        Extra keyword arguments passed to the Progress constructor.

    Returns
    -------
    Progress or None
        A Rich :class:`rich.progress.Progress` when available, otherwise
        ``None`` (callers must provide a software fallback in that case).
    """
    if not rich_enabled or not RICH_AVAILABLE:
        return None
    # Provide a sensible default set of columns
    columns = [SpinnerColumn(), " ", TextColumn("{task.description}"), BarColumn(), TimeElapsedColumn(), TimeRemainingColumn()]
    return Progress(*columns, console=(console if isinstance(console, Console) else None), **kwargs)


def setup_rich_logging(rich_enabled: bool = True, quiet: bool = False):
    """
    Configure the Python ``logging`` module to use Rich's logging handler.

    Parameters
    ----------
    rich_enabled : bool, optional
        Whether to enable Rich logging when available (default: True).
    quiet : bool, optional
        If True, set the logging level to ``ERROR``.

    Returns
    -------
    bool
        ``True`` if a Rich logging handler was installed, ``False`` when
        falling back to the standard logging configuration.
    """
    # Remove existing handlers
    for h in list(logging.root.handlers):
        logging.root.removeHandler(h)

    level = logging.ERROR if quiet else logging.INFO

    if rich_enabled and RICH_AVAILABLE and RichHandler is not None:
        handler = RichHandler()
        logging.basicConfig(level=level, handlers=[handler], format="%(message)s")
        return True
    else:
        # Default basic config to stdout + file can be configured by caller
        logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(message)s")
        return False


def print_error(message: str, console=None, rich_enabled: bool = True):
    """
    Present an error message to the user using Rich styling when possible.

    Parameters
    ----------
    message : str
        The error message to display.
    console : Console-like, optional
        Optional console to use. If not provided and Rich is available,
        a new Console will be created.
    rich_enabled : bool, optional
        Whether to prefer Rich-based display (default: True).

    Returns
    -------
    None
    """
    if not rich_enabled or not RICH_AVAILABLE:
        # plain fallback
        print(f"ERROR: {message}")
        return

    try:
        if console is None:
            console = Console()
        from rich.panel import Panel
        console.print(Panel(message, title="Error", style="bold red"))
    except Exception:
        # last-resort fallback
        print(f"ERROR: {message}")
