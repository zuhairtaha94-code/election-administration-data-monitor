"""Download and verify the official 2024 EAVS Version 2.0 source files."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data import sha256_file  # noqa: E402


def download(url: str, destination: Path) -> None:
    """Download a URL atomically so partial files are never mistaken for sources."""

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "election-administration-data-monitor/1.0"},
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as temp:
        temp_path = Path(temp.name)
        with urllib.request.urlopen(request) as response:
            shutil.copyfileobj(response, temp)
    temp_path.replace(destination)


def require_digest(path: Path, expected: str) -> None:
    """Fail if a downloaded file differs from the documented release."""

    observed = sha256_file(path)
    if observed != expected:
        raise ValueError(
            f"SHA-256 mismatch for {path.name}: expected {expected}, observed {observed}"
        )


def acquire_file(file_record: dict[str, str], raw_dir: Path, force: bool) -> None:
    destination = raw_dir / file_record["filename"]
    if force or not destination.exists():
        print(f"Downloading {destination.name}...")
        download(file_record["url"], destination)
    else:
        print(f"Reusing existing {destination.name}.")

    require_digest(destination, file_record["sha256"])
    print(f"Verified {destination.name}.")

    archive_member = file_record.get("archive_member")
    if archive_member:
        with zipfile.ZipFile(destination) as archive:
            archive.extract(archive_member, raw_dir)
        extracted_path = raw_dir / archive_member
        require_digest(extracted_path, file_record["archive_member_sha256"])
        print(f"Extracted and verified {extracted_path.name}.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--force",
        action="store_true",
        help="Download source files again even when verified copies already exist.",
    )
    args = parser.parse_args()

    manifest_path = PROJECT_ROOT / "data" / "source_manifest.json"
    raw_dir = PROJECT_ROOT / "data" / "raw"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    for file_record in manifest["files"]:
        acquire_file(file_record, raw_dir, args.force)


if __name__ == "__main__":
    main()
