"""
Offline pipeline to build FAISS index for IT roles from CSV.
Uses backend/apps/documents/data/IT_Job_Roles_Skills.csv and core embedding service.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Dict

import pandas as pd
from django.conf import settings

from core.services.embedding_service import encode
from .role_faiss_manager import RoleFAISSManager

logger = logging.getLogger(__name__)

# CSV lives in documents app data (single source of truth)
DOCUMENTS_DATA_CSV = Path(settings.BASE_DIR) / "apps" / "documents" / "data" / "IT_Job_Roles_Skills.csv"


class RolePipelineException(Exception):
    """Pipeline / dataset error."""
    pass


class RoleEmbeddingPipeline:
    """Build FAISS index for IT roles from CSV (Job Title, Job Description, Skills)."""

    def __init__(self) -> None:
        self.dataset_path = DOCUMENTS_DATA_CSV
        if not self.dataset_path.exists():
            raise RolePipelineException(
                f"Dataset not found: {self.dataset_path} (expected backend/apps/documents/data/IT_Job_Roles_Skills.csv)"
            )

    def run(self) -> None:
        logger.info("Loading roles dataset...")
        df = pd.read_csv(self.dataset_path, encoding="latin1")
        required_cols = {"Job Title", "Job Description", "Skills"}
        if not required_cols.issubset(df.columns):
            raise RolePipelineException(f"Dataset must contain columns: {required_cols}")
        df = df.dropna(subset=list(required_cols))
        logger.info("Loaded %s roles.", len(df))

        texts = self._build_role_text(df)
        metadata = self._build_metadata(df)

        logger.info("Generating embeddings (batch, normalized)...")
        vectors = encode(texts, normalize=True, return_numpy=True)

        logger.info("Building FAISS index...")
        manager = RoleFAISSManager()
        manager.create_index(vectors, metadata)
        logger.info("FAISS build complete.")

    def _build_role_text(self, df: pd.DataFrame) -> List[str]:
        texts = []
        for _, row in df.iterrows():
            title = str(row["Job Title"]).strip()
            desc = str(row["Job Description"]).strip()
            skills = str(row["Skills"]).strip()
            combined = (
                f"Job Title: {title}. "
                f"Job Description: {desc}. "
                f"Required Skills: {skills}."
            )
            texts.append(combined)
        return texts

    def _build_metadata(self, df: pd.DataFrame) -> List[Dict]:
        metadata = []
        has_certs = "Certifications" in df.columns
        for _, row in df.iterrows():
            meta = {
                "role": row["Job Title"],
                "skills": row["Skills"],
                "description": row["Job Description"],
            }
            if has_certs and pd.notna(row.get("Certifications")):
                meta["certifications"] = str(row["Certifications"]).strip()
            else:
                meta["certifications"] = ""
            metadata.append(meta)
        return metadata
