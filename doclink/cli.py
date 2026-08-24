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
        "--markdown-engine",
        choices=("docling", "lmstudio", "mineru"),
        default="docling",
        help="Markdown engine: Docling, local LM Studio vision model, or MinerU CLI",
    )
    parser.add_argument("--accelerator", choices=("auto", "cpu", "cuda"), default="auto", help="Docling accelerator device")
    parser.add_argument(
        "--pdf-backend",
        choices=("docling_parse", "pypdfium2", "dlparse_v4", "dlparse_v2", "dlparse_v1", "threaded_docling_parse", "auto"),
        default="docling_parse",
        help="PDF backend used by Docling",
    )
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
    parser.add_argument("--quality", choices=("fast", "balanced", "high", "max"), default="high")
    parser.add_argument("--ocr-scale", type=float, default=None, help="Override OCR render scale, e.g. 2.5, 3, 4")
    parser.add_argument("--ocr-lang", default="de", help="OCR language, e.g. de or en")
    parser.add_argument("--rapidocr-text-score", type=float, default=None, help="RapidOCR confidence threshold; lower can catch more text")
    parser.add_argument("--tesseract-psm", type=int, default=None, help="Tesseract page segmentation mode, e.g. 3, 6, 11")
    parser.add_argument("--table-mode", choices=("accurate", "fast", "off"), default="accurate")
    parser.add_argument("--table-structure-model", choices=("v1", "v2", "granite"), default="v1")
    parser.add_argument("--no-cell-matching", action="store_true", help="Disable table cell matching")
    parser.add_argument("--no-clean-table-duplicates", action="store_true", help="Keep repeated text in adjacent Markdown table cells")
    parser.add_argument("--force-backend-text", action="store_true", help="Prefer backend text where available")
    parser.add_argument("--no-layout-orphans", action="store_true", help="Disable orphan layout text clusters")
    parser.add_argument("--layout-keep-empty", action="store_true", help="Keep empty layout clusters")
    parser.add_argument("--layout-skip-cell-assignment", action="store_true", help="Skip assigning cells during layout analysis")
    parser.add_argument("--extract-pictures", action="store_true", help="Extract picture images in Docling pipeline")
    parser.add_argument("--describe-pictures", action="store_true", help="Use Docling VLM picture descriptions")
    parser.add_argument("--chart-extraction", action="store_true", help="Enable chart extraction")
    parser.add_argument("--no-heading-hierarchy", action="store_true", help="Disable Docling heading hierarchy inference")
    parser.add_argument("--no-traverse-picture-text", action="store_true", help="Disable traversing OCR text inside picture items")
    parser.add_argument("--escape-underscores", action="store_true", help="Escape underscores in Markdown export")
    parser.add_argument("--lmstudio-base-url", default="http://localhost:1234/v1", help="LM Studio OpenAI-compatible base URL")
    parser.add_argument("--lmstudio-model", default="", help="LM Studio model id; defaults to the first loaded model")
    parser.add_argument("--lmstudio-max-tokens", type=int, default=4096)
    parser.add_argument(
        "--mineru-backend",
        choices=("pipeline", "hybrid-engine", "vlm-engine", "hybrid-http-client", "vlm-http-client"),
        default="pipeline",
    )
    parser.add_argument("--mineru-method", choices=("auto", "ocr", "txt"), default="auto")
    parser.add_argument("--mineru-lang", default="", help="Optional MinerU language code")
    parser.add_argument("--mineru-no-table", action="store_true", help="Disable MinerU table parsing")
    parser.add_argument("--mineru-no-formula", action="store_true", help="Disable MinerU formula parsing")
    parser.add_argument("--mineru-image-analysis", action="store_true", help="Enable MinerU image/chart analysis")
    parser.add_argument("--mineru-api-url", default="", help="Existing MinerU FastAPI URL")
    args = parser.parse_args()

    output = args.output or args.input / "doclink_mds"
    options = ConversionOptions(
        markdown_engine=args.markdown_engine,
        accelerator=args.accelerator,
        pdf_backend=args.pdf_backend,
        ocr_engine=args.ocr_engine,
        ocr_mode=args.ocr_mode,
        quality=args.quality,
        ocr_scale=args.ocr_scale if args.ocr_scale and args.ocr_scale > 0 else None,
        ocr_lang=args.ocr_lang,
        rapidocr_text_score=args.rapidocr_text_score,
        tesseract_psm=args.tesseract_psm,
        easyocr_langs=tuple(lang.strip() for lang in args.ocr_lang.split(",") if lang.strip()) or ("de", "en"),
        tesseract_langs=tuple(_tesseract_langs(args.ocr_lang)),
        table_mode=args.table_mode,
        table_structure_model=args.table_structure_model,
        table_cell_matching=not args.no_cell_matching,
        clean_table_duplicates=not args.no_clean_table_duplicates,
        force_backend_text=args.force_backend_text,
        layout_create_orphan_clusters=not args.no_layout_orphans,
        layout_keep_empty_clusters=args.layout_keep_empty,
        layout_skip_cell_assignment=args.layout_skip_cell_assignment,
        extract_pictures=args.extract_pictures,
        describe_pictures=args.describe_pictures,
        chart_extraction=args.chart_extraction,
        heading_hierarchy=not args.no_heading_hierarchy,
        traverse_picture_text=not args.no_traverse_picture_text,
        escape_underscores=args.escape_underscores,
        lmstudio_base_url=args.lmstudio_base_url,
        lmstudio_model=args.lmstudio_model,
        lmstudio_max_tokens=args.lmstudio_max_tokens,
        mineru_backend=args.mineru_backend,
        mineru_method=args.mineru_method,
        mineru_lang=args.mineru_lang,
        mineru_table=not args.mineru_no_table,
        mineru_formula=not args.mineru_no_formula,
        mineru_image_analysis=args.mineru_image_analysis,
        mineru_api_url=args.mineru_api_url,
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
