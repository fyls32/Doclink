# Doclink

Kleine Windows-taugliche Tkinter-App, die einen Dokumentenordner ausliest und Markdown-Dateien erstellt.

## Start unter Windows

1. Python 3.11 oder neuer installieren.
2. `install_windows.bat` doppelklicken.
3. Danach `run_doclink_app.bat` starten.

Die Markdown-Dateien landen standardmaessig im Unterordner `doclink_mds` des ausgewaehlten Dokumentenordners.

## Unterstuetzte Dateien

Doclink verarbeitet aktuell:

- `.pdf`
- `.docx`
- `.pptx`
- `.xlsx`
- `.odt`
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

## EXE oder Installer bauen

Auf Windows:

```bat
build_windows_exe.bat
```

Das erzeugt `dist\Doclink\Doclink.exe`. Mit Inno Setup kann danach `installer\Doclink.iss` geoeffnet und ein klassischer Windows-Installer gebaut werden.
