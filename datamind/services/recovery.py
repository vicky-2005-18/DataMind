"""Recovery service: guarded reconciliation of interrupted runs and orphaned artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from datamind.config import get_settings
from datamind.storage.database import get_connection
from datamind.storage.locks import WorkspaceLock


class RecoveryService:
    """Guarded crash recovery and workspace reconciliation service."""

    def __init__(self, lock: Optional[WorkspaceLock] = None, db_path: Optional[Path] = None):
        settings = get_settings()
        self.db_path = db_path or settings.db_path
        lock_file = settings.locks_dir / "workspace.lock"
        self.lock = lock or WorkspaceLock(lock_file)

    def reconcile(self, storage_root: Optional[Path] = None) -> Dict[str, int]:
        """
        Reconcile workspace state after abnormal termination or on restart.

        Guards:
        - If the workspace lock is currently held (an active training run is in flight),
          reconcile returns immediately without modifying state (satisfying T23).
        - If free, acquires the lock and transitions any stale 'running' experiments and
          trials to 'interrupted'.
        - Scans for orphaned artifact directories not recorded in SQLite (satisfying T42).
        """
        if self.lock.is_locked:
            # Active run in progress; do not touch
            return {
                "interrupted_experiments": 0,
                "interrupted_trials": 0,
                "orphaned_artifacts": 0,
                "skipped_reason": "lock_held",
            }

        settings = get_settings()
        root = storage_root or settings.storage_root

        interrupted_exps = 0
        interrupted_trials = 0
        orphans_detected = 0

        with self.lock.acquire():
            conn = get_connection(self.db_path)
            try:
                # 1. Detect and mark interrupted experiments
                running_cur = conn.execute("SELECT id FROM experiments WHERE status = 'running'")
                running_exp_ids = [row["id"] for row in running_cur.fetchall()]

                if running_exp_ids:
                    interrupted_exps = len(running_exp_ids)
                    err_payload = json.dumps(
                        {"error": "Interrupted by abnormal process termination; recovered on restart."}
                    )
                    for exp_id in running_exp_ids:
                        conn.execute(
                            """
                            UPDATE experiments
                            SET status = 'interrupted',
                                finished_at = CURRENT_TIMESTAMP,
                                error_json = ?
                            WHERE id = ?
                            """,
                            (err_payload, exp_id),
                        )
                        trial_cur = conn.execute(
                            """
                            UPDATE trials
                            SET status = 'interrupted',
                                error_json = ?
                            WHERE experiment_id = ? AND status = 'running'
                            """,
                            (err_payload, exp_id),
                        )
                        interrupted_trials += trial_cur.rowcount
                    conn.commit()

                # 2. Reconcile filesystem artifacts vs DB (T42)
                exp_storage_dir = root / "experiments"
                if exp_storage_dir.exists():
                    all_db_exps = {
                        r["id"] for r in conn.execute("SELECT id FROM experiments").fetchall()
                    }
                    for item in exp_storage_dir.iterdir():
                        if item.is_dir() and item.name not in all_db_exps:
                            orphans_detected += 1
                            # Orphaned directory: tag so it is not loadable
                            orphan_marker = item / ".orphan"
                            if not orphan_marker.exists():
                                orphan_marker.write_text(
                                    "Orphaned artifact: not registered in database."
                                )
            finally:
                conn.close()

        return {
            "interrupted_experiments": interrupted_exps,
            "interrupted_trials": interrupted_trials,
            "orphaned_artifacts": orphans_detected,
        }
