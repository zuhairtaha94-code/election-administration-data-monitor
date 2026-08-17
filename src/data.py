"""Data-loading and missing-value utilities for the EAVS analysis."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


SENTINEL_LABELS = {
    -77: "valid_skip",
    -88: "does_not_apply",
    -99: "data_not_available",
}

IDENTIFIER_DTYPES = {
    "FIPSCode": "string",
    "Jurisdiction_Name": "string",
    "State_Full": "string",
    "State_Abbr": "string",
}


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Return the SHA-256 digest of a file without loading it all into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_eavs(path: Path) -> pd.DataFrame:
    """Load the EAVS CSV while preserving identifiers such as leading-zero FIPS codes."""

    return pd.read_csv(path, dtype=IDENTIFIER_DTYPES, low_memory=False)


def load_codebook(path: Path) -> pd.DataFrame:
    """Load the variable-level sheet from the official EAVS codebook."""

    return pd.read_excel(path, sheet_name="Variables")


def valid_numeric(series: pd.Series) -> pd.Series:
    """Return numeric responses and replace EAVS sentinel codes with missing values."""

    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.where(numeric >= 0)


def response_profile(series: pd.Series) -> dict[str, int]:
    """Count valid values, EAVS sentinel responses, and blank/invalid cells."""

    numeric = pd.to_numeric(series, errors="coerce")
    profile = {
        label: int((numeric == code).sum())
        for code, label in SENTINEL_LABELS.items()
    }
    profile["missing_blank_or_invalid"] = int(numeric.isna().sum())
    profile["valid_nonnegative"] = int((numeric >= 0).sum())
    return profile
