from __future__ import annotations

import csv
import html
import json
import os
import re
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Iterable
from xml.etree import ElementTree


SUPPORTED_EXTENSIONS = {
    ".bmp",
    ".csv",
    ".doc",
    ".docx",
    ".epub",
    ".jpeg",
    ".jpg",
    ".htm",
    ".html",
    ".json",
    ".log",
    ".md",
    ".odp",
    ".ods",
    ".odt",
    ".pdf",
    ".png",
    ".ppt",
    ".pptx",
    ".rtf",
    ".tif",
    ".tiff",
    ".txt",
    ".webp",
    ".xls",
    ".xlsx",
    ".xml",
}

DOCLING_EXTENSIONS = {
    ".bmp",
    ".csv",
    ".doc",
    ".docx",
    ".epub",
    ".htm",
    ".html",
    ".jpeg",
    ".jpg",
    ".md",
    ".odp",
    ".ods",
    ".odt",
    ".pdf",
    ".png",
    ".ppt",
    ".pptx",
    ".tif",
    ".tiff",
    ".webp",
    ".xls",
    ".xlsx",
}


@dataclass(frozen=True)
class ConversionResult:
    source: Path
    target: Path | None
    status: str
    message: str


ProgressCallback = Callable[[ConversionResult], None]


def list_supported_files(input_dir: Path, recursive: bool = True, output_dir: Path | None = None) -> list[Path]:
    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve() if output_dir else None
    pattern = "**/*" if recursive else "*"
    files: list[Path] = []

    for path in input_dir.glob(pattern):
        if not path.is_file():
            continue
        if output_dir and _is_relative_to(path.resolve(), output_dir):
            continue
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(path)

    return sorted(files, key=lambda item: str(item).lower())


def convert_folder(
    input_dir: Path,
    output_dir: Path,
    recursive: bool = True,
    overwrite: bool = True,
    progress: ProgressCallback | None = None,
) -> list[ConversionResult]:
    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve()

    if not input_dir.exists() or not input_dir.is_dir():
        raise ValueError(f"Input folder does not exist: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[ConversionResult] = []
    used_targets: set[Path] = set()

    for source in list_supported_files(input_dir, recursive=recursive, output_dir=output_dir):
        relative = source.relative_to(input_dir)
        target = _target_for(output_dir, relative, source.suffix.lower(), used_targets)
        used_targets.add(target)

        try:
            if target.exists() and not overwrite:
                result = ConversionResult(source, target, "skipped", "Markdown already exists")
            else:
                markdown = convert_file(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(markdown, encoding="utf-8", newline="\n")
                result = ConversionResult(source, target, "created", "Markdown created")
        except MissingDependencyError as exc:
            result = ConversionResult(source, target, "skipped", str(exc))
        except EmptyExtractionError as exc:
            result = ConversionResult(source, target, "failed", str(exc))
        except Exception as exc:  # pragma: no cover - shown in the GUI log for user action.
            result = ConversionResult(source, target, "failed", f"{type(exc).__name__}: {exc}")

        results.append(result)
        if progress:
            progress(result)

    return results


def convert_file(source: Path) -> str:
    suffix = source.suffix.lower()

    body = ""
    docling_error: Exception | None = None

    if suffix in DOCLING_EXTENSIONS:
        try:
            body = _docling_to_markdown(source)
        except MissingDependencyError as exc:
            docling_error = exc
        except Exception as exc:
            docling_error = exc

    if _has_content(body):
        pass
    elif suffix in {".txt", ".log", ".md"}:
        body = _read_text(source)
    elif suffix == ".csv":
        body = _csv_to_markdown(source)
    elif suffix == ".json":
        body = f"```json\n{json.dumps(json.loads(_read_text(source)), indent=2, ensure_ascii=False)}\n```"
    elif suffix in {".html", ".htm"}:
        body = _html_to_text(_read_text(source))
    elif suffix == ".xml":
        body = f"```xml\n{_read_text(source).strip()}\n```"
    elif suffix == ".rtf":
        body = _rtf_to_text(_read_text(source))
    elif suffix == ".pdf":
        body = _pdf_to_text(source)
    elif suffix == ".docx":
        body = _docx_to_markdown(source)
    elif suffix == ".xlsx":
        body = _xlsx_to_markdown(source)
    elif suffix == ".pptx":
        body = _pptx_to_markdown(source)
    elif suffix == ".odt":
        body = _odt_to_text(source)
    elif isinstance(docling_error, MissingDependencyError):
        raise docling_error
    elif docling_error:
        raise RuntimeError(f"Docling conversion failed: {docling_error}") from docling_error
    else:
        raise ValueError(f"Unsupported file type: {source.suffix}")

    if not _has_content(body):
        suffix_hint = " Scanned PDFs/images may need OCR support and a first run can take longer while models load."
        raise EmptyExtractionError(f"No text content could be extracted from {source.name}.{suffix_hint}")

    title = source.stem.replace("_", " ").replace("-", " ").strip() or source.name
    source_name = source.name.replace("\\", "/")
    return f"# {title}\n\n_Source: `{source_name}`_\n\n{body.strip()}\n"


class MissingDependencyError(RuntimeError):
    pass


class EmptyExtractionError(RuntimeError):
    pass


def _docling_to_markdown(path: Path) -> str:
    try:
        from docling.document_converter import DocumentConverter
    except ImportError as exc:
        raise MissingDependencyError("docling is missing; run install_windows.bat or pip install -r requirements.txt") from exc

    if path.stat().st_size == 0:
        raise EmptyExtractionError(f"{path.name} is empty and cannot be converted.")

    converter = _get_docling_converter()

    with tempfile.TemporaryDirectory(prefix="doclink_") as temp_dir:
        safe_path = Path(temp_dir) / f"source{path.suffix.lower()}"
        shutil.copy2(path, safe_path)
        result = converter.convert(safe_path)

    return result.document.export_to_markdown()


def _get_docling_converter():
    if not hasattr(_get_docling_converter, "_converter"):
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions, TableStructureOptions
        from docling.document_converter import DocumentConverter
        from docling.document_converter import PdfFormatOption

        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options = TableStructureOptions(do_cell_matching=True)
        pipeline_options.ocr_options = _get_ocr_options()

        _get_docling_converter._converter = DocumentConverter(  # type: ignore[attr-defined]
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
            }
        )
    return _get_docling_converter._converter  # type: ignore[attr-defined]


def _get_ocr_options():
    from docling.datamodel.pipeline_options import OcrMode

    rapidocr_lang = os.getenv("DOCLINK_OCR_LANG", "de")
    easyocr_langs = [lang.strip() for lang in os.getenv("DOCLINK_EASYOCR_LANGS", "de,en").split(",") if lang.strip()]

    try:
        from docling.datamodel.pipeline_options import RapidOcrOptions

        return RapidOcrOptions(mode=OcrMode.FULL_PAGE, lang=[rapidocr_lang])
    except Exception:
        pass

    try:
        from docling.datamodel.pipeline_options import EasyOcrOptions

        return EasyOcrOptions(mode=OcrMode.FULL_PAGE, lang=easyocr_langs)
    except Exception as exc:
        raise MissingDependencyError(
            "OCR support is missing; run install_windows.bat again or install rapidocr-onnxruntime/easyocr."
        ) from exc


def _has_content(markdown: str) -> bool:
    text = re.sub(r"!\[[^\]]*]\([^)]*\)", "", markdown)
    text = re.sub(r"\bpage\s+\d+\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bslide\s+\d+\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"#+\s*", "", text)
    text = re.sub(r"[_`|\\-]", " ", text)
    return bool(re.search(r"[A-Za-z0-9À-ÖØ-öø-ÿ]{3,}", text))


def _target_for(output_dir: Path, relative: Path, suffix: str, used_targets: set[Path]) -> Path:
    target = output_dir / relative.with_suffix(".md")
    if target not in used_targets:
        return target

    alternate = output_dir / relative.with_name(f"{relative.stem}{suffix.replace('.', '_')}.md")
    counter = 2
    while alternate in used_targets:
        alternate = output_dir / relative.with_name(f"{relative.stem}{suffix.replace('.', '_')}_{counter}.md")
        counter += 1
    return alternate


def _read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def _csv_to_markdown(path: Path) -> str:
    text = _read_text(path)
    sample = text[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample) if sample.strip() else csv.excel
    except csv.Error:
        dialect = csv.excel

    rows = list(csv.reader(text.splitlines(), dialect))
    if not rows:
        return ""

    width = max(len(row) for row in rows)
    normalized = [row + [""] * (width - len(row)) for row in rows]
    header = normalized[0]
    separator = ["---"] * width
    lines = [_markdown_row(header), _markdown_row(separator)]
    lines.extend(_markdown_row(row) for row in normalized[1:])
    return "\n".join(lines)


def _markdown_row(values: Iterable[str]) -> str:
    escaped = [str(value).replace("|", "\\|").replace("\n", " ").strip() for value in values]
    return "| " + " | ".join(escaped) + " |"


class _TextHTMLParser(HTMLParser):
    block_tags = {"br", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "p", "td", "th", "tr"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.block_tags:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.block_tags:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(html.unescape(data.strip()))

    def text(self) -> str:
        return "\n".join(line.strip() for line in "".join(self.parts).splitlines() if line.strip())


def _html_to_text(content: str) -> str:
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        parser = _TextHTMLParser()
        parser.feed(content)
        return parser.text()

    soup = BeautifulSoup(content, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text("\n", strip=True)


def _rtf_to_text(content: str) -> str:
    content = re.sub(r"\\'[0-9a-fA-F]{2}", " ", content)
    content = re.sub(r"\\[a-zA-Z]+\d* ?", " ", content)
    content = content.replace("{", " ").replace("}", " ")
    content = content.replace("\\", "")
    return "\n".join(line.strip() for line in content.splitlines() if line.strip())


def _pdf_to_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise MissingDependencyError("pypdf is missing; run install_windows.bat or pip install -r requirements.txt") from exc

    reader = PdfReader(str(path))
    pages = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(f"## Page {index}\n\n{text.strip()}")
    return "\n\n".join(pages)


def _docx_to_markdown(path: Path) -> str:
    try:
        from docx import Document
    except ImportError as exc:
        raise MissingDependencyError("python-docx is missing; run install_windows.bat or pip install -r requirements.txt") from exc

    document = Document(str(path))
    lines: list[str] = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text:
            style = paragraph.style.name.lower() if paragraph.style else ""
            if style.startswith("heading"):
                level_match = re.search(r"(\d+)", style)
                level = min(int(level_match.group(1)), 6) if level_match else 2
                lines.append(f"{'#' * level} {text}")
            else:
                lines.append(text)
            lines.append("")

    for table in document.tables:
        rows = [[cell.text.strip().replace("\n", " ") for cell in row.cells] for row in table.rows]
        if rows:
            width = max(len(row) for row in rows)
            normalized = [row + [""] * (width - len(row)) for row in rows]
            lines.append(_markdown_row(normalized[0]))
            lines.append(_markdown_row(["---"] * width))
            lines.extend(_markdown_row(row) for row in normalized[1:])
            lines.append("")

    return "\n".join(lines)


def _xlsx_to_markdown(path: Path) -> str:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise MissingDependencyError("openpyxl is missing; run install_windows.bat or pip install -r requirements.txt") from exc

    workbook = load_workbook(path, read_only=True, data_only=True)
    sections: list[str] = []

    for sheet in workbook.worksheets:
        sections.append(f"## {sheet.title}")
        rows = []
        for row in sheet.iter_rows(values_only=True):
            values = ["" if value is None else str(value) for value in row]
            if any(value.strip() for value in values):
                rows.append(values)
        if rows:
            width = max(len(row) for row in rows)
            normalized = [row + [""] * (width - len(row)) for row in rows]
            sections.append(_markdown_row(normalized[0]))
            sections.append(_markdown_row(["---"] * width))
            sections.extend(_markdown_row(row) for row in normalized[1:])
        sections.append("")

    return "\n".join(sections)


def _pptx_to_markdown(path: Path) -> str:
    try:
        from pptx import Presentation
    except ImportError as exc:
        raise MissingDependencyError("python-pptx is missing; run install_windows.bat or pip install -r requirements.txt") from exc

    presentation = Presentation(str(path))
    sections: list[str] = []

    for index, slide in enumerate(presentation.slides, start=1):
        sections.append(f"## Slide {index}")
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                sections.append(shape.text.strip())
        sections.append("")

    return "\n".join(sections)


def _odt_to_text(path: Path) -> str:
    namespaces = {
        "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    }

    with zipfile.ZipFile(path) as archive:
        content = archive.read("content.xml")

    root = ElementTree.fromstring(content)
    lines: list[str] = []
    for paragraph in root.findall(".//text:p", namespaces):
        text = "".join(paragraph.itertext()).strip()
        if text:
            lines.append(text)
    return "\n\n".join(lines)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False
