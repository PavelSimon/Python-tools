"""Simple clipboard logger.

This module provides a function :func:`clipboard_logger` that prints new
clipboard values as they are copied.  Optionally, a list can be supplied to
collect the clipboard history.  The script can be run directly and supports a
``--duration`` flag to stop logging after a specified number of seconds.
Clipboard access failures from :mod:`pyperclip` are caught to prevent crashes.
"""

from __future__ import annotations

import argparse
import time

import pyperclip


def clipboard_logger(duration: float | None = None, history: list[str] | None = None) -> list[str] | None:
    """Log clipboard changes until duration expires or interrupted.

    Parameters
    ----------
    duration:
        Number of seconds to run.  If ``None`` (the default) the logger runs
        until interrupted.
    history:
        Optional list used to store the clipboard history.  When provided, each
        new clipboard entry is appended to this list and it is returned when the
        logger exits.

    Returns
    -------
    list[str] | None
        The ``history`` list if supplied; otherwise ``None``.
    """

    recent_value = ""
    start_time = time.time()

    while True:
        try:
            tmp_value = pyperclip.paste()
        except pyperclip.PyperclipException as exc:  # type: ignore[attr-defined]
            print(f"Clipboard access failed: {exc}")
            break

        if tmp_value != recent_value:
            recent_value = tmp_value
            if history is not None:
                history.append(recent_value)
            print(f"Copied: {recent_value}")

        if duration is not None and time.time() - start_time >= duration:
            break

        time.sleep(1)

    return history


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Log clipboard changes.")
    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help="Run time in seconds. Defaults to run until interrupted.",
    )
    args = parser.parse_args()

    try:
        clipboard_logger(duration=args.duration)
    except KeyboardInterrupt:
        print("\nLogging stopped by user.")
