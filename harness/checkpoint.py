#!/usr/bin/env python3
"""
Atomic state persistence with breadcrumb crash recovery.

Implements tempfile+rename for atomic writes (Kazuma 037 D12) and
breadcrumb file for crash recovery (Kazuma 037 D11).

Layer 0 — foundation dependency for orchestrator.py.
"""
# FILE_TRAJECTORY: load-bearing
# TRAJECTORY_NOTE: All state persistence flows through this module.

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class CheckpointManager:
    """
    Manages atomic writes and crash recovery for expedition state.

    Atomic write: write to tempfile, then os.rename() into place.
    This guarantees the target file is either the old version or the
    new version — never a partial write. Works on Linux (same filesystem).

    Breadcrumb: before each agent invocation, write the task to a
    breadcrumb file. On startup, if a breadcrumb exists, the last
    invocation crashed — return that task for retry.
    """

    BREADCRUMB_NAME = ".breadcrumb.json"

    def __init__(self, state_dir: Path):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.breadcrumb_path = self.state_dir / self.BREADCRUMB_NAME

    def write_atomic(self, target: Path, content: str) -> None:
        """
        Write content to target atomically via tempfile+rename.

        The temp file is created in the same directory as the target
        to ensure same-filesystem rename (atomic on Linux).
        """
        target = Path(target)
        target.parent.mkdir(parents=True, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(
            dir=str(target.parent),
            prefix=f".{target.name}.",
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "w") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            os.rename(tmp_path, str(target))
        except Exception:
            # Clean up temp file on failure
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def write_breadcrumb(self, task: dict) -> None:
        """
        Write a breadcrumb before agent invocation.

        If the process crashes during invocation, the breadcrumb
        tells the next startup which task was in-flight.
        """
        breadcrumb = {
            "task": task,
            "started": datetime.now(timezone.utc).isoformat(),
        }
        self.write_atomic(
            self.breadcrumb_path,
            json.dumps(breadcrumb, indent=2, default=str),
        )

    def recover_breadcrumb(self) -> Optional[dict]:
        """
        Check for and recover from a crash breadcrumb.

        Returns the in-flight task if a breadcrumb exists, None otherwise.
        The breadcrumb is NOT cleared — the caller must clear it after
        successful completion via clear_breadcrumb().
        """
        if not self.breadcrumb_path.exists():
            return None

        try:
            data = json.loads(self.breadcrumb_path.read_text())
            return data.get("task")
        except (json.JSONDecodeError, KeyError):
            # Corrupted breadcrumb — clear and continue
            self.clear_breadcrumb()
            return None

    def clear_breadcrumb(self) -> None:
        """Remove the breadcrumb file after successful task completion."""
        if self.breadcrumb_path.exists():
            self.breadcrumb_path.unlink()

    def has_breadcrumb(self) -> bool:
        """Check if a breadcrumb exists (crash recovery pending)."""
        return self.breadcrumb_path.exists()
