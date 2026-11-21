# Untertitel

Jede Sendung erzeugt `subtitles.de.vtt` (WebVTT, für den Videoplayer und die Artikelseiten) und `subtitles.de.srt` (zum Herunterladen). Der Text ist genau der Text, der an die Sprachausgabe geht.

## Zeitbestimmung

1. **Abschnitte:** Jeder gesprochene Abschnitt (Begrüßung, Datum, jede Meldung, Abschluss) wird einzeln synthetisiert. Seine Länge ist aus der WAV-Datei exakt bekannt.
2. **Sätze:** `scripts/subtitle_alignment.py` sucht in der WAV-Datei jedes Abschnitts die Sprechpausen (Pegel in 10-ms-Schritten). Piper setzt nach jedem Satz eine feste Pause (`--sentence_silence 0.38`), eSpeak-NG macht am Satzende eine deutlich längere Pause als an Kommas. Für die n−1 Satzgrenzen eines Abschnitts werden die längsten Pausen in der richtigen Reihenfolge gewählt, bei ähnlich langen Pausen die, die der Schätzung nach Textanteil am nächsten liegt. Untertitel beginnen mit dem ersten gesprochenen Laut des Satzes und enden mit dem letzten.
3. **Innerhalb eines Satzes:** Ein Untertitel hat höchstens zwei Zeilen à 42 Zeichen und reicht nie über eine Satzgrenze. Wird ein langer Satz geteilt, schätzt die Zeitbestimmung die Trennstelle nach Zeichenanteil und legt sie auf eine Sprechpause (etwa an einem Komma), wenn eine innerhalb von 0,6 Sekunden liegt.
4. **Rückfall:** Findet die Analyse zu wenige Pausen oder ist die Audiodatei nicht lesbar, gilt die frühere Verteilung nach Zeichenanteil innerhalb des Abschnitts.

Es gibt keine Spracherkennung, kein zusätzliches Modell und keine Netzwerkzugriffe. Satzenden werden nicht nach Abkürzungen („z. B.“, „bzw.“), Ordnungszahlen („3. November“) oder vor kleingeschriebenen Wörtern getrennt.

## Genauigkeit

Gemessen am 21.11.2026 mit eSpeak-NG an Nachrichtentexten mit 2–4 Sätzen, Sätze wie bei Piper einzeln gesprochen und mit 0,38 s Pause verbunden (Sollwerte aus den Einzeldateien bekannt):

| Verfahren | größte Abweichung an Satzanfängen/-enden | Mittel |
| --- | --- | --- |
| bisher: Zeichenanteil über den ganzen Abschnitt | 1,06 s | 0,33 s |
| neu: Pausenanalyse | 0,04 s | 0,02 s |

Bei eSpeak-NG mit ganzem Abschnittstext (Rückfallstimme) wurden in allen Stichproben die Satzpausen (≈ 0,4 s) statt der Kommapausen (≈ 0,2 s) gewählt. Die Tests `tests/test_subtitle_alignment.py` prüfen beides; der eSpeak-Test läuft, wenn `espeak-ng` installiert ist.

Grenzen: Wortgenaue Zeiten liefern weder Piper noch eSpeak-NG direkt. Innerhalb sehr langer Sätze ohne Pause bleibt die Trennstelle eine Schätzung.
