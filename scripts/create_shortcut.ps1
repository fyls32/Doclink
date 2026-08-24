$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Doclink.lnk"
$targetPath = Join-Path $root "run_doclink_app.bat"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetPath
$shortcut.WorkingDirectory = $root
$shortcut.Description = "Doclink Markdown-Erzeuger"
$shortcut.Save()

Write-Host "Desktop-Verknuepfung erstellt: $shortcutPath"
