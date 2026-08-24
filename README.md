# Doclink

Kleine Windows-taugliche Tkinter-App, die einen Dokumentenordner mit Docling ausliest und Markdown-Dateien erstellt.

## Start unter Windows

1. Python 3.11 oder neuer installieren.
2. `install_windows.bat` doppelklicken.
3. Danach `run_doclink_app.bat` starten.

Die Markdown-Dateien landen standardmaessig im Unterordner `doclink_mds` des ausgewaehlten Dokumentenordners. Bei gescannten PDFs nutzt Doclink OCR; der erste Lauf kann deshalb mehrere Minuten dauern.

## OCR- und Qualitaetsoptionen

In der App koennen mehrere Docling-Optionen umgeschaltet werden:

- Markdown-Modus: `docling`, `lmstudio` oder `mineru`
- Beschleunigung: `auto`, `cpu` oder `cuda`
- PDF Backend: `docling_parse`, `pypdfium2`, `dlparse_v4`, `dlparse_v2`, `dlparse_v1`, `threaded_docling_parse`, `auto`
- OCR Engine: `rapidocr`, `tesseract_cli`, `easyocr`, `auto`, `none`
- OCR Modus: `full_page`, `pdf_aware_layout_regions`, `layout_regions`, `default`
- Qualitaet: `fast`, `balanced`, `high`, `max`
- OCR Scale: leer = Qualitaetsvorgabe; sonst direkter Render-Faktor fuer OCR, z. B. `2.5`, `3`, `4`
- RapidOCR Score: leer = Standard; niedriger, z. B. `0.3`, erkennt mehr Text, kann aber mehr Fehler erzeugen
- Tesseract PSM: leer = Standard; fuer Tesseract z. B. `3`, `6` oder `11`
- Tabellenmodus: `accurate`, `fast` oder `off`
- Tabellenmodell: `v1`, `v2` oder `granite`, falls deine Docling-Version das Modell unterstuetzt
- Backend-Text erzwingen: vorhandenen PDF-Text bevorzugen, bei reinen Scans meist unwichtig
- Verwaiste Textbloecke: Text behalten, der keinem Layoutbereich sicher zugeordnet wird
- Leere Layoutbereiche: leere Layout-Cluster behalten; kann bei Formularen helfen, kann aber auch mehr Rauschen erzeugen
- Layout-Zellzuordnung aus: Zellen im Layout nicht automatisch zuordnen; experimentell fuer schwierige Tabellen
- Bilder extrahieren: Bilder im Markdown einbetten
- Bildtexte per VLM: sichtbaren Text/Bildinhalt als Text anhaengen
- Diagramme extrahieren
- Docling Ueberschriften: Heading-Level aus Schriftgroesse, Nummerierung und Font-Stil ableiten
- Scan-Bildtext: OCR-Text innerhalb von gescannten Seitenbildern beim Markdown-Export mitnehmen
- Unterstriche escapen: Unterstriche fuer Markdown schuetzen; standardmaessig aus, damit Text natuerlicher bleibt

Empfehlung fuer gescannte PDFs: `rapidocr`, `full_page`, Qualitaet `high`, Tabellen `accurate`, Tabellenmodell `v1`, Zellen abgleichen zuerst `aus` testen. Wenn viel Text fehlt, probiere `OCR Scale` nacheinander mit `2.5`, `3`, `4` und `5`; der beste Wert haengt stark vom Scan ab. Wenn RapidOCR Text uebersieht, probiere `RapidOCR Score=0.3`.

Wenn Tabellen/Formulare schlecht sind, teste diese Reihenfolge:

```text
1. Zellen abgleichen: aus
2. Tabellenmodell: v2
3. PDF Backend: pypdfium2
4. OCR Scale: 3 oder 4 statt nur Qualitaet max
5. Tabellenmodell: granite nur mit Vision-Installation/GPU oder viel Geduld auf CPU
```

`threaded_docling_parse` ist eher fuer Geschwindigkeit gedacht und nicht die erste Wahl fuer schwierige Tabellen.

Wenn leere Tabellenzellen falsch aufgefuellt werden, ist `Zellen abgleichen: aus` meist besser als Tabellen komplett auszuschalten. `Tabellen: off` ist der letzte Ausweg; dann wird keine Markdown-Tabelle rekonstruiert, sondern der OCR-Text normal ausgegeben.

Bei NVIDIA-GPU kann `Beschleunigung: cuda` Docling-Layout/OCR/Tabellenmodelle beschleunigen, sofern deine Python/PyTorch-Installation CUDA nutzen kann. `auto` laesst Docling selbst entscheiden, `cpu` erzwingt CPU.

Wichtig fuer gescannte PDFs: `Scan-Bildtext` sollte eingeschaltet bleiben. Docling dokumentiert, dass `traverse_pictures=True` fuer Full-Page-OCR wichtig ist, weil OCR-Text sonst innerhalb eines Picture-Elements liegen kann.

Der Modus `lmstudio` nutzt deinen lokalen LM-Studio-Server. Starte in LM Studio den lokalen Server, lade ein Vision-Modell und nutze in der App standardmaessig:

```text
LM Studio URL: http://localhost:1234/v1
LM Studio Modell: leer lassen oder Modell-ID eintragen
LM Tabellen: tabs, html oder markdown
```

In diesem Modus rendert Doclink jede PDF-Seite als Bild und laesst das lokale Vision-Modell direkt Markdown erzeugen. Das ist oft besser fuer schwierige Tabellen, kann aber langsamer sein und haengt stark vom geladenen Modell ab.

Der LM-Studio-Prompt ist bewusst streng: Das Modell soll nur sichtbaren Text transkribieren, nichts ergaenzen, leere Tabellenzellen leer lassen und relative Textgroessen ueber Markdown-Ueberschriften bzw. sichtbare Formatierung abbilden. Mit `LM Tabellen` kannst du steuern, wie Tabellen und Formularraster ausgegeben werden:

- `tabs`: Tabellen/Formulare als TSV-Bloecke mit echten Tabulatoren; oft gut fuer Steuerformulare mit vielen leeren Zellen
- `html`: Tabellen/Formulare als HTML-Tabellen mit leeren `<td></td>` Zellen; oft gut fuer Nanonets-OCR2
- `markdown`: klassische Markdown-Pipe-Tabellen

Wenn ein LM-Studio-Modell bei `tabs` leer antwortet, versucht Doclink dieselbe Seite automatisch mit `html`, danach mit `markdown` und zuletzt mit einem einfachen Nanonets-aehnlichen OCR-Prompt. Dadurch bricht ein Dokument nicht sofort ab, nur weil ein Tabellenformat vom Modell nicht beantwortet wird.

Der Modus `mineru` nutzt die externe MinerU CLI. Installiere MinerU separat:

```bat
install_mineru_windows.bat
```

Empfohlener Start fuer lokale Scans:

```text
Markdown-Modus: mineru
MinerU Backend: pipeline
MinerU Methode: auto oder ocr
MinerU Tabellen: an
```

MinerU erzeugt eigene Markdown-Dateien in einem temporaeren Ausgabeordner; Doclink uebernimmt die groesste gefundene `.md` Datei.

Auf Windows setzt Doclink automatisch `HF_HUB_DISABLE_SYMLINKS=1`, damit Hugging Face Modell-Dateien kopiert statt Symlinks anzulegen. Das vermeidet `WinError 1314`, kann aber mehr Speicherplatz im Modellcache brauchen.

Tesseract ist optional und muss als Windows-Programm separat installiert werden, bevor `tesseract_cli` funktioniert. Wenn Windows `tesseract.exe` nicht findet, setze `TESSERACT_CMD` auf den vollen Pfad. RapidOCR ist der normale lokale Docling/OCR-Weg dieser App. EasyOCR wird ueber `install_windows.bat` als Python-Paket installiert.

Fuer den Schalter `Bildtexte per VLM` einmal ausfuehren:

```bat
install_vision_windows.bat
```

Das installiert zusaetzliche Vision-Abhaengigkeiten und kann deutlich laenger dauern.

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

LM Studio per CLI:

```bat
.venv\Scripts\python.exe -m doclink.cli C:\Pfad\zu\Dokumenten --markdown-engine lmstudio --lmstudio-base-url http://localhost:1234/v1
```

MinerU per CLI:

```bat
.venv\Scripts\python.exe -m doclink.cli C:\Pfad\zu\Dokumenten --markdown-engine mineru --mineru-backend pipeline --mineru-method auto
```

Ohne `-o` schreibt Doclink in `doclink_mds`.

Hinweis: Der erste Lauf kann deutlich laenger dauern, weil Docling und OCR Modelle vorbereiten. OCR nutzt standardmaessig Deutsch. Fuer andere Sprachen kann vor dem Start `DOCLINK_OCR_LANG` gesetzt werden, z. B. `set DOCLINK_OCR_LANG=en`. Wenn sehr alte Office-Dateien (`.doc`, `.xls`, `.ppt`) verarbeitet werden sollen, sollte LibreOffice installiert sein.

## EXE oder Installer bauen

Auf Windows:

```bat
build_windows_exe.bat
```

Das erzeugt `dist\Doclink\Doclink.exe`. Mit Inno Setup kann danach `installer\Doclink.iss` geoeffnet und ein klassischer Windows-Installer gebaut werden.
