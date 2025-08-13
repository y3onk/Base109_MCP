import argparse
import json
import os
from pathlib import Path
from typing import Dict, Iterable, List


def iter_js_ts_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in {".js", ".ts"}:
            yield path


def read_file_text(path: Path) -> str:
    # Use UTF-8 and ignore decoding errors to mirror GitHub API behavior
    return path.read_text(encoding="utf-8", errors="ignore")


def to_relative_path(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root).as_posix())
    except ValueError:
        # Fallback to POSIX-like string
        return str(path.as_posix())


def build_output(root: Path) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    for file_path in iter_js_ts_files(root):
        results.append({
            "path": to_relative_path(root, file_path),
            "content": read_file_text(file_path),
        })
    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read local JS/TS files and print JSON in the same format as the GitHub fetcher."
    )
    parser.add_argument("folder", help="Root folder containing sample JS/TS files")
    args = parser.parse_args()

    root = Path(args.folder).resolve()
    if not root.exists() or not root.is_dir():
        print(json.dumps({"error": f"Folder not found or not a directory: {root}"}, ensure_ascii=False))
        return 1

    data = build_output(root)
    # Match get_github_file.py formatting: indent=2, ensure_ascii=False
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


