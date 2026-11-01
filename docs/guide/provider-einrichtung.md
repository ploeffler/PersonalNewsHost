# Provider einrichten: Was muss ich nach der Auswahl tun?

Stand und Quellenprüfung: **01.11.2026**. Gilt für den Entwicklungsbranch nach v0.1.
Diese Anleitung wird als T323 vorgezogen; sie implementiert keine neuen Adapter.

## Was kann ich heute aktivieren?

| Auswahl | Status in PersonalNewsHost | Was du jetzt tun kannst |
|---|---|---|
| Mock, alle sechs Providerarten | verfügbar | Konfiguration und Routing ohne Konto testen |
| Piper / eSpeak, lokale Sprache | vorhandener Produktionsweg | Programm und Stimme installieren, lokal prüfen |
| 2D-Werbevideo | vorhandener Produktionsweg | Hostbild, Mundkalibrierung und lokale Stimme vorbereiten |
| sd-turbo + SadTalker, T900 | experimenteller CPU-Workflow | manuellen technischen Reel-Lauf mit seinen Eingaben starten |
| Ollama, llama.cpp, LocalAI | Adapter noch nicht implementiert | lokalen Dienst unabhängig vorbereiten und prüfen |
| ComfyUI, stable-diffusion.cpp | Adapter noch nicht implementiert | Bildlaufzeit und passendes Modell unabhängig vorbereiten |
| Docker Model Runner | optionale spätere Anbindung | Docker-Funktion und Modell unabhängig prüfen |
| Gemini, Groq, Mistral | Adapter noch nicht implementiert | API-Konto und Kontingent prüfen; keine Gratisgarantie |
| OpenAI, Anthropic, BFL, Runway | Adapter noch nicht implementiert | API-Zugang vorbereiten; noch keine PNH-Generierung |
| 3d-local / 3d-online | setup_required | Auswahl speicherbar; Renderadapter fehlt |

Ein laufender externer Dienst oder ein gültiger API-Key bedeutet noch nicht, dass
PersonalNewsHost ihn aufrufen kann. Der Verwaltungsreiter „Unterstützung“, sein
Schlüsselmanager und Verbindungstest sind mit T320–T322 geplant. Es gibt aktuell
keine entsprechende Schaltfläche. `adapter` akzeptiert hier ausschließlich
`mock`; ein Cloud-Endpoint in der Mock-Konfiguration wird nicht unterstützt.

## Gemeinsamer Ablauf

1. Aufgabe bestimmen: Textanalyse, Formulierung, Bild, Clip, Sprache oder Avatar.
   Ein Modell für Text kann nicht automatisch Bilder oder Videos erzeugen.
2. Integrationsstatus oben prüfen. Bei fehlendem Adapter endet die Einrichtung
   nach der unabhängigen Dienstprüfung mit **vorbereitet, noch nicht verbunden**.
3. Lokal: Betriebssystem, Architektur, RAM/VRAM, freien Modellplatz und Modelllizenz
   prüfen. Klein beginnen; keine feste Hardwaregarantie ohne konkretes Modell.
   Cloud: API-Projekt, Landverfügbarkeit, Modellzugang und aktuelle Bedingungen prüfen.
4. Endpoint und tatsächlich installierte/erlaubte Modell-ID notieren. Beispiele
   mit `MODELL_ID` sind Platzhalter und keine Modell-Empfehlung.
5. Zugangsdaten nur dem serverseitigen Dienst geben. Zuerst Erreichbarkeit und
   Modellliste prüfen, danach einen kurzen Funktionstest ausdrücklich auslösen.
   Modellabfragen sind keine Generierung; sie können trotzdem Authentifizierung
   oder Kontingent benötigen. Ein Testprompt ist kein garantierter Nullkostentest.
6. Erst mit implementiertem Adapter Aufgabe, Priorität und gleichartigen Fallback
   zuordnen. Bezahlt nur nach ausdrücklicher Aktivierung und positivem Budget.
   Erschöpftes Gratis-Kontingent darf keinen automatischen Tarifwechsel auslösen.
7. Ergebnis und tatsächliche Engine prüfen. Fehlende Verbindung, ungeklärte
   Abrechnung oder ungeeignete Fähigkeit halten den Anbieter deaktiviert.

## Mock: sofort ohne Konto ausprobieren

Vom Repository-Hauptordner aus, in der vorhandenen Projekt-Pythonumgebung:

```bash
python3 scripts/validate_config.py config.example.json
printf '%s\n' '{"text":"Lokaler Test ohne Netzwerk."}' | \
  python3 scripts/run_provider.py --config config.example.json --kind text_generation
```

Erwartung: JSON mit `provider_id`, `value` und `cached`. Wiederholen liefert einen
Cachetreffer. Bei anderen nichttextuellen Mockarten ist das Ergebnis eine
Testreferenz, keine Audio-/Videodatei. Für optionale Analyseaufgaben siehe
[Runtime-Konfiguration](provider-runtime.md). Mocks benötigen keinen API-Key.

## Lokale Textdienste vorbereiten

Die folgenden Diensttests werden außerhalb der PNH-Providerverwaltung ausgeführt.
Sie schalten in PersonalNewsHost nichts frei.

### Wenn du Ollama wählst

Installiere Ollama für dein Betriebssystem über die [offizielle Anleitung](https://docs.ollama.com/quickstart).
Wähle ein für deinen Rechner lizenziertes Modell und ersetze `MODELL_ID`:

```bash
ollama pull MODELL_ID
ollama list
curl --fail --max-time 10 http://127.0.0.1:11434/api/tags
```

Erwartung: Die Modellliste enthält genau die geladene ID. Erst ein bewusstes
`ollama run MODELL_ID` testet die Inferenz. Der lokale Dienst braucht normalerweise
keinen Cloud-Key; entfernte oder Cloud-Angebote gesondert prüfen. Bei Fehlern
Dienststart, Speicher und Modell-ID prüfen. In PNH bleibt Ollama bis zum Adapter
**nicht verbunden**. Quellen: [CLI](https://docs.ollama.com/cli),
[Modellliste](https://docs.ollama.com/api/tags).

### Wenn du llama.cpp wählst

Installiere eine passende Release-/Buildvariante, beschaffe ein kompatibles
GGUF-Modell mit geprüfter Lizenz und starte den Server zunächst auf Loopback:

```bash
llama-server -m /pfad/zum/modell.gguf --host 127.0.0.1 --port 8080
```

In einem zweiten Terminal: `curl --fail --max-time 10 http://127.0.0.1:8080/health`.
Erwartung: ein betriebsbereiter Server; während des Ladens noch keine Freigabe.
Modellpfad, Quantisierung und Speicher prüfen. Den lokalen Dienst nicht ungeprüft
öffentlich binden. PNH-Adapter fehlt. Quelle:
[offizieller Serververtrag](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md).

### Wenn du LocalAI wählst

Installiere LocalAI nach dem [offiziellen Einstieg](https://localai.io/docs/getting-started/).
Installiere danach ein Modell über die Galerie oder die dokumentierte CLI;
ein leerer Server ist kein eingerichteter Anbieter. Prüfe den gewählten Port:

```bash
curl --fail --max-time 10 http://127.0.0.1:8080/v1/models
```

Erwartung: die gewünschte Modell-ID erscheint. Bei aktivierter Authentifizierung
den Dienst mit seinem vorgesehenen Secret-Verfahren ansprechen. Backend und
Modalität müssen zum Modell passen; „OpenAI-kompatibel“ ist keine Garantie für
sämtliche Funktionen. PNH-Adapter fehlt. Quelle:
[Modelle einrichten](https://localai.io/docs/getting-started/models/).

## Lokale Bilder vorbereiten

### Wenn du ComfyUI wählst

Folge der [offiziellen Installation](https://docs.comfy.org/installation/manual_install)
für die CPU/GPU deines Rechners. Starte die Oberfläche, lade ein kompatibles
Modell und dessen benötigte Zusatzdateien in die vorgesehenen Modellordner und
führe einen kleinen Beispielworkflow aus. Erwartung: ein lokal erzeugtes Bild.
Bewahre Workflow und Modellversionen auf; ein erreichbarer Server ohne passende
Nodes und Modelle reicht nicht. Fehlende Nodes/Weights oder GPU-Speicher zuerst
im ComfyUI-Log klären. PNH kann derzeit keinen ComfyUI-Workflow absenden.

### Wenn du stable-diffusion.cpp wählst

Installiere den passenden Build und lade ein unterstütztes Modell samt den in
der Modellanleitung geforderten Encodern/VAE-Dateien. Prüfe `sd-cli --help`;
ein minimaler Aufruf für ein dazu passendes Einzeldateimodell lautet:

```bash
sd-cli -m /pfad/zum/modell.safetensors -p 'Ein neutrales Teststudio'
```

Erwartung: ein Bild im vom Programm gemeldeten Ausgabepfad. Nicht jedes Modell
funktioniert mit diesem Minimalaufruf; bei mehrteiligen Modellen gelten deren
zusätzliche Parameter. Ein universeller HTTP-Endpoint wird hier nicht behauptet.
PNH-Adapter fehlt. Quelle: [Projekt und Modell-/Buildanleitungen](https://github.com/leejet/stable-diffusion.cpp).

### Wenn du Docker Model Runner wählst

Prüfe zuerst die Unterstützung deiner Docker-Installation. Aktiviere die Funktion
in Docker Desktop oder installiere das dokumentierte Plugin für Docker Engine.
Danach `docker model version`, `docker model pull MODELL_ID` und bewusst
`docker model run MODELL_ID`. Erwartung: Modell geladen und lokaler Test möglich.
Docker Model Runner ist keine Voraussetzung für PNH. Host-TCP-Zugriff muss bei
Bedarf separat aktiviert werden; keinen universellen Port voraussetzen.
PNH-Adapter fehlt. Quelle: [Docker-Einrichtung](https://docs.docker.com/ai/model-runner/get-started/).

## Cloudanbieter vorbereiten

**Für alle folgenden Anbieter fehlt der PNH-Adapter.** Diese Schritte richten
lediglich den externen API-Zugang ein. Noch keine Schlüssel in PNH eingeben und
keinen Cloudanbieter in `config.json` als funktionsfähig aktivieren.

| Wenn du … wählst | Das musst du beim Anbieter tun | Modell, Verbindung und Kosten prüfen |
|---|---|---|
| OpenAI | Im API-Dashboard ein Projekt und einen API-Key erstellen; serverseitig als `OPENAI_API_KEY` bereitstellen. | Mit dem offiziellen SDK die zugänglichen Modelle abfragen, dann einen kurzen Test bewusst auslösen. API-Zugang und Abrechnung im Projekt prüfen. [Offizieller Quickstart](https://developers.openai.com/api/docs/quickstart). |
| Google Gemini | In Google AI Studio ein API-Projekt auswählen/anlegen und einen Key erstellen. `GEMINI_API_KEY` oder `GOOGLE_API_KEY` verwenden; bei beiden hat laut SDK-Dokumentation `GOOGLE_API_KEY` Vorrang. | Modellberechtigung und Konto-Kontingente prüfen. Ein generierender Quickstart ist ein separater Test. Gratis- und bezahlte Nutzung nicht gleichsetzen. [Keys und Einrichtung](https://ai.google.dev/gemini-api/docs/api-key). |
| Groq | In GroqCloud einen API-Key erstellen und serverseitig als `GROQ_API_KEY` geben. | Aktuell erlaubte Modelle und Limits im Konto prüfen; kurzen offiziellen SDK-Test bewusst auslösen. Kein automatischer Wechsel in einen bezahlten Tarif. [Quickstart](https://console.groq.com/docs/quickstart). |
| Mistral | Im Studio-/Adminbereich API-Key erstellen, erlaubtes Modell auswählen und dem offiziellen SDK geschützt übergeben. | API-Format, Modellzugang und Plan getrennt prüfen. Einen Test nach der offiziellen Anleitung ausführen, keine allgemeine Gratiszusage ableiten. [Studio-Einrichtung](https://docs.mistral.ai/studio), [erster Request](https://docs.mistral.ai/getting-started/quickstarts/developer/first-api-request). |
| Anthropic | In der Claude-API-Konsole einen passenden Workspace und API-Key einrichten. SDK-Key, Modellberechtigung und gegebenenfalls Workspace-Vorgaben setzen. | Der API-Dienst liegt unter `https://api.anthropic.com`; SDK-/API-Version gemäß aktueller Anleitung wählen. Erst Modellzugang, dann bewusst kurze Messages-Anfrage testen. [API-Einrichtung](https://platform.claude.com/docs/en/api/overview). |
| Black Forest Labs | Über die offizielle API-Dokumentation den Kontozugang und Schlüsselweg für den gewählten Bilddienst einrichten. | Aktuellen Modell-Endpoint, Authentifizierung und gegebenenfalls Result-Polling übernehmen; vor dem ersten Bild Preisgrundlage und Nutzungsrechte prüfen. Kein Textanbieter-Fallback. [API-Einstieg](https://docs.bfl.ai/quick_start/introduction), [Ergebnisabfrage](https://docs.bfl.ai/api-reference/utility/get-result). |
| Runway | Im Developerportal API-Zugang und Schlüssel einrichten; der offizielle Ablauf verwendet `RUNWAYML_API_SECRET`. | Verfügbares Modell, API-Version und erforderliche Credits prüfen. Ein Videoauftrag erzeugt einen Job; Status und Download müssen getrennt behandelt werden. Vor Upload und Generierung Umfang und Kosten freigeben. [API-Anleitung](https://docs.dev.runwayml.com/guides/using-the-api/). |

Die Variablennamen oben stammen aus Anbieter-SDKs beziehungsweise dokumentierten
Beispielen. Sie sind **keine bereits implementierten PNH-Adapteroptionen**.
Für Endpoints zunächst die Defaults des offiziellen SDK verwenden. Einen eigenen
Proxy, eine Region oder eine kompatible URL nur nach Prüfung von Authentifizierung,
Datenziel und tatsächlich unterstützten API-Routen einsetzen.

Vor jeder echten Aktivierung Modellrechte, Datennutzung/Training, Speicherfristen,
Region, Kontingente und aktuelle Preise im gewählten Konto prüfen. Diese Seite
bestätigt keine Datenschutz-/Tarifprüfung eines konkreten Kontos. Besonders bei
Bildern und Video werden auch Medien an den Anbieter übertragen. Ohne geklärte
Kosten bleibt der Dienst aus; ein Serverfehler ist keine Erlaubnis zum Tarifwechsel.

## Zugangsdaten bei Linux, Docker und Portainer

Für den späteren Adapterbetrieb ist folgendes Verfahren vorgesehen; der PNH-
Schlüsselmanager und ein allgemeiner Secret-Mount-Loader sind noch nicht gebaut:

- **Linux:** Secret im Dienstkontext über eine nur für den Dienst lesbare Datei
  oder einen Secret-Manager injizieren. Eine Variable im eigenen Terminal steht
  einem systemd-Dienst nicht automatisch zur Verfügung. Datei nicht im Repository
  ablegen. Nach Änderung Dienst kontrolliert neu starten.
- **Docker/Compose:** Secret serverseitig injizieren oder als schreibgeschützte
  Secretdatei mounten. Ein Mount wird nur wirksam, wenn der jeweilige Adapter diese
  Datei ausdrücklich lesen kann. Secretpersistenz getrennt von Image und Git halten.
- **Portainer:** Umgebung/Secret des tatsächlichen Dienstes beziehungsweise Stacks
  konfigurieren und neu bereitstellen. Zugang zur Stack-Verwaltung beschränken.
  Umgebungsvariablen sind kein verschlüsselter Tresor und für Berechtigte einsehbar.
- **GitHub Actions:** nur für einen implementierten Workflow das benötigte Repository-
  Secret setzen und explizit in den Schritt geben. Ein vorhandenes Secret allein
  aktiviert keine Funktion. Keine Keys in Workflowdateien schreiben.

Keys nie in Chat, Git, exportierte Pläne, Browserstorage oder Screenshots kopieren.
Zum planmäßigen Wechseln einen neuen Key hinterlegen, Verbindung kontrollieren und
erst danach den alten widerrufen. Bei vermutetem Missbrauch den alten Key sofort sperren. Die Dokumentation legt keinen Key an und speichert keinen.

## Netzwerke: Warum localhost oft falsch ist

Auf dem Host bezeichnet `127.0.0.1` den Host, im Container den jeweiligen Container.
Für zwei Dienste im selben Compose-Netz den tatsächlichen Servicenamen verwenden,
z. B. `http://ollama:11434`. Voraussetzung: Der Zieldienst lauscht auf einer dort
erreichbaren Schnittstelle. Das Beispiel ist kein mitgelieferter Compose-Stack.
Ein Dienst auf Host-Loopback ist aus dem Container normalerweise nicht erreichbar.
Host-Gateway/erlaubte LAN-Adresse gezielt nach Docker-Plattform konfigurieren;
`host.docker.internal` ist nicht in jeder Linux-Engine automatisch vorhanden.
Keine ungeschützten KI-Server dafür ins öffentliche Internet stellen.

## Bereits vorhandene Audio-/Avatarwege

**Piper wählen:** Benötigt werden `piper` im PATH oder `.venv-promo/bin/piper`,
`models/de_DE-thorsten-high.onnx` und die zugehörige `.onnx.json`. Verwende die
versionierten Projekt-Requirements/Constraints für eine eigene Umgebung; kein
ungeprüftes Upgrade aufgrund älterer Versionsangaben in Beispielen. Erst
`piper --help` und die vorhandenen Modelldateien prüfen, danach eine kurze lokale
WAV erzeugen. Die 2D-Produktion bricht bei fehlender Stimme ab. Die folgenden Schritte sind für einen Linux-Rechner mit Python-venv, curl und
FFmpeg gedacht; sie verändern keine globale Pythoninstallation:

```bash
python3 -m venv .venv-promo
.venv-promo/bin/python -m pip install -c requirements-constraints.txt piper-tts
mkdir -p models
curl --fail --location --output models/de_DE-thorsten-high.onnx \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/high/de_DE-thorsten-high.onnx
curl --fail --location --output models/de_DE-thorsten-high.onnx.json \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/high/de_DE-thorsten-high.onnx.json
.venv-promo/bin/piper --help
printf '%s\n' 'Dies ist ein lokaler Sprachtest.' | \
  .venv-promo/bin/piper --model models/de_DE-thorsten-high.onnx --output-file /tmp/pnh-stimmtest.wav
```

Erwartung: eine abspielbare WAV. Downloads vorher anhand der
[Stimmen-Dateien und Modellhinweise](https://huggingface.co/rhasspy/piper-voices/tree/main/de/de_DE/thorsten/high)
auf Lizenz und Eignung prüfen. Modell-Downloads hier folgen dem bestehenden
Produktionsworkflow; vor reproduzierbarem Deployment zusätzlich eine konkrete
Revision/Prüfsumme festhalten. Diese Download-/Installationsbefehle wurden für
diese Dokumentation nicht ausgeführt. Produktionsaufruf: [Werbevideo](../../WERBEVIDEO.md).

**eSpeak wählen:** `espeak-ng` und FFmpeg installieren, Versionen lokal prüfen und
bei der Werbevideo-Produktion ausdrücklich `--voice-engine espeak` wählen.
Die Stimme ist ein anderer lokaler Produktionsweg; kein stiller Ersatz für Piper.

**T900 / SadTalker wählen:** den manuellen Workflow „Produce one free chat Reel“
mit Stationsname, Sendung, fiktivem Host, Studio, öffentlichem Feed, Nachrichtenanzahl
und Ausgabename starten. Zuerst `test_mode=true`: kurzer Techniktest ohne Live-
Nachrichten, aber mit Modelldownloads und realer CPU-Inferenz. Der Workflow baut
zwei getrennte Python-3.10-Umgebungen; nicht in die allgemeine Pythonumgebung
installieren. Kein API-Key erforderlich. Das Ergebnis ist ein befristetes
Artefakt, keine automatische Veröffentlichung. Der geprüfte 3-Sekunden-Smoke ist
keine Qualitätsgarantie für längere Sendungen. Quellen: Projektdateien
`.github/workflows/chat-reel.yml` und `scripts/setup_reel_runtime.py`.

**MuseTalk wählen:** derzeit nur eigene experimentelle Workflows. Ein
installiertes Modell ist noch keine Auswahl in der gemeinsamen Providerverwaltung;
keinen automatischen Einsatz im regulären Video erwarten.

**3d-local / 3d-online wählen:** Status `setup_required`; es fehlen Renderadapter.
Pfade oder Keys beseitigen diese Sperre nicht. Bewusst auf `2d-local` wechseln,
wenn der vorhandene Produktionsweg gewünscht ist. [Renderoptionen](../../WERBEVIDEO.md).

## Fehler und nächster Schritt

| Meldung/Symptom | Was du prüfen musst | Bis dahin |
|---|---|---|
| Verbindung verweigert / Timeout | Dienst läuft? Richtiger Port? Host versus Container? Firewall? | Anbieter deaktiviert lassen |
| Modell fehlt / leere Liste | Modell vollständig geladen? Genaue ID, Lizenz, Backend und Speicher? | Keine Generierung |
| 401/403 | Key im tatsächlichen Dienst gesetzt? Rechte/Projekt/Workspace korrekt? | Key nicht protokollieren; bei Bedarf ersetzen |
| 404 | Basis-URL und API-Route sowie Modellzugang prüfen | Nicht blind auf kompatibles API-Format wechseln |
| 429 / Kontingent erschöpft | Rate-Limit und Budget unterscheiden; Wartezeit/Konto prüfen | Geplanter gleichartiger lokaler Fallback, kein Tarifwechsel |
| GPU-/RAM-Fehler | Modellgröße, Quantisierung und unterstützten Backend-Build prüfen | Modell kleiner wählen oder CPU bewusst testen |
| setup_required / Adapter fehlt | Integrationsstatus dieser Anleitung prüfen | Extern vorbereitet lassen, nicht als verbunden melden |
| Piper-Modell fehlt | ONNX und ONNX-JSON sowie Binary prüfen | Abbruch oder explizit eSpeak wählen |

Ein erfolgreicher Diensttest wird mit Datum, Runtime-/Modellversion und Ergebnis
notiert, ohne Key oder private Eingaben. Für eine echte PNH-Aktivierung fehlen bei
den Katalogkandidaten weiterhin Adapter, Verbindungstest und geschützte Verwaltung.
