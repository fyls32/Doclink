# Doclink

Kleine Windows-taugliche Tkinter-App, die einen Dokumentenordner mit Docling ausliest und Markdown-Dateien erstellt.

## Start unter Windows

1. Python 3.11 oder neuer installieren.
2. `install_windows.bat` doppelklicken.
3. Danach `run_doclink_app.bat` starten.

Die Markdown-Dateien landen standardmaessig im Unterordner `doclink_mds` des ausgewaehlten Dokumentenordners. Bei gescannten PDFs nutzt Doclink OCR; der erste Lauf kann deshalb mehrere Minuten dauern.

## Unterstuetzte Dateien

Doclink verarbeitet aktuell:

- `.pdf`
- `.doc` / `.xls` / `.ppt` mit LibreOffice
- `.docx`
- `.pptx`
- `.xlsx`
- `.odt` / `.ods` / `.odp`
- `.epub`
- `.png` / `.jpg` / `.tiff` / `.bmp` / `.webp`
- `.html` / `.htm`
- `.txt` / `.log`
- `.csv`
- `.json`
- `.xml`
- `.rtf`
- `.md`

## Kommandozeile

```bat
.venv\Scripts\python.exe -m doclink.cli C:\Pfad\zu\Dokumenten -o C:\Pfad\zu\Markdown
```

Ohne `-o` schreibt Doclink in `doclink_mds`.

Hinweis: Der erste Lauf kann deutlich laenger dauern, weil Docling und OCR Modelle vorbereiten. OCR nutzt standardmaessig Deutsch. Fuer andere Sprachen kann vor dem Start `DOCLINK_OCR_LANG` gesetzt werden, z. B. `set DOCLINK_OCR_LANG=en`. Wenn sehr alte Office-Dateien (`.doc`, `.xls`, `.ppt`) verarbeitet werden sollen, sollte LibreOffice installiert sein.

## EXE oder Installer bauen

Auf Windows:

```bat
build_windows_exe.bat
```

Das erzeugt `dist\Doclink\Doclink.exe`. Mit Inno Setup kann danach `installer\Doclink.iss` geoeffnet und ein klassischer Windows-Installer gebaut werden.
