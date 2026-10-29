# Architektur – Bestandsaufnahme für 0.1

Stand: 29.10.2026. Ausgangsbasis des Branches: `6b97cb9`. Der andere Arbeitsbaum `source/` hat zusätzliche uncommittete Entwicklungen und wird nicht automatisch übernommen. Die vollständige Abnahme von T001 steht noch aus; dieses Inventar ist der erste belegte Stand.

## Datenfluss und Grenzen

`config.json` → `generate.py`: RSS-Abruf und Parsing → konservative Themencluster und ausgewogene Auswahl → lokale redaktionelle Kurztexte / optionale Artikelanreicherung und Gegenrecherche → TTS mit Piper bzw. eSpeak-Fallback → FFmpeg-Komposition mit Studio, Szenen und Untertiteln → Dateien unter `docs/` → Pages/Feed und optional Telegram über Workflow.

Der aktuelle Generator schreibt direkt in das Veröffentlichungsverzeichnis. Die geplante harte Trennung von Produktion, Pflichtarchiv und Veröffentlichung ist noch nicht umgesetzt. Bestehende Headline-Gegenrecherche ist kein Nachweis einer Faktenprüfung. `lipsync.py` erzeugt eine amplitudenbasierte Annäherung, keine phonemgenaue Synchronisation. Provider-Registry und Budgetplan führen bisher keine realen Provideraufrufe oder dauerhafte Verbrauchsbuchung aus.

Parallele Testpfade: RSS-Themenanalyse → `build_broadcast_plan.py` → einzelne Renderjobs → `assemble_segments.py`. MuseTalk-Probes und Benchmarks sind Experimente, keine allgemeine Produktionsgarantie.

## Skriptinventar

- `analyze_topics.py`: Conservative RSS topic clustering, independent of the production publisher. Einstiegspunkte: clean, tokens, similarity, parse_feed, group_items, bilingual_candidates, main.
- `assemble_segments.py`: Zweck anhand Einstiegspunkten weiter prüfen. Einstiegspunkte: Moduldefinitionen.
- `audit_provider_research.py`: Review pending model-level evidence without external calls. Einstiegspunkte: report.
- `avatar_probe.py`: Non-publishing CPU feasibility probe for an animated-presenter pipeline. Einstiegspunkte: Moduldefinitionen.
- `build_broadcast_plan.py`: Build a deterministic, review-aware production plan from RSS topic candidates. Einstiegspunkte: clip, build, main.
- `build_hybrid_demo.py`: Experimental MuseTalk intro + existing bulletin. Does not alter docs/ production. Einstiegspunkte: run, probe, main.
- `check_schedule.py`: Gate scheduled production according to public config; manual runs bypass gate. Einstiegspunkte: Moduldefinitionen.
- `cleanup_telegram.py`: Delete bot messages no earlier than 25 hours after delivery. Einstiegspunkte: Moduldefinitionen.
- `generate.py`: Zero-cost RSS -> narrated static-image video -> podcast-style video RSS. Einstiegspunkte: german_number, spoken_timestamp, clean, fetch, media_candidates, download_media, extract_article_text, article_image_candidates, improve_news_image, search_commons_image, feed_timestamp, select_balanced_groups, items_from_feed, run, adjust_voice_pitch, synthesize, referenced_sources, crosscheck_headline, edit_news, group_news_items, main.
- `lipsync.py`: Lightweight offline, audio-driven mouth animation for a transparent presenter PNG. Einstiegspunkte: generate_frames.
- `model_residency.py`: Offline validation of model-level residency evidence; never calls provider APIs. Einstiegspunkte: validate_candidate.
- `mouth_motion_probe.py`: Experimental audio-reactive mouth-motion preview, not phoneme-level lip sync. Einstiegspunkte: Moduldefinitionen.
- `processing_location.py`: Processing-location preference validation for future provider integrations. Einstiegspunkte: validate_location.
- `provider_catalog.py`: Evidence-first processing location catalog for future paid providers. Einstiegspunkte: evaluate.
- `provider_registry.py`: Provider contracts and safe selection plan for a future PersonalNewsHost 2.0. Einstiegspunkte: _budget, plan, require_executable_version.
- `publish_telegram.py`: Optional Telegram delivery. Credentials are GitHub Actions secrets, never config.json. Einstiegspunkte: send.
- `render_musetalk_segment.py`: Zweck anhand Einstiegspunkten weiter prüfen. Einstiegspunkte: Moduldefinitionen.
- `render_segment.py`: Render one standalone test segment with local TTS and FFmpeg. Einstiegspunkte: main.
- `research_language.py`: Language-neutral groundwork for news research (DE/EN). Einstiegspunkte: normalize_language, research_terms, source_metadata, event_tokens, event_candidate.
- `story_card.py`: Generate original editorial story artwork without external image licensing. Einstiegspunkte: render.
- `validate_config.py`: Validate configuration locally; errors never echo configuration values/secrets. Einstiegspunkte: validate_config, main.

## Konfigurationsschlüssel

Pfade des aktuellen config.json; Werte werden absichtlich nicht in das Inventar kopiert. Erweiterungen sind vorerst schema-kompatibel zulässig, bekannte Felder werden typisiert validiert.

- `title`
- `production_version`
- `language`
- `voice`
- `max_items`
- `max_description_chars`
- `feeds`
- `background`
- `presenter`
- `tts_engine`
- `piper_length_scale`
- `presenter_settings`
- `presenter_settings.name`
- `presenter_settings.gender`
- `presenter_settings.portrait`
- `presenter_settings.background`
- `presenter_settings.voice_model`
- `presenter_settings.lip_sync`
- `presenter_settings.lip_sync.enabled`
- `presenter_settings.lip_sync.engine`
- `presenter_settings.lip_sync.fallback`
- `presenter_settings.lip_sync.mouth`
- `presenter_settings.lip_sync.mouth.x`
- `presenter_settings.lip_sync.mouth.y`
- `presenter_settings.lip_sync.mouth.width`
- `presenter_settings.lip_sync.mouth.height`
- `presenter_settings.lip_sync.note`
- `presenter_settings.lip_sync.fps`
- `presenter_settings.scenes`
- `presenter_settings.scenes.show_headlines`
- `presenter_settings.scenes.intro_mode`
- `presenter_settings.scenes.intro_text`
- `presenter_settings.scenes.outro_text`
- `presenter_settings.scenes.intro_static_type`
- `presenter_settings.scenes.intro_static_color`
- `presenter_settings.scenes.intro_static_image`
- `presenter_settings.desk_foreground`
- `voice_pitch_semitones`
- `telegram`
- `telegram.enabled`
- `telegram.recipient_type`
- `telegram.delivery`
- `telegram.caption`
- `automation`
- `automation.enabled`
- `automation.interval_hours`
- `automation.start_hour_local`
- `automation.timezone`
- `automation.days`
- `advanced_services`
- `advanced_services.processing_region`
- `advanced_services.processing_country`
- `advanced_services.require_verified_region`
- `advanced_services.news_provider`
- `advanced_services.voice_provider`
- `advanced_services.avatar_provider`
- `advanced_services.video_provider`
- `advanced_services.max_per_video_eur`
- `advanced_services.max_per_month_eur`
- `advanced_services.allow_paid`
- `editorial`
- `editorial.style`
- `editorial.max_sentences`
- `editorial.crosscheck`
- `editorial.crosscheck.enabled`
- `editorial.crosscheck.max_sources`
- `editorial.crosscheck.method`
- `editorial.crosscheck.note`
- `editorial.topic_clustering`
- `editorial.topic_clustering.enabled`
- `editorial.topic_clustering.mode`
- `editorial.topic_clustering.note`
- `editorial.selection`
- `editorial.selection.mode`
- `editorial.selection.note`
- `media`
- `media.mode`
- `media.max_download_mb`
- `media.web_image_fallback`
- `media.enhancement`
- `media.enhancement_modes`
- `media.prefer_article_images`

## Workflows

Timeout ist die konfigurierte Obergrenze, keine gemessene tatsächliche Laufzeit. Reale Laufzeit-/Monatsbudgetmessung bleibt offen.

| Workflow | Trigger | Job-Timeouts (Minuten) |
|---|---|---|
| `analyze-rss-topics.yml` | workflow_dispatch | analyze: 5 |
| `avatar-test.yml` | workflow_dispatch | probe: 10 |
| `lipsync-readiness.yml` | workflow_dispatch | cpu-readiness: 8 |
| `musetalk-25fps-benchmark.yml` | workflow_dispatch | official-preflight: 20 |
| `musetalk-audio-test.yml` | workflow_dispatch | audio: 15 |
| `musetalk-conditioned-unet.yml` | workflow_dispatch | conditioned-unet: 15 |
| `musetalk-cpu-optimize.yml` | workflow_dispatch | optimize: 15 |
| `musetalk-cpu-smoke.yml` | workflow_dispatch | cpu-compatibility: 12 |
| `musetalk-dependency-test.yml` | workflow_dispatch | dependencies: 15 |
| `musetalk-face-detection.yml` | workflow_dispatch | face: 15 |
| `musetalk-first-frame.yml` | workflow_dispatch | first-frame: 15 |
| `musetalk-first-video.yml` | workflow_dispatch | first-video: 15 |
| `musetalk-hybrid-interpolation.yml` | workflow_dispatch | official-preflight: 20 |
| `musetalk-model-load.yml` | workflow_dispatch | real-model-load: 12 |
| `musetalk-official-frame.yml` | workflow_dispatch | official-preflight: 15 |
| `musetalk-official-preflight.yml` | workflow_dispatch | official-preflight: 15 |
| `musetalk-official-video.yml` | workflow_dispatch | official-preflight: 15 |
| `musetalk-pipeline-preflight.yml` | workflow_dispatch | preflight: 8 |
| `musetalk-piper-10fps.yml` | workflow_dispatch | official-preflight: 20 |
| `musetalk-piper-intro.yml` | workflow_dispatch | official-preflight: 20 |
| `musetalk-quality-check.yml` | workflow_dispatch | quality-check: 15 |
| `musetalk-repeat-benchmark.yml` | workflow_dispatch | repeat: 15 |
| `musetalk-unet-forward.yml` | workflow_dispatch | cpu-forward: 15 |
| `musetalk-vae-cpu.yml` | workflow_dispatch | vae: 15 |
| `news.yml` | workflow_dispatch, schedule [{'cron': '17 * * * *'}] | generate: 40 |
| `parallel-broadcast.yml` | workflow_dispatch | prepare: GitHub-Standard, render: GitHub-Standard, assemble: GitHub-Standard |
| `parallel-musetalk-broadcast.yml` | workflow_dispatch | prepare: GitHub-Standard, render: 35, assemble: GitHub-Standard |
| `telegram-cleanup.yml` | workflow_dispatch, schedule [{'cron': '42 * * * *'}] | cleanup: GitHub-Standard |
| `wiki-sync.yml` | workflow_dispatch, push | publish: GitHub-Standard |

## Externe Zugriffe und lokale Abhängigkeiten

Der reguläre Betrieb liest konfigurierte HTTP(S)-Feeds und kann Artikel, Medien, Wikimedia-/Suchergebnisse sowie Modell-/Paketdownloads beziehen. Optionale Telegram-Skripte senden über die Bot-API. GitHub Actions/Pages und Modell-/Codequellen wie Hugging Face und GitHub sind weitere externe Dienste. Die genaue URL-/Secret-/Datenflussprüfung aller experimentellen Skripte ist vor Abschluss T001/T073 zu vervollständigen.

Lokal: Python, FFmpeg/ffprobe, Piper/eSpeak; je Pfad Pillow, OpenCV, NumPy und experimentelle PyTorch-/MuseTalk-Abhängigkeiten. Für die neue Schema-Prüfung `python3 -m pip install -r requirements.txt` verwenden.

## Offene Pull Requests

Über GitHub-Connector am 29.10.2026 ermittelt. Folgende Bewertungen sind vorläufige Scope-Einschätzungen anhand der PR-Beschreibungen, keine abgeschlossene Diff-/Integrationsprüfung und keine Mergefreigabe:

| PR | Vorschlag | Begründung |
|---|---|---|
| [#14 RSS-Quellen mit Logos](https://github.com/ploeffler/PersonalNewsHost/pull/14) | zurückstellen | Für Quellenverwaltung relevant, aber UI-/Assetumfang außerhalb der ersten Schemaänderung; Schema-/Datenmodellabgleich nötig. |
| [#13 Sendungsaufbereitung parallelisieren](https://github.com/ploeffler/PersonalNewsHost/pull/13) | zurückstellen | Nützlich für spätere Ressourcenplanung; zunächst gemeinsame Produktionsverträge stabilisieren und Last messen. |
| [#8 Telegram-Themenliste](https://github.com/ploeffler/PersonalNewsHost/pull/8) | zurückstellen | Auf spätere Kanalintegration abstimmen; bestehendes Telegramverhalten vorerst erhalten. |
| [#7 Renderfortschritt](https://github.com/ploeffler/PersonalNewsHost/pull/7) | zurückstellen | Sinnvolle Diagnose, nach Diffprüfung als separate Änderung integrierbar; keine Voraussetzung für Schema. |

## Prüfstand

Vor Änderungen: 38 Tests erfolgreich, einschließlich vorhandener FFmpeg-Smoke-Tests. Bestehende Tests versuchen teilweise Netzwerk-Fallbacks, obwohl sie ohne Verbindung bestehen. Strikte Netzwerksperre/Fixtures für alle Tests ist noch nachzuarbeiten (T072). Neue Validator-Tests benötigen keine Netzwerkverbindung.

Nächste Arbeiten für 0.1: Showisolierung, Kategorien-/Quellenregeln, Nachrichtendatenmodell, Mocks/Provider-Runtime, dauerhafte Budget-/Cache-/Datenabflusskontrolle sowie Analyse-Ausgabeschemata. 0.1 ist noch nicht erreicht.

## Abgleich T001 am 29.10.2026

Der lokale Ergänzungsentwurf wurde geprüft und separat gesichert. Seine pauschale Abschlussbehauptung wird nicht übernommen. Das Inventar oben ist ein historischer Zwischenstand und muss für T001 anhand des aktuellen Entwicklungsbranches vervollständigt werden. Die anderen lokalen 0.1-Arbeiten bleiben getrennt und ungeprüft; weder T001 noch Version 0.1 sind damit abgenommen.
