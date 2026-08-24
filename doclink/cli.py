from __future__ import annotations

import argparse
from pathlib import Path

from .converter import convert_folder


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert a document folder to Markdown files.")
    parser.add_argument("input", type=Path, help="Folder with source documents")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output folder for Markdown files")
    parser.add_argument("--flat", action="store_true", help="Only process files directly inside the input folder")
    parser.add_argument("--no-overwrite", action="store_true", help="Keep existing Markdown files")
    args = parser.parse_args()

    output = args.output or args.input / "doclink_mds"
    results = convert_folder(
        args.input,
        output,
        recursive=not args.flat,
        overwrite=not args.no_overwrite,
    )

    created = sum(result.status == "created" for result in results)
    skipped = sum(result.status == "skipped" for result in results)
    failed = sum(result.status == "failed" for result in results)

    for result in results:
        target = result.target if result.target else "-"
        print(f"[{result.status}] {result.source} -> {target} ({result.message})")

    print(f"\nDone. Created: {created}, skipped: {skipped}, failed: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
