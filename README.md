# Barcode Checker Python – Android

Python-Port der Android-App [SHS-maker/Barcode-Checker](https://github.com/SHS-maker/Barcode-Checker).
Das Kotlin-Projekt bleibt unverändert. Diese eigenständige Android-App übernimmt
die vollständige Funktionalität der drei Kotlin-Quelldateien.

## Benutzung

1. Den integrierten Scanner (z. B. CipherLAB RS38) auf **Tastatur-/HID-Modus** mit
   **Enter**, **CR** oder **LF** als Abschluss konfigurieren.
2. Barcode 1 scannen, anschließend Barcode 2.
3. Die App zeigt **CORRECT** in Grün oder **INCORRECT** in Rot.
4. **RESET** startet ein neues Paar. Weitere Scans werden bis zum Reset ignoriert.
5. Beschädigte Barcodes lassen sich über **Manuelle Eingabe** eingeben.

Das Zahnrad öffnet alle Einstellungen. Schalteränderungen werden sofort in
Androids SharedPreferences gespeichert; die Reset-Sekunden beim Schließen des
Dialogs oder beim Wechsel in den Hintergrund. Die Scanner-Eingabe öffnet keine
Bildschirmtastatur. Die manuelle Eingabe und das Sekundenfeld dürfen sie öffnen.

## Übernommene Funktionen

| Funktion | Verhalten wie im Kotlin-Projekt |
|---|---|
| Scan-Ablauf | Zwei Scans; Ergebnis bis zum manuellen/automatischen Reset halten |
| Vergleich | Exakt und unter Beachtung der Groß-/Kleinschreibung |
| Teilübereinstimmung | Optional reicht ein vollständig im anderen enthaltener Code |
| Zusätzliche Null | Optional eine einzelne zusätzliche `0` an beliebiger Position |
| Markierung | Längste gemeinsame Teilfolge (LCS); nur abweichende Zeichen rot/fett |
| Ton | Android ACK 200 ms / NACK 400 ms |
| Vibration | 120 ms bei CORRECT / 150 ms, 100 ms Pause, 150 ms bei INCORRECT |
| Farbe | Ergebnisfeld oder optional ganzer Bildschirm grün/rot |
| Schaltflächen | RESET und manuelle Eingabe separat ein-/ausblendbar |
| Automatischer Reset | 0 bis 60 Sekunden, 0 = nur manuell |
| Darstellung | Hochformat, Vollbild, deutsche Beschriftungen, adaptive Barcode-Schriftgröße |

Alle acht Schalter sind wie im Original standardmäßig eingeschaltet. Der
automatische Reset ist standardmäßig ausgeschaltet. Sind beide Toleranzen aus,
zählt nur exakte Übereinstimmung. Enthaltene Leerzeichen gehören zum Code;
Leerraum am Anfang/Ende wird entfernt. CR/LF schließen eine Scanner-Eingabe ab.

## APK über GitHub bauen

Unter **Actions → Android-APK bauen** wird bei einem Push nach `main` automatisch
eine Debug-APK gebaut. Alternativ dort **Run workflow** wählen. Nach erfolgreichem
Build steht sie unter **Artifacts → Barcode-Checker-Python-APK** zum Download.
Das Artefakt ist ein ZIP; die enthaltene APK auf das Android-Gerät übertragen
und installieren. Der erste Build lädt Python, SDK und NDK und kann länger dauern.

- Android **8.0 / API 26** oder neuer.
- ARM64 und ARMv7 werden in einer APK unterstützt.
- Eigenständige Paketkennung: **`com.melber.barcodecheckerpython`**.
- Das Original **`com.melber.barcodecmm`** kann parallel installiert bleiben.
- Einstellungen werden in der neuen App separat gespeichert und nicht aus der
  Original-App übernommen. Die Python-Version verändert keine Original-App-Daten.
- Die Debug-APK ist für direkte Installation und Erprobung vorgesehen. Eine
  Veröffentlichung im Play Store erfordert einen eigenen Release-Prozess.

## Lokal bauen (Linux, empfohlen Ubuntu 24.04)

Benötigt werden Python 3.12, JDK 17 und die Systempakete des Build-Workflows.

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-build.txt
buildozer -v android debug
```

SDK-Lizenzen beim ersten lokalen Build lesen und bestätigen. Die fertige APK
liegt unter `bin/`. Bei angeschlossenem Gerät und eingerichtetem USB-Debugging:

```sh
buildozer android deploy run
```

Die App ist ausschließlich für Android vorgesehen. `python main.py` auf einem
Desktop ist kein unterstützter App-Start. Die unabhängigen Logiktests laufen dort
ohne Kivy, Android-SDK oder zusätzliche Python-Pakete:

```sh
python3 -m unittest discover -s tests -v
```

## Umsetzung und Prüfstand

- `barcode_checker/core.py`: Scan-Zustände, Vergleich und LCS-Markierung.
- `barcode_checker/settings.py`: Alle Einstellungen und SharedPreferences.
- `barcode_checker/android_app.py`: Native Oberfläche, HID-Eingabe, Dialoge,
  Handler-Timer, Vollbild, Ton und Vibration – vollständig in Python.
- `main.py`: Android-Lebenszyklus über Kivy/python-for-android.
- `buildozer.spec`: APK-Paketierung mit festgelegter Toolchain.
- `.github/workflows/`: Logiktests und Android-Build.

Die Oberfläche verwendet über PyJNIus die nativen Android-Widgets, damit der
Hardware-Scanner wie im Original in ein fokussiertes EditText-Feld schreiben
kann. Kivy/SDL liefert den Python-Android-Start und den Lebenszyklus; die native
Oberfläche liegt darüber. Es gibt keine eigenen Java-/Kotlin-Quelldateien.
Die Android-Laufzeit der verwendeten Werkzeuge enthält weiterhin Java/C-Code.

Die 16 Logiktests prüfen Vergleichstoleranzen, Scan-Zustände, Reset,
SharedPreferences-Persistenz, Eingabeterminierung und Markierungen, einschließlich
einer unabhängigen LCS-Prüfung über 961 Codepaare. Sämtliche Python-Dateien wurden
auf Syntax geprüft. **Ein erfolgreicher APK-Build und ein Test auf dem RS38 sind
zusätzliche Prüfungen; bestandene Logiktests ersetzen sie nicht.** Der lokale
Portierungsrechner hatte weder JDK noch Android-SDK/Emulator. Die Geräteprüfliste
steht in [docs/ANDROID_TESTPLAN.md](docs/ANDROID_TESTPLAN.md).

Zuordnung aller Kotlin-Funktionen und Abweichungen der Plattformumsetzung:
[docs/PORTIERUNG.md](docs/PORTIERUNG.md).

Toolchain-Dokumentation: [Kivy Android-Paketierung](https://kivy.org/doc/stable/guide/packaging-android.html),
[Buildozer Installation](https://buildozer.readthedocs.io/en/latest/installation/),
[python-for-android v2026.05.09](https://github.com/kivy/python-for-android/releases/tag/v2026.05.09).
