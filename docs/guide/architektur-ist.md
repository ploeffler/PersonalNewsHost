# Architektur und Quellinventar – T001 / Version 0.1

Stand: 29.10.2026, Entwicklungscommit `bfd1fce13a274c4599e8570d08ed1f8092e01cf5`. Arbeitsnachweis für [Issue #26](https://github.com/ploeffler/PersonalNewsHost/issues/26).

Dieses Inventar beschreibt den veröffentlichten Entwicklungsstand einschließlich dieses Inventar-PRs. Nicht integrierte lokale Änderungen anderer 0.1-Aufgaben sind ausgeschlossen. Es ist keine Versionsabnahme und veröffentlicht weder Wiki noch neue Diagramme.

Erfasst: **40 Python-Skripte, 43 Testdateien und 34 Workflows**. Sämtliche Dateien dieser Verzeichnisse sowie README und die vier Konfigurations-/Schemadateien wurden statisch gelesen. Experimentelle Jobs und externe Inhaltsproduktion wurden dafür nicht gestartet.

## Datenfluss und Produktionsgrenzen

1. `config.json` → `validate_config.py` → `shows.py`: Konfiguration prüfen, Legacy-Konfiguration als Show `main` auflösen, Show-Overrides und Ausgabeziel bestimmen.
2. `collect_news.py` speichert RSS-Nachrichten und ihre Zuordnung zu Sendungen/Kurzmeldungen. `editorial_pipeline.py` gruppiert Ereignisse, erstellt Entwürfe, prüft Quellenunterstützung und wählt freigegebene Beiträge. `news_policy.py` ergänzt Rubriken, Gewichtungen und Sperrlisten.
3. `generate.py` enthält weiterhin einen Legacy-Einstieg mit eigenem Feed-/Auswahlpfad. Artikelanreicherung erfolgt über `article_enrichment.py`; Gegenrecherche und Quellenunterstützung sind keine garantierte Faktenprüfung. `research_language.py` unterstützt DE/EN.
4. Redaktionstext → lokale Piper-Sprachausgabe mit eSpeak-Fallback → FFmpeg-Komposition aus Studio-/Moderatorbildern, Szenen, Untertiteln und Quellen. `lipsync.py` ist amplitudenbasierte Mundanimation; MuseTalk-Proben sind ein separater experimenteller Pfad.
5. `produce_show.py --show ...` setzt den Ausgabeordner auf `out/<show_id>/` und ruft keinen Publisher auf. Der direkte Legacy-Generator schreibt dagegen nach `docs/`; `news.yml` kann diese Dateien committen und optional Telegram beliefern. Die vollständige betriebliche Trennung von Produktion und Veröffentlichung ist deshalb noch nicht erreicht.
6. Kurzmeldungen laufen zusätzlich über `short_updates.py`, `short_update_video.py` und den eigenen Telegram-Publisher. Die Parallel-Demos verwenden Produktionsplan, einzelne Renderjobs und `assemble_segments.py`.
7. `broadcast_archive.py` hält im bisherigen Websitepfad nur die jüngsten zwei Sendungen. Das ist noch nicht das geplante verpflichtende, dauerhafte Jahr/Monat/Tag-Archiv. Die Beispielshow besitzt einen eigenen datierten Artefaktpfad.

`provider_registry.py` ist eine Auswahl-/Planungsgrundlage; `provider_runtime.py` bietet deterministische Mocks, Antwortvalidierung und SQLite-Cache. In diesem Commit werden die Legacy-Netzwerkzugriffe nicht vollständig über diese Runtime geleitet. Die lokal vorbereiteten Budget-/Analyse-Erweiterungen sind nicht Bestandteil dieses Inventars. T100/T101/T103/T104/T130/T135 bleiben separat offen.

## Skripte mit Zweck

Beschreibungen aus den Modulverträgen, ergänzt um die beiden Skripte ohne Modulbeschreibung. Funktionen dienen als Navigationshilfe; bloße Auflistung ist kein Nachweis der Funktionstüchtigkeit.

| Skript | Zweck |
|---|---|
| `scripts/analyze_topics.py` | Conservative RSS topic clustering, independent of the production publisher. |
| `scripts/article_enrichment.py` | Bounded public-article enrichment before editorial drafting and source checks. |
| `scripts/assemble_segments.py` | Fügt die im Produktionsplan genannten gerenderten Segmente mit FFmpeg zu parallel-demo.mp4 zusammen; fehlt ein Segment, bricht es ab. |
| `scripts/audit_provider_research.py` | Review pending model-level evidence without external calls. |
| `scripts/avatar_probe.py` | Non-publishing CPU feasibility probe for an animated-presenter pipeline. |
| `scripts/broadcast_archive.py` | Keep the two most recent bulletins and attach the homepage playlist. |
| `scripts/build_broadcast_plan.py` | Build a deterministic, review-aware production plan from RSS topic candidates. |
| `scripts/build_example_show.py` | Build a labelled offline example of the initial Allgemein newsroom's Newsshow. |
| `scripts/build_hybrid_demo.py` | Experimental MuseTalk intro + existing bulletin. Does not alter docs/ production. |
| `scripts/build_task_board.py` | Import planning sources once into an explicit multi-client development board. |
| `scripts/check_documentation_release.py` | Fail closed unless documentation targets a confirmed completed subversion. |
| `scripts/check_schedule.py` | Produce the newest due edition, including delayed or missed schedule runs. |
| `scripts/cleanup_telegram.py` | Compatibility entry point: retention is configured in the Telegram destination. |
| `scripts/collect_news.py` | Persist all RSS messages for 24 hours, with broadcast/update membership. |
| `scripts/editorial_pipeline.py` | Stored news -> event groups -> editorial draft -> source-support gate -> selection. |
| `scripts/export_example_demo.py` | Export the verified example as Newsshow-Demo repository media. |
| `scripts/generate.py` | Zero-cost RSS -> narrated static-image video -> podcast-style video RSS. |
| `scripts/lipsync.py` | Lightweight offline, audio-driven mouth animation for a transparent presenter PNG. |
| `scripts/model_residency.py` | Offline validation of model-level residency evidence; never calls provider APIs. |
| `scripts/mouth_motion_probe.py` | Experimental audio-reactive mouth-motion preview, not phoneme-level lip sync. |
| `scripts/news_policy.py` | Deterministic category mapping and explicit source selection rules. |
| `scripts/processing_location.py` | Processing-location preference validation for future provider integrations. |
| `scripts/produce_show.py` | Produce a selected show into out/<show_id>; never invoke external publishers. |
| `scripts/provider_catalog.py` | Evidence-first processing location catalog for future paid providers. |
| `scripts/provider_registry.py` | Provider contracts and safe selection plan for a future PersonalNewsHost 2.0. |
| `scripts/provider_runtime.py` | Offline-first provider contracts, response validation and transactional cache. |
| `scripts/publish_short_updates_telegram.py` | Two-phase Telegram delivery: persist attempt IDs before contacting Telegram. |
| `scripts/publish_telegram.py` | Optional Telegram delivery. Credentials are GitHub Actions secrets, never config.json. |
| `scripts/render_musetalk_segment.py` | Experimenteller CPU-Renderer für MuseTalk-Intro/Outro: lädt Modelle und Code, erzeugt Audio/Frames und interpoliert mit FFmpeg; kein regulärer Veröffentlichungspfad. |
| `scripts/render_segment.py` | Render one standalone test segment with local TTS and FFmpeg. |
| `scripts/render_workflow_diagrams.py` | Render maintained Graphviz sources as PNG and SVG for docs and GitHub Wiki. |
| `scripts/research_language.py` | Language-neutral groundwork for news research (DE/EN). |
| `scripts/short_update_video.py` | Render a narrated short-update card with transparent station branding. |
| `scripts/short_updates.py` | Conservative, extractive short news updates. No article scraping or invented facts. |
| `scripts/shows.py` | Resolve isolated show configurations without changing the caller's configuration. |
| `scripts/story_card.py` | Generate original editorial story artwork without external image licensing. |
| `scripts/sync_github_tasks.py` | Idempotent one-way mirror: authoritative JSON tasks -> GitHub issues/milestones. |
| `scripts/task_client.py` | JSON task coordination using ordinary fast-forward Git pushes as compare-and-swap. |
| `scripts/validate_config.py` | Validate configuration locally; errors never echo configuration values/secrets. |
| `scripts/video_branding.py` | Shared transparent station logo and the red short-update label. |

## Konfigurationsschlüssel

Es werden ausschließlich Pfade aufgeführt, keine Werte, Zugangsdaten oder Feed-Inhalte. `[]` bezeichnet beliebige Arrayelemente. Die Liste vereinigt die drei Konfigurationsdateien und alle im JSON-Schema definierten Objektfelder; sie unterscheidet definierte Schnittstelle und tatsächliche Beispielbelegung. Erweiterungsfelder können während der Migration zusätzlich erlaubt sein.

| Schlüsselpfad | Belegt / definiert in |
|---|---|
| `advanced_services` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `advanced_services.allow_paid` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `advanced_services.avatar_provider` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `advanced_services.max_per_month_eur` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `advanced_services.max_per_video_eur` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `advanced_services.news_provider` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `advanced_services.processing_country` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `advanced_services.processing_region` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `advanced_services.require_verified_region` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `advanced_services.video_provider` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `advanced_services.voice_provider` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `article_enrichment` | `config.json`, `config.example.json`, `config.shows.example.json` |
| `article_enrichment.enabled` | `config.json`, `config.example.json`, `config.shows.example.json` |
| `article_enrichment.max_fetches_per_run` | `config.json`, `config.example.json`, `config.shows.example.json` |
| `automation` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `automation.days` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `automation.enabled` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `automation.interval_hours` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `automation.start_hour_local` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `automation.timezone` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `background` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `category_filter` | `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `editorial` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `editorial.broadcast_sections` | `config.json`, `config.example.json`, `config.shows.example.json` |
| `editorial.broadcast_sections.default` | `config.json`, `config.example.json`, `config.shows.example.json` |
| `editorial.broadcast_sections.enabled` | `config.json`, `config.example.json`, `config.shows.example.json` |
| `editorial.broadcast_sections.feed_sections` | `config.json`, `config.example.json`, `config.shows.example.json` |
| `editorial.broadcast_sections.feed_sections.https://www.bmi.gv.at/rss/stmk_presse.xml` | `config.json`, `config.example.json`, `config.shows.example.json` |
| `editorial.broadcast_sections.feed_sections.https://www.kleinezeitung.at/rss/steiermark` | `config.json`, `config.example.json`, `config.shows.example.json` |
| `editorial.broadcast_sections.sections` | `config.json`, `config.example.json`, `config.shows.example.json` |
| `editorial.broadcast_sections.sections[].id` | `config.json`, `config.example.json`, `config.shows.example.json` |
| `editorial.broadcast_sections.sections[].keywords` | `config.json`, `config.example.json`, `config.shows.example.json` |
| `editorial.broadcast_sections.sections[].label` | `config.json`, `config.example.json`, `config.shows.example.json` |
| `editorial.crosscheck` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `editorial.crosscheck.enabled` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `editorial.crosscheck.max_sources` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `editorial.crosscheck.method` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `editorial.crosscheck.note` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `editorial.max_sentences` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `editorial.pipeline` | `config.json`, `config.example.json`, `config.shows.example.json` |
| `editorial.pipeline.enabled` | `config.json`, `config.example.json`, `config.shows.example.json` |
| `editorial.pipeline.max_store_age_minutes` | `config.json`, `config.example.json`, `config.shows.example.json` |
| `editorial.pipeline.method` | `config.json`, `config.example.json`, `config.shows.example.json` |
| `editorial.selection` | `config.json`, `config.schema.json` |
| `editorial.selection.mode` | `config.json`, `config.schema.json` |
| `editorial.selection.note` | `config.json`, `config.schema.json` |
| `editorial.style` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `editorial.topic_clustering` | `config.json`, `config.schema.json` |
| `editorial.topic_clustering.enabled` | `config.json`, `config.schema.json` |
| `editorial.topic_clustering.mode` | `config.json`, `config.schema.json` |
| `editorial.topic_clustering.note` | `config.json`, `config.schema.json` |
| `feed_categories` | `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `feeds` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `fork_config_initialized` | `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `language` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `max_description_chars` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `max_items` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `media` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `media.enhancement` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `media.enhancement_modes` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `media.max_download_mb` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `media.mode` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `media.prefer_article_images` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `media.web_image_fallback` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `piper_length_scale` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings.background` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings.desk_foreground` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings.gender` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings.lip_sync` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings.lip_sync.enabled` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings.lip_sync.engine` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings.lip_sync.fallback` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings.lip_sync.fps` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings.lip_sync.mouth` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings.lip_sync.mouth.height` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings.lip_sync.mouth.width` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings.lip_sync.mouth.x` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings.lip_sync.mouth.y` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings.lip_sync.note` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings.name` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings.portrait` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings.scenes` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings.scenes.intro_mode` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings.scenes.intro_static_color` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings.scenes.intro_static_image` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings.scenes.intro_static_type` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings.scenes.intro_text` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings.scenes.outro_text` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings.scenes.show_headlines` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `presenter_settings.voice_model` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `production` | `config.json`, `config.example.json`, `config.shows.example.json` |
| `production.parallel_workers` | `config.json`, `config.example.json`, `config.shows.example.json` |
| `production_version` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `short_updates` | `config.example.json`, `config.shows.example.json` |
| `short_updates.enabled` | `config.example.json`, `config.shows.example.json` |
| `short_updates.freshness_minutes` | `config.example.json`, `config.shows.example.json` |
| `short_updates.interval_minutes` | `config.example.json`, `config.shows.example.json` |
| `shows` | `config.shows.example.json`, `config.schema.json` |
| `shows[].automation` | `config.schema.json` |
| `shows[].automation.days` | `config.schema.json` |
| `shows[].automation.enabled` | `config.schema.json` |
| `shows[].automation.interval_hours` | `config.schema.json` |
| `shows[].automation.start_hour_local` | `config.schema.json` |
| `shows[].automation.timezone` | `config.schema.json` |
| `shows[].background` | `config.schema.json` |
| `shows[].category_filter` | `config.schema.json` |
| `shows[].editorial` | `config.schema.json` |
| `shows[].editorial.crosscheck` | `config.schema.json` |
| `shows[].editorial.crosscheck.enabled` | `config.schema.json` |
| `shows[].editorial.crosscheck.max_sources` | `config.schema.json` |
| `shows[].editorial.crosscheck.method` | `config.schema.json` |
| `shows[].editorial.crosscheck.note` | `config.schema.json` |
| `shows[].editorial.max_sentences` | `config.schema.json` |
| `shows[].editorial.selection` | `config.schema.json` |
| `shows[].editorial.selection.mode` | `config.schema.json` |
| `shows[].editorial.selection.note` | `config.schema.json` |
| `shows[].editorial.style` | `config.schema.json` |
| `shows[].editorial.topic_clustering` | `config.schema.json` |
| `shows[].editorial.topic_clustering.enabled` | `config.schema.json` |
| `shows[].editorial.topic_clustering.mode` | `config.schema.json` |
| `shows[].editorial.topic_clustering.note` | `config.schema.json` |
| `shows[].feed_categories` | `config.schema.json` |
| `shows[].feeds` | `config.schema.json` |
| `shows[].id` | `config.shows.example.json`, `config.schema.json` |
| `shows[].language` | `config.schema.json` |
| `shows[].max_description_chars` | `config.schema.json` |
| `shows[].max_items` | `config.shows.example.json`, `config.schema.json` |
| `shows[].media` | `config.schema.json` |
| `shows[].media.enhancement` | `config.schema.json` |
| `shows[].media.enhancement_modes` | `config.schema.json` |
| `shows[].media.max_download_mb` | `config.schema.json` |
| `shows[].media.mode` | `config.schema.json` |
| `shows[].media.prefer_article_images` | `config.schema.json` |
| `shows[].media.web_image_fallback` | `config.schema.json` |
| `shows[].piper_length_scale` | `config.schema.json` |
| `shows[].presenter` | `config.schema.json` |
| `shows[].presenter_settings` | `config.shows.example.json`, `config.schema.json` |
| `shows[].presenter_settings.background` | `config.schema.json` |
| `shows[].presenter_settings.desk_foreground` | `config.schema.json` |
| `shows[].presenter_settings.gender` | `config.schema.json` |
| `shows[].presenter_settings.lip_sync` | `config.schema.json` |
| `shows[].presenter_settings.lip_sync.enabled` | `config.schema.json` |
| `shows[].presenter_settings.lip_sync.engine` | `config.schema.json` |
| `shows[].presenter_settings.lip_sync.fallback` | `config.schema.json` |
| `shows[].presenter_settings.lip_sync.fps` | `config.schema.json` |
| `shows[].presenter_settings.lip_sync.mouth` | `config.schema.json` |
| `shows[].presenter_settings.lip_sync.mouth.height` | `config.schema.json` |
| `shows[].presenter_settings.lip_sync.mouth.width` | `config.schema.json` |
| `shows[].presenter_settings.lip_sync.mouth.x` | `config.schema.json` |
| `shows[].presenter_settings.lip_sync.mouth.y` | `config.schema.json` |
| `shows[].presenter_settings.lip_sync.note` | `config.schema.json` |
| `shows[].presenter_settings.name` | `config.schema.json` |
| `shows[].presenter_settings.portrait` | `config.schema.json` |
| `shows[].presenter_settings.scenes` | `config.shows.example.json`, `config.schema.json` |
| `shows[].presenter_settings.scenes.intro_mode` | `config.shows.example.json`, `config.schema.json` |
| `shows[].presenter_settings.scenes.intro_static_color` | `config.schema.json` |
| `shows[].presenter_settings.scenes.intro_static_image` | `config.schema.json` |
| `shows[].presenter_settings.scenes.intro_static_type` | `config.schema.json` |
| `shows[].presenter_settings.scenes.intro_text` | `config.schema.json` |
| `shows[].presenter_settings.scenes.outro_text` | `config.schema.json` |
| `shows[].presenter_settings.scenes.show_headlines` | `config.schema.json` |
| `shows[].presenter_settings.voice_model` | `config.schema.json` |
| `shows[].production` | `config.schema.json` |
| `shows[].schedule` | `config.shows.example.json`, `config.schema.json` |
| `shows[].schedule.days` | `config.schema.json` |
| `shows[].schedule.enabled` | `config.shows.example.json`, `config.schema.json` |
| `shows[].schedule.interval_hours` | `config.schema.json` |
| `shows[].schedule.start_hour_local` | `config.schema.json` |
| `shows[].schedule.timezone` | `config.schema.json` |
| `shows[].source_policy` | `config.schema.json` |
| `shows[].source_policy.blocked_domains` | `config.schema.json` |
| `shows[].source_policy.excluded_keywords` | `config.schema.json` |
| `shows[].source_policy.weights` | `config.schema.json` |
| `shows[].station_logo` | `config.schema.json` |
| `shows[].studio` | `config.schema.json` |
| `shows[].target_duration_seconds` | `config.shows.example.json`, `config.schema.json` |
| `shows[].title` | `config.shows.example.json`, `config.schema.json` |
| `shows[].tts_engine` | `config.schema.json` |
| `shows[].voice` | `config.schema.json` |
| `shows[].voice_pitch_semitones` | `config.schema.json` |
| `source_policy` | `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `source_policy.blocked_domains` | `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `source_policy.excluded_keywords` | `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `source_policy.weights` | `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `station_logo` | `config.json`, `config.example.json`, `config.shows.example.json` |
| `telegram` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `telegram.caption` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `telegram.delivery` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `telegram.enabled` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `telegram.recipient_type` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `telegram.target` | `config.json` |
| `title` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `tts_engine` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `voice` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |
| `voice_pitch_semitones` | `config.json`, `config.example.json`, `config.shows.example.json`, `config.schema.json` |

## Workflows: Trigger, Grenzen und beobachtete Laufzeit

Timeouts sind Job-Obergrenzen in Minuten; „nicht gesetzt“ bedeutet kein explizites Limit im Repository. Gemessene Zeiten sind Laufzeit des gesamten Workflow-Laufs von run_started_at bis updated_at, einschließlich Abschluss-/Warteanteilen, keine Abrechnungsminuten oder Prognose. Je Workflow wird der neueste abgeschlossene Lauf aus den zuletzt 100 über die API gelieferten Repository-Läufen verwendet; fehlende Messung heißt nicht „nie gelaufen“. Die Messung kann einen anderen Branch betreffen.

| Workflow | Trigger einschließlich Einschränkungen | Job-Timeouts (Min.) | Beobachtung |
|---|---|---|---|
| `.github/workflows/analyze-rss-topics.yml` | `{"workflow_dispatch":""}` | analyze: 5 | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/avatar-test.yml` | `{"workflow_dispatch":""}` | probe: 10 | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/example-newsshow.yml` | `{"push":{"branches":["Full-featured-Newsoutlet"],"paths":[".github/workflows/example-newsshow.yml","scripts/build_example_show.py","scripts/export_example_demo.py","tests/fixtures/example-show.json"]},"workflow_dispatch":""}` | example: 20 | [42 s, success](https://github.com/ploeffler/PersonalNewsHost/actions/runs/40948790166); `Full-featured-Newsoutlet`; 2026-10-29T20:24:47Z |
| `.github/workflows/lipsync-readiness.yml` | `{"workflow_dispatch":""}` | cpu-readiness: 8 | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/musetalk-25fps-benchmark.yml` | `{"workflow_dispatch":""}` | official-preflight: 20 | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/musetalk-audio-test.yml` | `{"workflow_dispatch":""}` | audio: 15 | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/musetalk-conditioned-unet.yml` | `{"workflow_dispatch":""}` | conditioned-unet: 15 | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/musetalk-cpu-optimize.yml` | `{"workflow_dispatch":""}` | optimize: 15 | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/musetalk-cpu-smoke.yml` | `{"workflow_dispatch":""}` | cpu-compatibility: 12 | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/musetalk-dependency-test.yml` | `{"workflow_dispatch":""}` | dependencies: 15 | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/musetalk-face-detection.yml` | `{"workflow_dispatch":""}` | face: 15 | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/musetalk-first-frame.yml` | `{"workflow_dispatch":""}` | first-frame: 15 | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/musetalk-first-video.yml` | `{"workflow_dispatch":""}` | first-video: 15 | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/musetalk-hybrid-interpolation.yml` | `{"workflow_dispatch":""}` | official-preflight: 20 | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/musetalk-model-load.yml` | `{"workflow_dispatch":""}` | real-model-load: 12 | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/musetalk-official-frame.yml` | `{"workflow_dispatch":""}` | official-preflight: 15 | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/musetalk-official-preflight.yml` | `{"workflow_dispatch":""}` | official-preflight: 15 | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/musetalk-official-video.yml` | `{"workflow_dispatch":""}` | official-preflight: 15 | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/musetalk-pipeline-preflight.yml` | `{"workflow_dispatch":""}` | preflight: 8 | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/musetalk-piper-10fps.yml` | `{"workflow_dispatch":""}` | official-preflight: 20 | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/musetalk-piper-intro.yml` | `{"workflow_dispatch":""}` | official-preflight: 20 | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/musetalk-quality-check.yml` | `{"workflow_dispatch":""}` | quality-check: 15 | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/musetalk-repeat-benchmark.yml` | `{"workflow_dispatch":""}` | repeat: 15 | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/musetalk-unet-forward.yml` | `{"workflow_dispatch":""}` | cpu-forward: 15 | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/musetalk-vae-cpu.yml` | `{"workflow_dispatch":""}` | vae: 15 | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/news.yml` | `{"workflow_dispatch":"","schedule":[{"cron":"17 * * * *"}]}` | generate: 40 | [211 s, success](https://github.com/ploeffler/PersonalNewsHost/actions/runs/40916671040); `main`; 2026-10-29T16:57:42Z |
| `.github/workflows/parallel-broadcast.yml` | `{"workflow_dispatch":""}` | prepare: nicht gesetzt; render: nicht gesetzt; assemble: nicht gesetzt | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/parallel-musetalk-broadcast.yml` | `{"workflow_dispatch":""}` | prepare: nicht gesetzt; render: 35; assemble: nicht gesetzt | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/render-regression.yml` | `{"pull_request":{"paths":["scripts/**","tests/**","assets/**","config.json","config.example.json","config.shows.example.json","config.schema.json","requirements.txt",".github/workflows/render-regression.yml"]},"workflow_dispatch":""}` | render: 15 | [0 s, action_required](https://github.com/ploeffler/PersonalNewsHost/actions/runs/40957875783); `Full-featured-Newsoutlet`; 2026-10-29T21:26:52Z |
| `.github/workflows/research-feed-catalogs.yml` | `{"workflow_dispatch":{"inputs":{"group":{"description":"Welche Quellengruppe recherchieren?","required":"true","default":"both","type":"choice","options":["both","news","authorities"]}}}}` | news: 25; authorities: 35; source-logos: 20 | keine abgeschlossene Messung im 100-Läufe-Fenster |
| `.github/workflows/short-updates.yml` | `{"workflow_dispatch":"","push":{"branches":["main"],"paths":[".github/workflows/short-updates.yml","scripts/video_branding.py","scripts/short_update_video.py","assets/logo-video.png","scripts/article_enrichment.py","scripts/collect_news.py","scripts/short_updates.py","scripts/publish_short_updates_telegram.py"]},"schedule":[{"cron":"7,22,37,52 * * * *"}]}` | updates: 15 | [63 s, success](https://github.com/ploeffler/PersonalNewsHost/actions/runs/40954264227); `main`; 2026-10-29T21:02:12Z |
| `.github/workflows/task-sync.yml` | `{"push":{"branches":["Full-featured-Newsoutlet"],"paths":["planning/task-board.json","planning/project.json","scripts/sync_github_tasks.py",".github/workflows/task-sync.yml"]},"workflow_dispatch":""}` | mirror: 20 | [17 s, success](https://github.com/ploeffler/PersonalNewsHost/actions/runs/40957832315); `Full-featured-Newsoutlet`; 2026-10-29T21:26:33Z |
| `.github/workflows/telegram-test.yml` | `{"workflow_dispatch":{"inputs":{"target":{"description":"Secret destination","type":"choice","options":["default","secondary"],"default":"default"},"delivery":{"description":"Send a test message or resend the current video","type":"choice","options":["text","video"],"default":"text"}}}}` | test: 3 | [14 s, success](https://github.com/ploeffler/PersonalNewsHost/actions/runs/40853777829); `main`; 2026-10-29T09:58:10Z |
| `.github/workflows/wiki-sync.yml` | `{"push":{"tags":["v[0-9]*.[0-9]*"]},"workflow_dispatch":{"inputs":{"release_tag":{"description":"Already completed subversion tag, for example v0.1","required":"true","type":"string"}}}}` | publish: nicht gesetzt | [9 s, success](https://github.com/ploeffler/PersonalNewsHost/actions/runs/40878108903); `main`; 2026-10-29T13:00:57Z |

`task-sync.yml` spiegelt den JSON-Bestand auf dem Entwicklungsbranch. `wiki-sync.yml` läuft nur nach Versions-Tag bzw. explizitem Release-Aufruf und prüft den Freigabemarker. `short-updates.yml` enthält weiterhin einen Push-Trigger auf `main`; das ist Bestandsaufnahme, keine Freigabe, diesen Branch zu ändern. Geplante Jobs laufen nach GitHub-Regeln vom Defaultbranch; sie werden durch dieses Inventar nicht aktiviert.

## Externe Dienste und Datenwege

| Dienstgruppe | Auslöser / ausgehende Daten |
|---|---|
| Konfigurierte RSS-/Atom-Quellen und Artikelseiten | HTTP-Abruf in Sammlung/Generator/Artikelanreicherung; Abrufziel aus Konfiguration oder Meldung, Metadaten/Netzwerkadresse gehen an den Server. |
| Websuche, Wikimedia und Medienserver | Optionale Gegenrecherche/Bildsuche mit Titel-/Suchbegriffen, Bild-/Artikeldownloads; Zielhosts können aus Feed und HTML stammen. |
| Telegram Bot API | Optionale Sendungen/Kurzmeldungen, Text/Video und Zielchat; Token aus Secrets/Umgebung. Cleanup kann alte Bot-Nachrichten löschen. |
| GitHub API, Git-Remotes, Actions, Pages, Wiki | Code/Artefakte, Tasks/PRs, Website-Dateien; Wiki-Publishing nur bei freigegebener Subversion. Actions benötigt außerdem Paket-/Action-Downloads. |
| Hugging Face / MuseTalk / Piper-Modellquellen | Modell-/Code-Downloads für TTS oder experimentelle Avatarjobs, einschließlich Whisper/VAE/MuseTalk; kein Nachweis lokaler Offline-Ersteinrichtung. |
| Python-/Node-/Linux-Paketquellen und Browser-Downloads | Installation im Workflow; Offline-Tests bedeuten nicht, dass auch die Installation ohne Netzwerk erfolgt. |
| Katalogisierte KI-Anbieter / optionale Provider-Endpunkte | Auswahl- und Vertragsdaten sind vorhanden; daraus folgt kein aktiver externer Adapter. Provider-Mocks erzeugen lokal. Legacy-Zugriffe bestehen separat fort. |

### Statisch gefundene HTTP(S)-Hosts

Hosts aus Skripten, Workflows und den drei Konfigurationsdateien, jeweils mit Fundstellen. Dokumentations-/Namespace-URLs und reine Metadaten können enthalten sein; ein Fund beweist keinen Netzwerkaufruf. Dynamisch zusammengesetzte, konfigurierte oder über Weiterleitungen erreichte Ziele sind durch eine statische Liste nicht abschließend bestimmbar. Test-Fixture-Hosts sind ausgeschlossen.

- `api.krone.at`: `config.json`
- `api.telegram.org`: `.github/workflows/telegram-test.yml`, `scripts/publish_short_updates_telegram.py`, `scripts/publish_telegram.py`
- `archive.ubuntu.com`: `.github/workflows/news.yml`
- `commons.wikimedia.org`: `scripts/generate.py`
- `download.pytorch.org`: `.github/workflows/musetalk-25fps-benchmark.yml`, `.github/workflows/musetalk-audio-test.yml`, `.github/workflows/musetalk-conditioned-unet.yml`, `.github/workflows/musetalk-cpu-optimize.yml`, `.github/workflows/musetalk-cpu-smoke.yml`, `.github/workflows/musetalk-dependency-test.yml`, `.github/workflows/musetalk-face-detection.yml`, `.github/workflows/musetalk-first-frame.yml`, `.github/workflows/musetalk-first-video.yml`, `.github/workflows/musetalk-hybrid-interpolation.yml`, `.github/workflows/musetalk-model-load.yml`, `.github/workflows/musetalk-official-frame.yml`, `.github/workflows/musetalk-official-preflight.yml`, `.github/workflows/musetalk-official-video.yml`, `.github/workflows/musetalk-piper-10fps.yml`, `.github/workflows/musetalk-piper-intro.yml`, `.github/workflows/musetalk-quality-check.yml`, `.github/workflows/musetalk-repeat-benchmark.yml`, `.github/workflows/musetalk-unet-forward.yml`, `.github/workflows/musetalk-vae-cpu.yml`, `.github/workflows/parallel-musetalk-broadcast.yml`
- `example.invalid`: `scripts/build_example_show.py`
- `github.com`: `.github/workflows/musetalk-25fps-benchmark.yml`, `.github/workflows/musetalk-hybrid-interpolation.yml`, `.github/workflows/musetalk-official-frame.yml`, `.github/workflows/musetalk-official-preflight.yml`, `.github/workflows/musetalk-official-video.yml`, `.github/workflows/musetalk-piper-10fps.yml`, `.github/workflows/musetalk-piper-intro.yml`, `.github/workflows/wiki-sync.yml`, `scripts/render_musetalk_segment.py`, `scripts/sync_github_tasks.py`
- `huggingface.co`: `.github/workflows/avatar-test.yml`, `.github/workflows/musetalk-piper-10fps.yml`, `.github/workflows/musetalk-piper-intro.yml`, `.github/workflows/news.yml`, `.github/workflows/parallel-broadcast.yml`, `.github/workflows/parallel-musetalk-broadcast.yml`
- `mirrors.edge.kernel.org`: `.github/workflows/news.yml`
- `news.google.com`: `scripts/generate.py`
- `ploeffler.github.io`: `scripts/generate.py`, `scripts/publish_short_updates_telegram.py`, `scripts/publish_telegram.py`
- `purl.org`: `scripts/collect_news.py`, `scripts/generate.py`
- `raw.githubusercontent.com`: `.github/workflows/news.yml`, `.github/workflows/wiki-sync.yml`, `scripts/generate.py`
- `rss.orf.at`: `config.json`
- `search.yahoo.com`: `scripts/collect_news.py`, `scripts/generate.py`
- `www.bmi.gv.at`: `config.example.json`, `config.json`, `config.shows.example.json`
- `www.derstandard.at`: `config.example.json`, `config.json`, `config.shows.example.json`
- `www.kleinezeitung.at`: `config.example.json`, `config.json`, `config.shows.example.json`
- `www.w3.org`: `scripts/analyze_topics.py`, `scripts/collect_news.py`, `scripts/generate.py`

Secret-Bezeichner in Workflows (keine Werte): `PERSONALNEWSHOST_CONFIG`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_CHAT_ID_SECONDARY`, `WIKI_TOKEN`.

Lokale Werkzeuge: Python mit JSON-Schema-Prüfung, FFmpeg/ffprobe, Piper/eSpeak, Pillow; abhängig vom Pfad NumPy/OpenCV, PyTorch und MuseTalk. JavaScript- und Browsertests benötigen Node und gegebenenfalls Playwright/Browser. Tatsächlich verwendete Paketversionen sind den jeweiligen Anforderungen und Workflow-Installationsschritten zu entnehmen; eine einheitliche Pinning-Abnahme ist T073.

## Testinventar

Alle vorhandenen Testdateien; Benennung und Testfunktionen geben den geprüften Schwerpunkt an. Diese Liste ist keine neue Gesamttest-Ausführung und behauptet keine vollständige Testabdeckung.

| Testdatei | Testbereiche / Einstiegspunkte |
|---|---|
| `tests/test_article_enrichment.py` | test_orf_extracts_article_without_navigation; test_generic_and_structured_article_data; test_wrong_page_consent_paywall_and_content_types_are_not_sources; test_redirect_and_canonical_identity; test_cache_provenance_and_age_preservation; test_failure_backoff_and_changed_headline_does_not_use_stale_text; test_refresh_failure_preserves_same_version_snapshot; test_fetch_budget_and_deferred_retry; test_puzzles_are_classified_without_fetching_but_news_about_puzzles_is_not; test_optional_rdrr_fallback_uses_existing_markup_cleanup; test_collector_cache_survives_another_empty_rss_poll |
| `tests/test_article_markup.py` | test_police_district_locality_and_date; test_date_is_not_a_sentence_boundary; test_actual_image_credit_and_emphasis; test_link_label_survives_nested_url_parentheses; test_nested_and_linked_images_are_removed; test_reference_images_links_and_definitions; test_html_code_blocks_and_autolinks; test_plain_prose_and_numbers_survive; test_parenthesized_image_credits_are_removed; test_image_credits_do_not_remove_other_parentheses; test_extraction_removes_image_credit_before_length_limit; test_rss_fallback_removes_image_credits_in_all_styles; test_image_only_extraction_falls_back_to_rss; test_clean_before_article_length_limit; test_all_editorial_styles_clean_rss_fallback |
| `tests/test_bilingual_broadcast_plan.py` | test_bilingual_candidate_added_to_review_not_narration; test_no_bilingual_candidates_backward_compatible; test_invalid_candidate_does_not_enter_queue |
| `tests/test_bilingual_topics.py` | test_cross_language_candidate; test_same_language_and_unknown_not_cross_language; test_rss_language_metadata; test_unknown_feed_language_is_not_assumed |
| `tests/test_broadcast_archive.py` | test_two_broadcasts_and_their_sidecars_survive_rotation; test_missing_video_does_not_publish_manifest; test_homepage_is_decorated_once |
| `tests/test_collect_news.py` | test_all_feed_entries_and_atom_dates; test_tracking_dedup_preserves_article_identifiers; test_age_future_and_original_date; test_collection_badges_outage_and_no_undated_resurrection; test_every_member_of_a_combined_broadcast_story_is_marked; test_expired_selected_message_is_not_reintroduced |
| `tests/test_config_validation.py` | test_repository_configs_are_valid; test_invalid_core_values; test_bad_timezone_and_budget; test_non_finite_numbers_even_in_extensions; test_error_does_not_echo_secret; test_invalid_config_stops_before_feed_fetch |
| `tests/test_documentation_release.py` | test_matching_confirmed_tag; test_incomplete_or_untested_blocks; test_wrong_tag_or_branch_blocks; test_unconfirmed_version_marker_blocks; test_incomplete_task_board_blocks_even_confirmed_marker; test_renderer_does_not_run_before_gate |
| `tests/test_editorial_pipeline.py` | test_combines_complementary_sentences_from_different_sources; test_source_credit_occurs_once_at_end_for_single_and_multiple_sources; test_classified_puzzles_are_reported_separately_from_failed_source_checks; test_question_headline_is_not_changed_to_a_statement; test_distinct_places_and_broad_topics_are_not_grouped; test_opposing_negation_and_uncertainty_are_not_deduplicated_into_certainty; test_counter_disagreement_is_held_before_selection; test_numbers_names_negation_and_modal_qualifiers_cannot_be_changed; test_free_text_and_foreign_citation_are_rejected; test_one_bounded_repair_pass_is_recorded; test_all_groups_are_checked_before_limit_is_applied; test_expired_future_and_empty_prose_are_not_used; test_missing_and_stale_store_fail_without_raw_feed_fallback; test_district_cleanup_preserves_locality_and_date |
| `tests/test_editorial_production.py` | test_stored_multi_source_text_reaches_voice_without_raw_refetch_or_rewrite; test_later_text_tampering_blocks_voice_and_updates_audit; test_blocked_member_excludes_entire_prepared_group; test_no_approved_story_never_synthesizes_or_falls_back |
| `tests/test_editorial_report_browser.cjs` | Node-Assertions / Browser-Szenario im Dateieinstieg |
| `tests/test_example_show.py` | test_fixture_and_configuration; test_fixture_restores_sources_and_blocks_network; test_example_strapline_does_not_claim_live; test_workflow_only_updates_development_demo |
| `tests/test_feed_picker.cjs` | Node-Assertions / Browser-Szenario im Dateieinstieg |
| `tests/test_feed_picker_browser.cjs` | \n |
| `tests/test_feed_research.py` | test_stored_catalogues_validate; test_empty_catalogue_is_not_success; test_duplicates_are_rejected; test_research_cannot_activate_a_feed; test_opml_mismatch_is_rejected; test_empty_warning_feed_is_valid_with_adapter_requirement; test_warning_adapter_requirement_cannot_be_omitted; test_failed_run_exports_failure_log_but_no_old_catalogue; test_offline_export_is_labelled_as_stored_snapshot; test_existing_artifact_directory_is_not_reused |
| `tests/test_github_task_sync.py` | test_create_and_repeat_without_duplicate_or_mutation; test_human_notes_and_unmanaged_labels_are_preserved; test_done_closes_issue_but_not_milestone; test_ambiguous_create_is_recovered_without_duplicate; test_task_title_collision_without_marker_is_not_duplicated; test_duplicate_managed_issues_fail |
| `tests/test_intro_headlines.py` | test_all_topics_cover_measured_intro_once_in_order; test_single_headline_uses_whole_intro; test_no_topics_or_no_intro |
| `tests/test_model_residency.py` | test_empty_candidate_is_not_approved; test_destination_outside_allowed_regions; test_complete_documentation_still_needs_independent_approval |
| `tests/test_news_list.cjs` | Node-Assertions / Browser-Szenario im Dateieinstieg |
| `tests/test_news_list_browser.cjs` | . |
| `tests/test_news_policy.py` | test_default_and_category_filter; test_domain_boundary_and_feed_block; test_keyword_and_block_override_weight; test_weights_change_order_but_defaults_keep_recency |
| `tests/test_news_selection.py` | test_sections_feed_priority_fallback_and_activation; test_rss_pubdate; test_rdf_dc_date; test_diversity_before_second_item_from_same_source; test_undated_items_are_not_prioritized; test_unrelated_stories_stay_separate |
| `tests/test_parallel_production.py` | test_tasks_overlap_and_results_remain_in_input_order; test_worker_limit_is_respected; test_single_worker_runs_on_calling_thread; test_missing_config_enables_two_workers; test_worker_failure_propagates; test_empty_stage |
| `tests/test_playlist.cjs` | Node-Assertions / Browser-Szenario im Dateieinstieg |
| `tests/test_playlist_browser.cjs` | . |
| `tests/test_provider_registry.py` | test_default_is_free; test_paid_requires_consent_and_budgets; test_even_consented_paid_is_blocked; test_invalid_provider_and_budget_rejected; test_processing_location_validation; test_unverified_provider_residency; test_legacy_version_remains_valid |
| `tests/test_provider_runtime.py` | test_cache_survives_runtime_restart; test_prompt_model_and_revision_invalidate; test_allowlist_removes_fields_and_rejects_nested_data; test_secrets_rejected_before_provider; test_paid_provider_never_called_even_with_cache; test_invalid_response_not_cached_and_fallback; test_timeout_fallback; test_parallel_identical_calls_generate_once; test_all_kinds_have_deterministic_mock; test_namespaces_do_not_share_cache; test_secret_in_model_metadata_rejected; test_unknown_or_incompatible_provider; test_corrupt_cache_recomputed; test_feed_instruction_is_data_and_no_execution_schema |
| `tests/test_rdrr_extraction.py` | test_extracts_article_text; test_falls_back_on_failed_extraction; test_rejects_invalid_url |
| `tests/test_render_load.py` | test_five_stories_with_animated_presenter_and_media |
| `tests/test_render_progress.py` | test_scene_boundaries; test_titles_stay_on_one_log_line; test_read_partial_and_missing_progress; test_ffmpeg_progress_is_enabled_and_completion_logged; test_timeout_and_process_errors_are_propagated; test_contribution_is_reported_before_render_process_finishes |
| `tests/test_research_language.py` | test_language_codes; test_terms_preserve_original_headline; test_bilingual_event_candidate_requires_review; test_generic_headlines_do_not_match; test_source_metadata |
| `tests/test_schedule.py` | test_observed_late_run_catches_missed_six_oclock; test_no_duplicate_after_catchup_or_manual_publication; test_multiple_missed_slots_produce_only_latest_edition; test_failed_attempt_does_not_consume_slot; test_next_slot_becomes_due; test_disabled_and_manual_override; test_weekday_and_weekend_restrictions; test_daily_before_start_catches_previous_day; test_spring_gap_is_skipped; test_autumn_repeated_hour_publishes_once; test_missing_or_future_publication_does_not_block; test_rss_timestamp_and_malformed_fallback; test_invalid_configuration_rejected_even_for_manual_runs; test_command_line_emits_github_output |
| `tests/test_short_updates.py` | test_fresh_significant_item_and_repeat; test_stale_missing_future_and_generic; test_retention_exact_boundary_and_count; test_cross_source_duplicate_and_rate_limit |
| `tests/test_short_updates_telegram.py` | test_secondary_and_repeat_across_runs; test_same_queue_cannot_be_sent_twice; test_timeout_does_not_retry_and_hides_token; test_disabled_and_old_updates; test_missing_credentials_does_not_reserve; test_destination_change_refuses_send; test_future_updates_and_invalid_ids; test_unicode_and_long_text_fit_telegram; test_rejected_api_result_fails |
| `tests/test_short_updates_video.py` | test_branding_rejects_path_traversal; test_render_has_video_audio_red_label_and_transparent_logo; test_existing_audio_gets_one_video_and_expiry_removes_both |
| `tests/test_shows.py` | test_legacy_main_is_exact_copy; test_independent_inheritance; test_ids_and_unknown_fields_rejected; test_two_productions_restore_globals_and_separate_artifacts; test_error_restores_context_and_does_not_mark_success; test_symlink_escape_rejected; test_unknown_show_has_no_side_effects; test_legacy_entrypoint_does_not_ignore_explicit_shows; test_two_shows_generate_separate_videos; test_example_is_valid |
| `tests/test_source_logos.py` | test_fresh_cached_logo_needs_no_network; test_new_domain_is_downloaded_without_losing_other_group_cache; test_expired_icon_is_refreshed; test_transient_failure_keeps_previous_image_and_success_date; test_missing_image_is_not_treated_as_a_usable_cache_hit; test_identical_images_share_one_local_file; test_refresh_does_not_replace_another_hosts_shared_icon; test_cache_paths_cannot_escape_asset_directory; test_successful_groups_are_combined_before_one_shared_refresh; test_single_selected_group_is_supported; test_failed_second_group_does_not_replace_successful_result; test_failed_group_is_not_packaged_as_success |
| `tests/test_speech_config.py` | test_invalid_engine_fails_closed; test_espeak_does_not_call_piper |
| `tests/test_spoken_timestamp.py` | test_october_example; test_midnight; test_twentieth |
| `tests/test_subtitles.py` | test_pcm_pause_has_exact_duration_and_silent_samples; test_subtitles_end_before_transition_pause; test_timestamps_carry_and_long_duration; test_speech_boundaries_and_literal_text; test_empty_and_zero_length_segments; test_reject_mismatched_segments |
| `tests/test_task_client.py` | test_project_board_and_schema; test_claim_conflict_and_file_scope_conflict; test_expired_owner_is_fenced; test_dependency_and_local_pending_block; test_review_is_separate_and_requires_evidence; test_unsafe_or_empty_scopes_rejected; test_state_input_is_not_mutated; test_two_clients_cannot_both_claim_same_task; test_stale_revision_cannot_publish; test_non_shared_evidence_commit_is_rejected |
| `tests/test_telegram.py` | test_secondary; test_video_caption_lists_broadcast_topics_in_order; test_long_caption_and_emoji_topics_fit_telegram_limit; test_invalid_topic_file_preserves_caption; test_cleanup_never_calls_telegram; test_legacy_deletion_setting_is_ignored; test_missing_video_blocks_send; test_disabled |
| `tests/test_video_smoke.py` | test_avatar_intro; test_static_color_intro; test_static_image_intro; test_transparent_station_logo_throughout_broadcast; test_default_station_logo_without_config_field |

Zusätzliche Fixture: `tests/fixtures/example-show.json` enthält vorbereitete, nicht aktuelle Beispielmeldungen. Die Schema-, Nachrichten-, Show- und Renderprüfungen sind getrennte Nachweise; bestehende Testläufe in PR-Beschreibungen werden hier nicht als neu bestanden übernommen.

## Offene Pull Requests und Empfehlung

API-Snapshot vom 29.10.2026 vor Erstellung dieses Inventar-PRs. Die Empfehlungen betreffen ausschließlich den Entwicklungsbranch; keine Mergefreigabe nach `main`. Für #7/#8/#13/#14 wurden die geänderten Dateilisten geprüft und ihre Head-Commits per `git merge-base --is-ancestor` im Entwicklungsbranch nachgewiesen. Bereits enthaltene Änderungen brauchen keinen zweiten Merge.

| PR | Empfehlung | Begründung |
|---|---|
| [#7 Renderfortschritt](https://github.com/ploeffler/PersonalNewsHost/pull/7) | übernehmen – bereits enthalten | Head ist Vorfahr des Entwicklungsstands; Generator-/Workflow-Logging und Tests vorhanden. Den noch offenen PR gegen main separat behandeln. |
| [#8 Telegram-Themenliste](https://github.com/ploeffler/PersonalNewsHost/pull/8) | übernehmen – bereits enthalten | Head ist Vorfahr; Telegram-Publisher und Tests enthalten. |
| [#13 Parallele Sendungsaufbereitung](https://github.com/ploeffler/PersonalNewsHost/pull/13) | übernehmen – bereits enthalten | Head ist Vorfahr; Konfiguration, Generator und Paralleltests enthalten. |
| [#14 RSS-Quellen mit Logos](https://github.com/ploeffler/PersonalNewsHost/pull/14) | übernehmen – bereits enthalten | Head ist Vorfahr; Feed-Picker, Kataloge und Assets enthalten. |
| [#25 Entwicklungsstand nach main](https://github.com/ploeffler/PersonalNewsHost/pull/25) | zurückstellen | Basis ist main; Version 0.1 ist nicht abgenommen. Kein Merge in main im Rahmen von T001. |

## Abnahmegrenze

T001 liefert die vollständige Bestandsaufnahme. Die eigentliche Statusänderung zu „done“ setzt unabhängige Prüfung im Aufgabenprotokoll voraus. Der Inventar-PR wird im Issue verlinkt; die Freigabe von Version 0.1, Produktfunktionen anderer Aufgaben, Diagrammerzeugung und Wiki-Synchronisierung sind ausdrücklich separate Schritte.
