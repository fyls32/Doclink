from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from doclink.converter import ConversionOptions, ConversionResult, convert_folder, list_supported_files


class DoclinkApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Doclink")
        self.geometry("1040x780")
        self.minsize(860, 700)

        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.recursive_var = tk.BooleanVar(value=True)
        self.overwrite_var = tk.BooleanVar(value=True)
        self.markdown_engine_var = tk.StringVar(value="docling")
        self.accelerator_var = tk.StringVar(value="auto")
        self.pdf_backend_var = tk.StringVar(value="docling_parse")
        self.ocr_engine_var = tk.StringVar(value="rapidocr")
        self.ocr_mode_var = tk.StringVar(value="full_page")
        self.quality_var = tk.StringVar(value="high")
        self.ocr_scale_var = tk.StringVar(value="")
        self.ocr_lang_var = tk.StringVar(value="de")
        self.rapidocr_text_score_var = tk.StringVar(value="")
        self.tesseract_psm_var = tk.StringVar(value="")
        self.table_mode_var = tk.StringVar(value="accurate")
        self.table_structure_model_var = tk.StringVar(value="v1")
        self.table_cell_matching_var = tk.BooleanVar(value=False)
        self.force_backend_text_var = tk.BooleanVar(value=False)
        self.layout_create_orphan_clusters_var = tk.BooleanVar(value=True)
        self.layout_keep_empty_clusters_var = tk.BooleanVar(value=False)
        self.layout_skip_cell_assignment_var = tk.BooleanVar(value=False)
        self.extract_pictures_var = tk.BooleanVar(value=False)
        self.describe_pictures_var = tk.BooleanVar(value=False)
        self.chart_extraction_var = tk.BooleanVar(value=False)
        self.heading_hierarchy_var = tk.BooleanVar(value=True)
        self.traverse_picture_text_var = tk.BooleanVar(value=True)
        self.escape_underscores_var = tk.BooleanVar(value=False)
        self.lmstudio_base_url_var = tk.StringVar(value="http://localhost:1234/v1")
        self.lmstudio_model_var = tk.StringVar(value="")
        self.lmstudio_max_tokens_var = tk.StringVar(value="4096")
        self.lmstudio_table_format_var = tk.StringVar(value="tabs")
        self.mineru_backend_var = tk.StringVar(value="pipeline")
        self.mineru_method_var = tk.StringVar(value="auto")
        self.mineru_lang_var = tk.StringVar(value="")
        self.mineru_table_var = tk.BooleanVar(value=True)
        self.mineru_formula_var = tk.BooleanVar(value=True)
        self.mineru_image_analysis_var = tk.BooleanVar(value=False)
        self.mineru_api_url_var = tk.StringVar(value="")
        self.docstrange_processing_var = tk.StringVar(value="local_gpu")
        self.docstrange_output_var = tk.StringVar(value="html")
        self.status_var = tk.StringVar(value="Bereit")
        self.progress_var = tk.IntVar(value=0)

        self._events: queue.Queue[tuple[str, object]] = queue.Queue()
        self._worker: threading.Thread | None = None

        self._build_ui()
        self.after(100, self._drain_events)

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)

        header = ttk.Frame(self, padding=(16, 14, 16, 8))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        title = ttk.Label(header, text="Doclink Markdown-Erzeuger", font=("Segoe UI", 16, "bold"))
        title.grid(row=0, column=0, sticky="w")
        subtitle = ttk.Label(header, text="Ordner auswaehlen, Dokumente verarbeiten, Markdown-Dateien erstellen.")
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))

        form = ttk.Frame(self, padding=(16, 8))
        form.grid(row=1, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Dokumentenordner").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=6)
        ttk.Entry(form, textvariable=self.input_var).grid(row=0, column=1, sticky="ew", pady=6)
        ttk.Button(form, text="Auswaehlen", command=self._choose_input).grid(row=0, column=2, padx=(10, 0), pady=6)

        ttk.Label(form, text="Markdown-Ziel").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=6)
        ttk.Entry(form, textvariable=self.output_var).grid(row=1, column=1, sticky="ew", pady=6)
        ttk.Button(form, text="Aendern", command=self._choose_output).grid(row=1, column=2, padx=(10, 0), pady=6)

        options = ttk.Frame(self, padding=(16, 0, 16, 8))
        options.grid(row=2, column=0, sticky="ew")
        options.columnconfigure(4, weight=1)

        ttk.Checkbutton(options, text="Unterordner einbeziehen", variable=self.recursive_var).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(options, text="Vorhandene .md ueberschreiben", variable=self.overwrite_var).grid(row=0, column=1, sticky="w", padx=(18, 0))
        self.start_button = ttk.Button(options, text="Verarbeiten", command=self._start)
        self.start_button.grid(row=0, column=2, sticky="e", padx=(18, 0))
        ttk.Button(options, text="Zielordner oeffnen", command=self._open_output).grid(row=0, column=3, sticky="e", padx=(10, 0))

        docling_options = ttk.LabelFrame(self, text="Docling / OCR Optionen", padding=(12, 8))
        docling_options.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 8))
        for column in range(6):
            docling_options.columnconfigure(column, weight=1)

        ttk.Label(docling_options, text="Markdown-Modus").grid(row=0, column=0, sticky="w", pady=(0, 4))
        markdown_engine = ttk.Combobox(
            docling_options,
            textvariable=self.markdown_engine_var,
            state="readonly",
            values=("docling", "lmstudio", "mineru", "docstrange"),
            width=16,
        )
        markdown_engine.grid(row=1, column=0, sticky="ew", padx=(0, 10))

        ttk.Label(docling_options, text="Beschleunigung").grid(row=0, column=1, sticky="w", pady=(0, 4))
        accelerator = ttk.Combobox(
            docling_options,
            textvariable=self.accelerator_var,
            state="readonly",
            values=("auto", "cpu", "cuda"),
            width=12,
        )
        accelerator.grid(row=1, column=1, sticky="ew", padx=(0, 10))

        ttk.Label(docling_options, text="OCR Engine").grid(row=0, column=2, sticky="w", pady=(0, 4))
        engine = ttk.Combobox(
            docling_options,
            textvariable=self.ocr_engine_var,
            state="readonly",
            values=("rapidocr", "tesseract_cli", "easyocr", "auto", "none"),
            width=16,
        )
        engine.grid(row=1, column=2, sticky="ew", padx=(0, 10))

        ttk.Label(docling_options, text="OCR Modus").grid(row=0, column=3, sticky="w", pady=(0, 4))
        mode = ttk.Combobox(
            docling_options,
            textvariable=self.ocr_mode_var,
            state="readonly",
            values=("full_page", "pdf_aware_layout_regions", "layout_regions", "default"),
            width=22,
        )
        mode.grid(row=1, column=3, sticky="ew", padx=(0, 10))

        ttk.Label(docling_options, text="Qualitaet").grid(row=0, column=4, sticky="w", pady=(0, 4))
        quality = ttk.Combobox(
            docling_options,
            textvariable=self.quality_var,
            state="readonly",
            values=("fast", "balanced", "high", "max"),
            width=12,
        )
        quality.grid(row=1, column=4, sticky="ew", padx=(0, 10))

        ttk.Label(docling_options, text="Sprache").grid(row=0, column=5, sticky="w", pady=(0, 4))
        ttk.Entry(docling_options, textvariable=self.ocr_lang_var, width=10).grid(row=1, column=5, sticky="ew")

        ttk.Label(docling_options, text="Tabellen").grid(row=2, column=4, sticky="w", pady=(8, 4))
        tables = ttk.Combobox(
            docling_options,
            textvariable=self.table_mode_var,
            state="readonly",
            values=("accurate", "fast", "off"),
            width=12,
        )
        tables.grid(row=3, column=4, sticky="ew", padx=(0, 10))

        ttk.Checkbutton(docling_options, text="Zellen abgleichen", variable=self.table_cell_matching_var).grid(row=3, column=5, sticky="w")
        ttk.Checkbutton(docling_options, text="Bilder extrahieren", variable=self.extract_pictures_var).grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Checkbutton(docling_options, text="Bildtexte per VLM", variable=self.describe_pictures_var).grid(row=2, column=1, sticky="w", pady=(8, 0))
        ttk.Checkbutton(docling_options, text="Diagramme extrahieren", variable=self.chart_extraction_var).grid(row=2, column=2, sticky="w", pady=(8, 0))

        ttk.Label(docling_options, text="LM Studio URL").grid(row=4, column=0, sticky="w", pady=(10, 4))
        ttk.Entry(docling_options, textvariable=self.lmstudio_base_url_var).grid(row=5, column=0, columnspan=2, sticky="ew", padx=(0, 10))
        ttk.Label(docling_options, text="LM Studio Modell").grid(row=4, column=2, sticky="w", pady=(10, 4))
        ttk.Entry(docling_options, textvariable=self.lmstudio_model_var).grid(row=5, column=2, columnspan=2, sticky="ew", padx=(0, 10))
        ttk.Label(docling_options, text="Max Tokens").grid(row=4, column=4, sticky="w", pady=(10, 4))
        ttk.Entry(docling_options, textvariable=self.lmstudio_max_tokens_var, width=10).grid(row=5, column=4, sticky="ew", padx=(0, 10))
        ttk.Label(docling_options, text="LM Tabellen").grid(row=4, column=5, sticky="w", pady=(10, 4))
        lmstudio_tables = ttk.Combobox(
            docling_options,
            textvariable=self.lmstudio_table_format_var,
            state="readonly",
            values=("tabs", "html", "markdown"),
            width=12,
        )
        lmstudio_tables.grid(row=5, column=5, sticky="ew")

        ttk.Label(docling_options, text="MinerU Backend").grid(row=6, column=0, sticky="w", pady=(10, 4))
        mineru_backend = ttk.Combobox(
            docling_options,
            textvariable=self.mineru_backend_var,
            state="readonly",
            values=("pipeline", "hybrid-engine", "vlm-engine", "hybrid-http-client", "vlm-http-client"),
            width=18,
        )
        mineru_backend.grid(row=7, column=0, sticky="ew", padx=(0, 10))
        ttk.Label(docling_options, text="MinerU Methode").grid(row=6, column=1, sticky="w", pady=(10, 4))
        mineru_method = ttk.Combobox(
            docling_options,
            textvariable=self.mineru_method_var,
            state="readonly",
            values=("auto", "ocr", "txt"),
            width=12,
        )
        mineru_method.grid(row=7, column=1, sticky="ew", padx=(0, 10))
        ttk.Label(docling_options, text="MinerU Sprache").grid(row=6, column=2, sticky="w", pady=(10, 4))
        ttk.Entry(docling_options, textvariable=self.mineru_lang_var).grid(row=7, column=2, sticky="ew", padx=(0, 10))
        ttk.Label(docling_options, text="MinerU API URL").grid(row=6, column=3, sticky="w", pady=(10, 4))
        ttk.Entry(docling_options, textvariable=self.mineru_api_url_var).grid(row=7, column=3, columnspan=2, sticky="ew", padx=(0, 10))
        ttk.Checkbutton(docling_options, text="MinerU Tabellen", variable=self.mineru_table_var).grid(row=8, column=0, sticky="w", pady=(8, 0))
        ttk.Checkbutton(docling_options, text="MinerU Formeln", variable=self.mineru_formula_var).grid(row=8, column=1, sticky="w", pady=(8, 0))
        ttk.Checkbutton(docling_options, text="MinerU Bildanalyse", variable=self.mineru_image_analysis_var).grid(row=8, column=2, sticky="w", pady=(8, 0))
        ttk.Checkbutton(docling_options, text="Docling Ueberschriften", variable=self.heading_hierarchy_var).grid(row=8, column=3, sticky="w", pady=(8, 0))
        ttk.Checkbutton(docling_options, text="Scan-Bildtext", variable=self.traverse_picture_text_var).grid(row=8, column=4, sticky="w", pady=(8, 0))
        ttk.Checkbutton(docling_options, text="Unterstriche escapen", variable=self.escape_underscores_var).grid(row=8, column=5, sticky="w", pady=(8, 0))

        ttk.Label(docling_options, text="PDF Backend").grid(row=9, column=0, sticky="w", pady=(10, 4))
        pdf_backend = ttk.Combobox(
            docling_options,
            textvariable=self.pdf_backend_var,
            state="readonly",
            values=("docling_parse", "pypdfium2", "dlparse_v4", "dlparse_v2", "dlparse_v1", "threaded_docling_parse", "auto"),
            width=16,
        )
        pdf_backend.grid(row=10, column=0, sticky="ew", padx=(0, 10))

        ttk.Label(docling_options, text="Tabellenmodell").grid(row=9, column=1, sticky="w", pady=(10, 4))
        table_structure_model = ttk.Combobox(
            docling_options,
            textvariable=self.table_structure_model_var,
            state="readonly",
            values=("v1", "v2", "granite"),
            width=12,
        )
        table_structure_model.grid(row=10, column=1, sticky="ew", padx=(0, 10))

        ttk.Label(docling_options, text="OCR Scale").grid(row=9, column=2, sticky="w", pady=(10, 4))
        ttk.Entry(docling_options, textvariable=self.ocr_scale_var, width=10).grid(row=10, column=2, sticky="ew", padx=(0, 10))

        ttk.Label(docling_options, text="RapidOCR Score").grid(row=9, column=3, sticky="w", pady=(10, 4))
        ttk.Entry(docling_options, textvariable=self.rapidocr_text_score_var, width=10).grid(row=10, column=3, sticky="ew", padx=(0, 10))

        ttk.Label(docling_options, text="Tesseract PSM").grid(row=9, column=4, sticky="w", pady=(10, 4))
        ttk.Entry(docling_options, textvariable=self.tesseract_psm_var, width=10).grid(row=10, column=4, sticky="ew", padx=(0, 10))

        ttk.Checkbutton(docling_options, text="Backend-Text erzwingen", variable=self.force_backend_text_var).grid(row=11, column=0, sticky="w", pady=(8, 0))
        ttk.Checkbutton(docling_options, text="Verwaiste Textbloecke", variable=self.layout_create_orphan_clusters_var).grid(row=11, column=1, sticky="w", pady=(8, 0))
        ttk.Checkbutton(docling_options, text="Leere Layoutbereiche", variable=self.layout_keep_empty_clusters_var).grid(row=11, column=2, sticky="w", pady=(8, 0))
        ttk.Checkbutton(docling_options, text="Layout-Zellzuordnung aus", variable=self.layout_skip_cell_assignment_var).grid(row=11, column=3, columnspan=2, sticky="w", pady=(8, 0))

        ttk.Label(docling_options, text="DocStrange lokal").grid(row=12, column=0, sticky="w", pady=(10, 4))
        docstrange_processing = ttk.Combobox(
            docling_options,
            textvariable=self.docstrange_processing_var,
            state="readonly",
            values=("local_cpu", "local_gpu"),
            width=14,
        )
        docstrange_processing.grid(row=13, column=0, sticky="ew", padx=(0, 10))

        ttk.Label(docling_options, text="DocStrange Ausgabe").grid(row=12, column=1, sticky="w", pady=(10, 4))
        docstrange_output = ttk.Combobox(
            docling_options,
            textvariable=self.docstrange_output_var,
            state="readonly",
            values=("html", "markdown", "csv", "text", "json"),
            width=14,
        )
        docstrange_output.grid(row=13, column=1, sticky="ew", padx=(0, 10))

        log_frame = ttk.Frame(self, padding=(16, 6, 16, 8))
        log_frame.grid(row=4, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log = ScrolledText(log_frame, height=14, wrap="word", state="disabled")
        self.log.grid(row=0, column=0, sticky="nsew")

        footer = ttk.Frame(self, padding=(16, 4, 16, 14))
        footer.grid(row=5, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        ttk.Progressbar(footer, variable=self.progress_var, maximum=100).grid(row=0, column=0, sticky="ew", padx=(0, 12))
        ttk.Label(footer, textvariable=self.status_var, width=28).grid(row=0, column=1, sticky="e")

    def _choose_input(self) -> None:
        folder = filedialog.askdirectory(title="Dokumentenordner auswaehlen")
        if not folder:
            return
        self.input_var.set(folder)
        if not self.output_var.get():
            self.output_var.set(str(Path(folder) / "doclink_mds"))
        self._preview_count()

    def _choose_output(self) -> None:
        folder = filedialog.askdirectory(title="Markdown-Zielordner auswaehlen")
        if folder:
            self.output_var.set(folder)

    def _preview_count(self) -> None:
        input_dir = Path(self.input_var.get())
        output_dir = Path(self.output_var.get()) if self.output_var.get() else None
        if input_dir.exists():
            count = len(list_supported_files(input_dir, self.recursive_var.get(), output_dir))
            self.status_var.set(f"{count} Dateien gefunden")

    def _start(self) -> None:
        input_text = self.input_var.get().strip()
        output_text = self.output_var.get().strip()
        if not input_text:
            messagebox.showwarning("Doclink", "Bitte einen Dokumentenordner auswaehlen.")
            return
        if not output_text:
            output_text = str(Path(input_text) / "doclink_mds")
            self.output_var.set(output_text)

        input_dir = Path(input_text)
        output_dir = Path(output_text)
        if not input_dir.exists() or not input_dir.is_dir():
            messagebox.showerror("Doclink", "Der Dokumentenordner existiert nicht.")
            return

        self._clear_log()
        files = list_supported_files(input_dir, self.recursive_var.get(), output_dir)
        if not files:
            self.status_var.set("Keine passenden Dateien")
            self._append_log("Keine unterstuetzten Dateien gefunden.\n")
            return

        self.progress_var.set(0)
        self.status_var.set("Verarbeitung laeuft")
        self.start_button.configure(state="disabled")
        conversion_options = self._conversion_options()
        self._append_log(self._options_summary(conversion_options))

        self._worker = threading.Thread(
            target=self._run_conversion,
            args=(input_dir, output_dir, len(files), conversion_options),
            daemon=True,
        )
        self._worker.start()

    def _run_conversion(self, input_dir: Path, output_dir: Path, total: int, options: ConversionOptions) -> None:
        processed = 0

        def progress(result: ConversionResult) -> None:
            nonlocal processed
            processed += 1
            self._events.put(("result", (processed, total, result)))

        try:
            results = convert_folder(
                input_dir,
                output_dir,
                recursive=self.recursive_var.get(),
                overwrite=self.overwrite_var.get(),
                options=options,
                progress=progress,
            )
            self._events.put(("done", results))
        except Exception as exc:
            self._events.put(("error", exc))

    def _drain_events(self) -> None:
        try:
            while True:
                event, payload = self._events.get_nowait()
                if event == "result":
                    processed, total, result = payload  # type: ignore[misc]
                    percent = int(processed / total * 100)
                    self.progress_var.set(percent)
                    target = result.target.name if result.target else "-"
                    self._append_log(f"[{result.status}] {result.source.name} -> {target} ({result.message})\n")
                    self.status_var.set(f"{processed}/{total} verarbeitet")
                elif event == "done":
                    results = payload  # type: ignore[assignment]
                    created = sum(result.status == "created" for result in results)  # type: ignore[attr-defined]
                    skipped = sum(result.status == "skipped" for result in results)  # type: ignore[attr-defined]
                    failed = sum(result.status == "failed" for result in results)  # type: ignore[attr-defined]
                    self.progress_var.set(100)
                    self.status_var.set(f"{created} erstellt, {failed} Fehler")
                    self._append_log(f"\nFertig. Erstellt: {created}, uebersprungen: {skipped}, Fehler: {failed}\n")
                    self.start_button.configure(state="normal")
                    if failed:
                        messagebox.showwarning("Doclink", "Fertig, aber einige Dateien konnten nicht verarbeitet werden.")
                    else:
                        messagebox.showinfo("Doclink", "Markdown-Dateien wurden erstellt.")
                elif event == "error":
                    exc = payload
                    self.status_var.set("Fehler")
                    self._append_log(f"\nFehler: {exc}\n")
                    self.start_button.configure(state="normal")
                    messagebox.showerror("Doclink", str(exc))
        except queue.Empty:
            pass
        self.after(100, self._drain_events)

    def _conversion_options(self) -> ConversionOptions:
        ocr_lang = self.ocr_lang_var.get().strip() or "de"
        tesseract_langs = tuple(_tesseract_langs(ocr_lang))
        easyocr_langs = tuple(lang.strip() for lang in ocr_lang.replace(";", ",").split(",") if lang.strip()) or ("de", "en")

        return ConversionOptions(
            markdown_engine=self.markdown_engine_var.get(),
            accelerator=self.accelerator_var.get(),
            pdf_backend=self.pdf_backend_var.get(),
            ocr_engine=self.ocr_engine_var.get(),
            ocr_mode=self.ocr_mode_var.get(),
            quality=self.quality_var.get(),
            ocr_scale=_float_or_none(self.ocr_scale_var.get()),
            ocr_lang=ocr_lang.split(",")[0].strip(),
            rapidocr_text_score=_float_or_none(self.rapidocr_text_score_var.get()),
            tesseract_psm=_int_or_none(self.tesseract_psm_var.get()),
            easyocr_langs=easyocr_langs,
            tesseract_langs=tesseract_langs,
            table_mode=self.table_mode_var.get(),
            table_structure_model=self.table_structure_model_var.get(),
            table_cell_matching=self.table_cell_matching_var.get(),
            force_backend_text=self.force_backend_text_var.get(),
            layout_create_orphan_clusters=self.layout_create_orphan_clusters_var.get(),
            layout_keep_empty_clusters=self.layout_keep_empty_clusters_var.get(),
            layout_skip_cell_assignment=self.layout_skip_cell_assignment_var.get(),
            extract_pictures=self.extract_pictures_var.get(),
            describe_pictures=self.describe_pictures_var.get(),
            chart_extraction=self.chart_extraction_var.get(),
            heading_hierarchy=self.heading_hierarchy_var.get(),
            traverse_picture_text=self.traverse_picture_text_var.get(),
            escape_underscores=self.escape_underscores_var.get(),
            lmstudio_base_url=self.lmstudio_base_url_var.get().strip() or "http://localhost:1234/v1",
            lmstudio_model=self.lmstudio_model_var.get().strip(),
            lmstudio_max_tokens=_int_or_default(self.lmstudio_max_tokens_var.get(), 4096),
            lmstudio_table_format=self.lmstudio_table_format_var.get(),
            mineru_backend=self.mineru_backend_var.get(),
            mineru_method=self.mineru_method_var.get(),
            mineru_lang=self.mineru_lang_var.get().strip(),
            mineru_table=self.mineru_table_var.get(),
            mineru_formula=self.mineru_formula_var.get(),
            mineru_image_analysis=self.mineru_image_analysis_var.get(),
            mineru_api_url=self.mineru_api_url_var.get().strip(),
            docstrange_processing=self.docstrange_processing_var.get(),
            docstrange_output=self.docstrange_output_var.get(),
        )

    def _options_summary(self, options: ConversionOptions) -> str:
        picture_mode = "an" if options.extract_pictures else "aus"
        vlm_mode = "an" if options.describe_pictures else "aus"
        chart_mode = "an" if options.chart_extraction else "aus"
        return (
            "Optionen: "
            f"Markdown={options.markdown_engine}, Beschleunigung={options.accelerator}, "
            f"PDF={options.pdf_backend}, Engine={options.ocr_engine}, Modus={options.ocr_mode}, "
            f"Qualitaet={options.quality}, OCR-Scale={options.ocr_scale or 'auto'}, "
            f"Sprache={options.ocr_lang}, Tabellen={options.table_mode}/{options.table_structure_model}, "
            f"Zellen={'an' if options.table_cell_matching else 'aus'}, "
            f"RapidOCR-Score={options.rapidocr_text_score or 'auto'}, "
            f"Bilder={picture_mode}, VLM-Bildtext={vlm_mode}, Diagramme={chart_mode}, "
            f"LM Studio={options.lmstudio_base_url}, LM-Tabellen={options.lmstudio_table_format}, "
            f"MinerU={options.mineru_backend}/{options.mineru_method}, "
            f"DocStrange={options.docstrange_processing}/{options.docstrange_output}\n\n"
        )

    def _append_log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _open_output(self) -> None:
        output_text = self.output_var.get().strip()
        if not output_text:
            return
        output_dir = Path(output_text)
        output_dir.mkdir(parents=True, exist_ok=True)

        if sys.platform.startswith("win"):
            os.startfile(output_dir)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(output_dir)])
        else:
            subprocess.Popen(["xdg-open", str(output_dir)])


def main() -> None:
    app = DoclinkApp()
    app.mainloop()


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
        "french": "fra",
        "it": "ita",
        "ita": "ita",
    }
    langs = []
    for item in value.replace(";", ",").split(","):
        token = item.strip().lower()
        if token:
            langs.append(aliases.get(token, token))
    return langs or ["deu", "eng"]


def _float_or_none(value: str) -> float | None:
    value = value.strip().replace(",", ".")
    if not value:
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    return parsed if parsed > 0 else None


def _int_or_none(value: str) -> int | None:
    value = value.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _int_or_default(value: str, default: int) -> int:
    try:
        return int(value)
    except ValueError:
        return default


if __name__ == "__main__":
    main()
