"""Dataset service orchestration: ingestion, demo loading, profiling, and storage."""

from __future__ import annotations

import json
import uuid
from typing import List, Optional

import pandas as pd

from datamind.config import get_settings
from datamind.contracts import (
    DatasetSummary,
    DemoDatasetKind,
    ErrorCode,
    ServiceError,
)
from datamind.data.demos import generate_demo_csv
from datamind.data.ingestion import validate_and_parse_csv
from datamind.data.profiling import profile_dataframe
from datamind.storage.artifacts import compute_sha256_file, safe_relative_path, write_atomic_bytes
from datamind.storage.repositories import DatasetRepository


class DatasetService:
    """Service handling CSV imports, demo dataset generation, and profiling."""

    def __init__(self, repo: Optional[DatasetRepository] = None):
        if repo is None:
            settings = get_settings()
            repo = DatasetRepository(settings.db_path)
        self.repo = repo

    def import_csv(
        self,
        project_id: str,
        raw_bytes: bytes,
        display_name: str,
    ) -> DatasetSummary:
        """Validate, parse, profile, and persist an uploaded CSV file."""
        settings = get_settings()
        parsed = validate_and_parse_csv(raw_bytes, filename=display_name)
        profile, schema = profile_dataframe(parsed.df)

        # Generate unique folder and destination path
        dataset_id = str(uuid.uuid4())
        dest_dir = settings.datasets_dir / dataset_id
        dest_path = dest_dir / "raw.csv"

        # Atomically write raw bytes to immutable storage
        actual_sha256 = write_atomic_bytes(dest_path, parsed.raw_bytes)
        rel_path = safe_relative_path(settings.storage_dir, dest_path)

        # Source metadata JSON
        source_json = json.dumps(
            {
                "kind": "upload",
                "original_filename": display_name,
                "byte_size": len(raw_bytes),
            },
            sort_keys=True,
        )

        return self.repo.create(
            project_id=project_id,
            display_name=display_name.strip(),
            source_kind="upload",
            source_json=source_json,
            raw_sha256=actual_sha256,
            raw_relative_path=rel_path,
            parser_version=parsed.parser_version,
            parser_config_json=json.dumps(parsed.parser_config, sort_keys=True),
            schema_json=schema.model_dump_json(),
            profile_json=profile.model_dump_json(),
            row_count=parsed.row_count,
            column_count=parsed.column_count,
        )

    def load_demo(
        self,
        project_id: str,
        demo_kind: DemoDatasetKind,
        seed: int = 42,
    ) -> DatasetSummary:
        """Generate and ingest an offline demo dataset."""
        display_name, raw_bytes, source_meta = generate_demo_csv(demo_kind, seed=seed)
        settings = get_settings()

        parsed = validate_and_parse_csv(raw_bytes, filename=f"{demo_kind.value}.csv")
        profile, schema = profile_dataframe(parsed.df)

        dataset_id = str(uuid.uuid4())
        dest_dir = settings.datasets_dir / dataset_id
        dest_path = dest_dir / "raw.csv"

        actual_sha256 = write_atomic_bytes(dest_path, parsed.raw_bytes)
        rel_path = safe_relative_path(settings.storage_dir, dest_path)

        source_json = json.dumps(
            {
                "kind": "demo",
                "demo_kind": demo_kind.value,
                "seed": seed,
                **source_meta,
            },
            sort_keys=True,
        )

        return self.repo.create(
            project_id=project_id,
            display_name=display_name,
            source_kind="demo",
            source_json=source_json,
            raw_sha256=actual_sha256,
            raw_relative_path=rel_path,
            parser_version=parsed.parser_version,
            parser_config_json=json.dumps(parsed.parser_config, sort_keys=True),
            schema_json=schema.model_dump_json(),
            profile_json=profile.model_dump_json(),
            row_count=parsed.row_count,
            column_count=parsed.column_count,
        )

    def get_dataset(self, dataset_id: str) -> Optional[DatasetSummary]:
        """Fetch dataset metadata by ID."""
        return self.repo.get_by_id(dataset_id)

    def list_datasets(
        self, project_id: str, include_archived: bool = False
    ) -> List[DatasetSummary]:
        """List all datasets in a project."""
        return self.repo.list_by_project(project_id, include_archived=include_archived)

    def load_dataframe(self, dataset_id: str) -> pd.DataFrame:
        """Load and verify the stored raw CSV into a DataFrame."""
        summary = self.get_dataset(dataset_id)
        if not summary:
            raise ServiceError(
                ErrorCode.DATASET_NOT_FOUND,
                f"Dataset with ID '{dataset_id}' not found.",
                field="dataset_id",
            )

        settings = get_settings()
        file_path = settings.storage_dir / summary.raw_relative_path
        if not file_path.exists():
            raise ServiceError(
                ErrorCode.MODEL_UNAVAILABLE,
                f"Dataset file '{summary.raw_relative_path}' is missing on disk.",
            )

        # Check integrity
        current_sha256 = compute_sha256_file(file_path)
        if current_sha256 != summary.raw_sha256:
            raise ServiceError(
                ErrorCode.MODEL_UNAVAILABLE,
                "Stored dataset checksum mismatch. File may have been modified or corrupted.",
            )

        raw_bytes = file_path.read_bytes()
        parsed = validate_and_parse_csv(raw_bytes, filename=summary.display_name)
        return parsed.df
