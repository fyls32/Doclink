from __future__ import annotations

import argparse
from pathlib import Path

from .converter import ConversionOptions, convert_folder


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert a document folder to Markdown files.")
    parser.add_argument("input", type=Path, help="Folder with source documents")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output folder for Markdown files")
    parser.add_argument("--flat", action="store_true", help="Only process files directly inside the input folder")
    parser.add_argument("--no-overwrite", action="store_true", help="Keep existing Markdown files")
    parser.add_argument(
        "--ocr-engine",
        choices=("rapidocr", "tesseract_cli", "easyocr", "auto", "none"),
        default="rapidocr",
        help="OCR engine used by Docling",
    )
    parser.add_argument(
        "--ocr-mode",
        choices=("full_page", "pdf_aware_layout_regions", "layout_regions", "default"),
        default="full_page",
        help="OCR region mode",
    )
    parser.add_argument("--quality", choices=("fast", "balanced", "high", "max"), default="balanced")
    parser.add_argument("--ocr-lang", default="de", help="OCR language, e.g. de or en")
    parser.add_argument("--table-mode", choices=("accurate", "fast"), default="accurate")
    parser.add_argument("--no-cell-matching", action="store_true", help="Disable table cell matching")
    parser.add_argument("--extract-pictures", action="store_true", help="Extract picture images in Docling pipeline")
    parser.add_argument("--describe-pictures", action="store_true", help="Use Docling VLM picture descriptions")
    parser.add_argument("--chart-extraction", action="store_true", help="Enable chart extraction")
    args = parser.parse_args()

    output = args.output or args.input / "doclink_mds"
    options = ConversionOptions(
        ocr_engine=args.ocr_engine,
        ocr_mode=args.ocr_mode,
        quality=args.quality,
        ocr_lang=args.ocr_lang,
        easyocr_langs=tuple(lang.strip() for lang in args.ocr_lang.split(",") if lang.strip()) or ("de", "en"),
        tesseract_langs=tuple(_tesseract_langs(args.ocr_lang)),
        table_mode=args.table_mode,
        table_cell_matching=not args.no_cell_matching,
        extract_pictures=args.extract_pictures,
        describe_pictures=args.describe_pictures,
        chart_extraction=args.chart_extraction,
    )
    results = convert_folder(
        args.input,
        output,
        recursive=not args.flat,
        overwrite=not args.no_overwrite,
        options=options,
    )

    created = sum(result.status == "created" for result in results)
    skipped = sum(result.status == "skipped" for result in results)
    failed = sum(result.status == "failed" for result in results)

    for result in results:
        target = result.target if result.target else "-"
        print(f"[{result.status}] {result.source} -> {target} ({result.message})")

    print(f"\nDone. Created: {created}, skipped: {skipped}, failed: {failed}")
    return 1 if failed else 0

def _tesseract_langs(value: str) -> list[str]:
    aliases = {
        "de": "deu",
        "german": "deu",
        "deu": "deu",
        "en": "eng",
        "eng": "eng",
        "english": "eng",
        "fr": "fra",
        "fra": "fra",
        "it": "ita",
        "ita": "ita",
    }
    langs = []
    for item in value.replace(";", ",").split(","):
        token = item.strip().lower()
        if token:
            langs.append(aliases.get(token, token))
    return langs or ["deu", "eng"]


if __name__ == "__main__":
    raise SystemExit(main())
