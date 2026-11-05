# Zuordnung Kotlin → Python

Quelle: `SHS-maker/Barcode-Checker`, Branch `main`, GitHub-Commit
`d6daa3807b0a7d997bc3f9e0d3e0b056bba1cfd8`.
Lokale Ausgangskopie: Commit `716bf0f7534f666568f26884915a26d02377f9a2`.
Die lokale Kopie wurde nur gelesen. Alle drei Kotlin-Dateien des Ausgangsprojekts
wurden berücksichtigt. Die SHA-256-Prüfsummen der lokalen Quelldateien stehen in
`source_manifest.json`.

| Kotlin | Python |
|---|---|
| `MainActivity.ScanState`, `barcode1` | `core.ScanState`, `core.ScanSession` |
| `onCreate` | `AndroidBarcodeChecker.start` |
| `onResume`, `onWindowFocusChanged` | `resume`, `WindowFocus.onWindowFocusChanged` |
| `onDestroy` | `stop` |
| `enableFullscreen` | `fullscreen` (API 30+ und älter) |
| `applySettings` | `apply_settings` |
| `setupScannerInput` | `ScannerKeys`, `ScannerText`, natives EditText |
| `showManualEntryDialog` | `open_manual` |
| `consumeScan` | `consume`, `core.ScanSession.consume` |
| `barcodesMatch` | `core.barcodes_match` |
| `matchesWithOneExtraZero` | `core.matches_with_one_extra_zero` |
| `highlightDifferences` | `consume`, `core.differing_indices` |
| `differingIndices` | `core.differing_indices` (gleiches LCS/Tie-Breaking) |
| `withDiffHighlight` | `highlight`, `core.highlight_ranges` |
| `showResult`, `vibrate` | `show_result` |
| `resetAll`, Handler/Runnable | `reset`, nativer Handler und `Runnable` |
| `Settings` | `settings.Settings`, `AndroidSettingsStore` |
| `SettingsActivity.onCreate`, `bindSwitch` | `open_settings`, `Checked` |
| `SettingsActivity.onPause` | `save_auto_reset`, `pause`, `modal_dismissed` |

Die XML-Oberflächen und -Farben sind in Python mit nativen Android-Widgets
nachgebaut. Statt einer zweiten Activity gibt es einen scrollbaren nativen
Einstellungsdialog. Dessen Verhalten und gespeicherte Schlüssel entsprechen dem
Original. Rückkehr aus Dialogen/Hintergrund stellt den Scannerfokus wieder her.

Die neue Paketkennung und der App-Name trennen die Installation vom Original.
Ein Launcher-Symbol der Build-Toolchain ersetzt das ursprüngliche XML-Symbol.
Es werden keine Dateien oder Einstellungen der Originalinstallation migriert.
Ressourcen, private Gerätepfade, Gradle-Binärdateien und lokale Build-Caches des
Kotlin-Projekts sind nicht Teil dieses neuen Python-Repositories.

Python vergleicht Unicode-Codepunkte, Kotlin UTF-16-Codeeinheiten. Für die bei
Barcodes üblichen ASCII-Zeichen ist das Ergebnis identisch. Für die native
Zeichenmarkierung werden Python-Indizes in UTF-16-Offsets umgerechnet, damit
auch Zeichen außerhalb der BMP korrekte Android-Span-Grenzen erhalten. Bei
mehrdeutigen LCS-Ausrichtungen mit solchen Sonderzeichen kann sich die Auswahl
der Markierung gegenüber Kotlin unterscheiden.

Der TextWatcher verarbeitet wie im Original den ersten durch CR/LF beendeten
Code und leert anschließend den Puffer. Mehrere Barcodes in einem einzelnen
eingefügten Textblock werden nicht als Batch verarbeitet.

Die tatsächlich ausgeführten Vibrationszeiten wurden übernommen; der alte
Kotlin-Kommentar „dreimal lang“ widerspricht der dortigen Implementierung und
wurde nicht als Spezifikation verwendet.
