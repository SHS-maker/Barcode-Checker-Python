# Android-Geräteprüfung

Diese Punkte sind vor Produktiveinsatz auf dem tatsächlichen Scanner zu prüfen.
Die Liste dokumentiert ausstehende Geräteprüfungen, keine bereits erfolgte Freigabe.

- APK lässt sich zusätzlich zur Kotlin-App installieren; beide starten getrennt.
- Hochformat/Vollbild, Zahnrad und skalierte Barcodefelder sind lesbar.
- HID-Eingabe mit Enter, Numpad-Enter und CR/LF-Abschluss verarbeitet zwei Scans.
- Scannen öffnet keine Bildschirmtastatur; leere Scans verschieben keinen Zustand.
- Exakte Codes ergeben CORRECT; unterschiedliche Codes bei deaktivierten
  Toleranzen ergeben INCORRECT. Groß-/Kleinschreibung bleibt relevant.
- Beide Toleranzschalter getrennt testen: `123`/`X123Y` und `123`/`1023`.
- `12345`/`12X345`: Bei deaktivierten Toleranzen nur `X` markieren.
- Nach Ergebnis weitere Scans ignorieren; RESET startet wieder bei Barcode 1.
- Manuelle Eingabe für beide Felder testen; Abbrechen und Android-Zurück geben
  den Fokus an den Scanner zurück. Beim Ergebnis keine Eingabe öffnen.
- Alle acht Schalter ändern, Dialog schließen, App neu starten: Werte bleiben.
- Die beiden Schaltflächen lassen sich unabhängig ausblenden.
- Auto-Reset mit 0, 1, 5 und 60 Sekunden; Werte außerhalb 0–60 werden begrenzt.
- Manueller Reset entfernt den alten Timer: Er darf ein neues Scanpaar später
  nicht zurücksetzen. Ein Timer darf bei offenem Einstellungsdialog ablaufen.
- CORRECT: ACK/200 ms und ein 120-ms-Vibrationsimpuls.
- INCORRECT: NACK/400 ms und zwei 150-ms-Impulse mit 100-ms-Pause.
- Ton/Vibration aus, ohne Vibrator sowie Stummschaltung testen.
- Hintergrund/Fokusverlust, Benachrichtigungsleiste und Rückkehr: Vollbild und
  Scannerfokus funktionieren weiter. Prozessneustart beginnt mit leerem Scanpaar.
- App-Schließen entfernt Timer und gibt Audioressourcen frei.

Bei Fehlern `adb logcat` auf Python-/Android-Ausnahmen prüfen. Sensible
Barcodewerte nicht ungeprüft in öffentliche Fehlerberichte aufnehmen.
