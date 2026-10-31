# Vollständiges Quellinventar 0.1

Stand: 29.10.2026. Statische AST-/Textanalyse aller Python-Skripte, Tests und Workflowdefinitionen. Keine experimentellen Modelljobs wurden für dieses Inventar ausgeführt.

## Skripte

### `scripts/analysis_tasks.py`

Strict schemas and deterministic baselines, not independent factual verification.

Funktionen: obj, baseline.

Imports: .

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/analyze_topics.py`

Conservative RSS topic clustering, independent of the production publisher.

Funktionen: clean, tokens, similarity, parse_feed, group_items, bilingual_candidates, main.

Imports: argparse, datetime, html, json, pathlib, re, research_language, scripts, unicodedata, urllib, xml.

Explizite HTTP-Ziele: http://www.w3.org.

### `scripts/article_enrichment.py`

Bounded public-article enrichment before editorial drafting and source checks.

Funktionen: plain, url_allowed, same_site, download, records, title_matches, usable, extract, rdrr_fallback, fingerprint, enrich_articles.

Imports: datetime, difflib, editorial_pipeline, generate, hashlib, html, ipaddress, json, re, scripts, shutil, socket, subprocess, urllib.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/assemble_segments.py`

Hilfsmodul ohne Modulbeschreibung

Funktionen: keine.

Imports: json, pathlib, subprocess.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/audit_provider_research.py`

Review pending model-level evidence without external calls.

Funktionen: report.

Imports: json, pathlib, scripts.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/avatar_probe.py`

Non-publishing CPU feasibility probe for an animated-presenter pipeline.

Funktionen: keine.

Imports: json, os, pathlib, subprocess, time.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/broadcast_archive.py`

Keep the two most recent bulletins and attach the homepage playlist.

Funktionen: decorate_news, decorate_homepage, archive_broadcast.

Imports: datetime, json, pathlib, re, shutil.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/build_broadcast_plan.py`

Build a deterministic, review-aware production plan from RSS topic candidates.

Funktionen: clip, build, main.

Imports: argparse, datetime, json, pathlib, re.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/build_hybrid_demo.py`

Experimental MuseTalk intro + existing bulletin. Does not alter docs/ production.

Funktionen: run, probe, main.

Imports: json, pathlib, subprocess.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/check_repository.py`

Local CI: syntax, secrets, document links and tests with network denied.

Funktionen: tracked, secrets, links, no_network, main.

Imports: ast, os, pathlib, re, socket, subprocess, sys, unittest, urllib.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/check_schedule.py`

Produce the newest due edition, including delayed or missed schedule runs.

Funktionen: latest_slot, day_allowed, production_due, published_at, main.

Imports: datetime, email, json, os, pathlib, provider_registry, xml, zoneinfo.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/cleanup_telegram.py`

Compatibility entry point: retention is configured in the Telegram destination.

Funktionen: keine.

Imports: .

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/collect_news.py`

Persist all RSS messages for 24 hours, with broadcast/update membership.

Funktionen: clean, identity, timestamp, parse_feed, effective_time, merge_articles, read, annotate, collect, refresh_annotations.

Imports: argparse, article_enrichment, datetime, email, hashlib, html, json, pathlib, re, scripts, urllib, xml.

Explizite HTTP-Ziele: http://purl.org, http://search.yahoo.com, http://www.w3.org.

### `scripts/configured_providers.py`

Build explicit mock providers from configuration and run optional analyses.

Funktionen: configured_runtime, analyze_entries.

Imports: analysis_tasks, decimal, json, os, pathlib, provider_budget, provider_runtime, re.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/editorial_pipeline.py`

Stored news -> event groups -> editorial draft -> source-support gate -> selection.

Funktionen: prose, words, places, same_event, age, sentence_units, publisher, grouping, evidence_units, render_draft, formulate, numeric_conflicts, wording_conflicts, verify, prepare, select, production_plan.

Imports: datetime, difflib, hashlib, html, json, news_policy, pathlib, re, urllib.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/generate.py`

Zero-cost RSS -> narrated static-image video -> podcast-style video RSS.

Funktionen: german_number, spoken_timestamp, intro_headline_slots, clean, fetch, media_candidates, download_media, spoken_prose, extract_article_text, article_image_candidates, improve_news_image, search_commons_image, feed_timestamp, select_balanced_groups, items_from_feed, run, render_stage, render_time, run_render, adjust_voice_pitch, synthesize, referenced_sources, crosscheck_headline, edit_news, group_news_items, news_section, prepare_sections, subtitle_timestamp, parallel_map, append_silence, write_subtitles, main.

Imports: PIL, broadcast_archive, concurrent, configured_providers, cv2, datetime, difflib, editorial_pipeline, email, html, json, lipsync, math, news_policy, numpy, os, pathlib, re, scripts, subprocess, tempfile, textwrap, threading, time, urllib, validate_config, video_branding, wave, xml, zoneinfo.

Explizite HTTP-Ziele: http://purl.org, http://search.yahoo.com, http://www.w3.org, https://commons.wikimedia.org, https://news.google.com, https://ploeffler.github.io, https://raw.githubusercontent.com.

### `scripts/lipsync.py`

Lightweight offline, audio-driven mouth animation for a transparent presenter PNG.

Funktionen: generate_frames.

Imports: PIL, array, math, pathlib, wave.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/model_residency.py`

Offline validation of model-level residency evidence; never calls provider APIs.

Funktionen: validate_candidate.

Imports: datetime, urllib.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/mouth_motion_probe.py`

Experimental audio-reactive mouth-motion preview, not phoneme-level lip sync.

Funktionen: keine.

Imports: PIL, json, math, numpy, pathlib, subprocess, wave.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/news_policy.py`

Deterministic category mapping and explicit source selection rules.

Funktionen: domain, matches, category, allowed, source_weight.

Imports: urllib.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/processing_location.py`

Processing-location preference validation for future provider integrations.

Funktionen: validate_location.

Imports: .

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/produce_show.py`

Produce a selected show into out/<show_id>; never invoke external publishers.

Funktionen: show_context, produce, main.

Imports: argparse, contextlib, copy, generate, json, pathlib, shows, threading, validate_config.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/provider_budget.py`

Persistent conservative reservations; failed/uncertain attempts remain charged.

Funktionen: money.

Imports: contextlib, datetime, decimal, json, pathlib, sqlite3, uuid.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/provider_catalog.py`

Evidence-first processing location catalog for future paid providers.

Funktionen: evaluate.

Imports: .

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/provider_registry.py`

Provider contracts and safe selection plan for a future PersonalNewsHost 2.0.

Funktionen: _budget, plan, require_executable_version.

Imports: dataclasses, decimal, processing_location, provider_catalog, typing.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/provider_runtime.py`

Offline-first provider contracts, response validation and transactional cache.

Funktionen: canonical, filtered_request.

Imports: analysis_tasks, contextlib, dataclasses, hashlib, json, jsonschema, pathlib, provider_budget, re, sqlite3, time, typing, unicodedata, uuid.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/publish_short_updates_telegram.py`

Two-phase Telegram delivery: persist attempt IDs before contacting Telegram.

Funktionen: read_json, destination, clip, message, prepare, deliver, main.

Imports: argparse, datetime, hashlib, json, os, pathlib, re, sys, time, urllib.

Explizite HTTP-Ziele: https://api.telegram.org, https://ploeffler.github.io.

### `scripts/publish_telegram.py`

Optional Telegram delivery. Credentials are GitHub Actions secrets, never config.json.

Funktionen: shorten, with_topics, send.

Imports: json, os, pathlib, sys, urllib.

Explizite HTTP-Ziele: https://api.telegram.org, https://ploeffler.github.io.

### `scripts/render_musetalk_segment.py`

Hilfsmodul ohne Modulbeschreibung

Funktionen: keine.

Imports: PIL, argparse, cv2, gc, generate, huggingface_hub, json, math, musetalk, numpy, pathlib, resource, soundfile, subprocess, sys, time, torch, traceback, transformers.

Explizite HTTP-Ziele: https://github.com.

### `scripts/render_segment.py`

Render one standalone test segment with local TTS and FFmpeg.

Funktionen: main.

Imports: argparse, generate, json, pathlib, story_card, subprocess, tempfile, textwrap.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/research_language.py`

Language-neutral groundwork for news research (DE/EN).

Funktionen: normalize_language, research_terms, source_metadata, event_tokens, event_candidate.

Imports: re, unicodedata, urllib.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/short_update_video.py`

Render a narrated short-update card with transparent station branding.

Funktionen: render_short_update.

Imports: datetime, pathlib, re, scripts, subprocess, tempfile, textwrap, video_branding.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/short_updates.py`

Conservative, extractive short news updates. No article scraping or invented facts.

Funktionen: canonical, select_updates, main.

Imports: copy, datetime, difflib, generate, hashlib, json, pathlib, re, scripts, short_update_video, urllib.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/shows.py`

Resolve isolated show configurations without changing the caller's configuration.

Funktionen: merge_objects, resolve_shows.

Imports: copy, re.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/story_card.py`

Generate original editorial story artwork without external image licensing.

Funktionen: render.

Imports: PIL, hashlib, pathlib, textwrap.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/validate_config.py`

Validate configuration locally; errors never echo configuration values/secrets.

Funktionen: validate_config, main.

Imports: argparse, json, jsonschema, math, pathlib, shows, sys, urllib, zoneinfo.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

### `scripts/video_branding.py`

Shared transparent station logo and the red short-update label.

Funktionen: apply_branding.

Imports: PIL, pathlib, re.

Explizite HTTP-Ziele: keine festen Hosts; ggf. übergebene URLs.

## Tests

- `tests/test_article_enrichment.py`: 11 Python-Testfälle.
- `tests/test_article_markup.py`: 15 Python-Testfälle.
- `tests/test_bilingual_broadcast_plan.py`: 3 Python-Testfälle.
- `tests/test_bilingual_topics.py`: 4 Python-Testfälle.
- `tests/test_broadcast_archive.py`: 3 Python-Testfälle.
- `tests/test_collect_news.py`: 6 Python-Testfälle.
- `tests/test_config_validation.py`: 7 Python-Testfälle.
- `tests/test_editorial_pipeline.py`: 14 Python-Testfälle.
- `tests/test_editorial_production.py`: 4 Python-Testfälle.
- `tests/test_editorial_report_browser.cjs`: 0 Python-Testfälle / JavaScript-Prüfung.
- `tests/test_feed_picker.cjs`: 0 Python-Testfälle / JavaScript-Prüfung.
- `tests/test_feed_picker_browser.cjs`: 0 Python-Testfälle / JavaScript-Prüfung.
- `tests/test_feed_research.py`: 10 Python-Testfälle.
- `tests/test_intro_headlines.py`: 3 Python-Testfälle.
- `tests/test_model_residency.py`: 3 Python-Testfälle.
- `tests/test_news_list.cjs`: 0 Python-Testfälle / JavaScript-Prüfung.
- `tests/test_news_list_browser.cjs`: 0 Python-Testfälle / JavaScript-Prüfung.
- `tests/test_news_policy.py`: 4 Python-Testfälle.
- `tests/test_news_selection.py`: 8 Python-Testfälle.
- `tests/test_parallel_production.py`: 6 Python-Testfälle.
- `tests/test_playlist.cjs`: 0 Python-Testfälle / JavaScript-Prüfung.
- `tests/test_playlist_browser.cjs`: 0 Python-Testfälle / JavaScript-Prüfung.
- `tests/test_provider_budget.py`: 8 Python-Testfälle.
- `tests/test_provider_registry.py`: 7 Python-Testfälle.
- `tests/test_provider_runtime.py`: 14 Python-Testfälle.
- `tests/test_rdrr_extraction.py`: 3 Python-Testfälle.
- `tests/test_render_load.py`: 1 Python-Testfälle.
- `tests/test_render_progress.py`: 6 Python-Testfälle.
- `tests/test_repository_checks.py`: 2 Python-Testfälle.
- `tests/test_research_language.py`: 5 Python-Testfälle.
- `tests/test_schedule.py`: 14 Python-Testfälle.
- `tests/test_short_updates.py`: 4 Python-Testfälle.
- `tests/test_short_updates_telegram.py`: 9 Python-Testfälle.
- `tests/test_short_updates_video.py`: 3 Python-Testfälle.
- `tests/test_shows.py`: 10 Python-Testfälle.
- `tests/test_source_logos.py`: 12 Python-Testfälle.
- `tests/test_speech_config.py`: 2 Python-Testfälle.
- `tests/test_spoken_timestamp.py`: 3 Python-Testfälle.
- `tests/test_subtitles.py`: 6 Python-Testfälle.
- `tests/test_telegram.py`: 8 Python-Testfälle.
- `tests/test_video_smoke.py`: 5 Python-Testfälle.

## Konfiguration


`config.json`: `title`, `production_version`, `language`, `voice`, `max_items`, `max_description_chars`, `feeds`, `background`, `presenter`, `tts_engine`, `piper_length_scale`, `presenter_settings`, `presenter_settings.name`, `presenter_settings.gender`, `presenter_settings.portrait`, `presenter_settings.background`, `presenter_settings.voice_model`, `presenter_settings.lip_sync`, `presenter_settings.lip_sync.enabled`, `presenter_settings.lip_sync.engine`, `presenter_settings.lip_sync.fallback`, `presenter_settings.lip_sync.mouth`, `presenter_settings.lip_sync.mouth.x`, `presenter_settings.lip_sync.mouth.y`, `presenter_settings.lip_sync.mouth.width`, `presenter_settings.lip_sync.mouth.height`, `presenter_settings.lip_sync.note`, `presenter_settings.lip_sync.fps`, `presenter_settings.scenes`, `presenter_settings.scenes.show_headlines`, `presenter_settings.scenes.intro_mode`, `presenter_settings.scenes.intro_text`, `presenter_settings.scenes.outro_text`, `presenter_settings.scenes.intro_static_type`, `presenter_settings.scenes.intro_static_color`, `presenter_settings.scenes.intro_static_image`, `presenter_settings.desk_foreground`, `voice_pitch_semitones`, `telegram`, `telegram.enabled`, `telegram.recipient_type`, `telegram.delivery`, `telegram.caption`, `telegram.target`, `automation`, `automation.enabled`, `automation.interval_hours`, `automation.start_hour_local`, `automation.timezone`, `automation.days`, `advanced_services`, `advanced_services.processing_region`, `advanced_services.processing_country`, `advanced_services.require_verified_region`, `advanced_services.news_provider`, `advanced_services.voice_provider`, `advanced_services.avatar_provider`, `advanced_services.video_provider`, `advanced_services.max_per_video_eur`, `advanced_services.max_per_month_eur`, `advanced_services.allow_paid`, `editorial`, `editorial.style`, `editorial.max_sentences`, `editorial.crosscheck`, `editorial.crosscheck.enabled`, `editorial.crosscheck.max_sources`, `editorial.crosscheck.method`, `editorial.crosscheck.note`, `editorial.topic_clustering`, `editorial.topic_clustering.enabled`, `editorial.topic_clustering.mode`, `editorial.topic_clustering.note`, `editorial.selection`, `editorial.selection.mode`, `editorial.selection.note`, `editorial.broadcast_sections`, `editorial.broadcast_sections.enabled`, `editorial.broadcast_sections.default`, `editorial.broadcast_sections.sections`, `editorial.broadcast_sections.feed_sections`, `editorial.broadcast_sections.feed_sections.https://www.bmi.gv.at/rss/stmk_presse.xml`, `editorial.broadcast_sections.feed_sections.https://www.kleinezeitung.at/rss/steiermark`, `editorial.pipeline`, `editorial.pipeline.enabled`, `editorial.pipeline.method`, `editorial.pipeline.max_store_age_minutes`, `media`, `media.mode`, `media.max_download_mb`, `media.web_image_fallback`, `media.enhancement`, `media.enhancement_modes`, `media.prefer_article_images`, `station_logo`, `article_enrichment`, `article_enrichment.enabled`, `article_enrichment.max_fetches_per_run`, `production`, `production.parallel_workers`, `providers`, `provider_tasks`, `provider_budgets`, `provider_budgets.allow_paid`, `provider_budgets.monthly_budget_eur`, `provider_budgets.per_run_budget_eur`, `provider_budgets.unit_limits`.

`config.example.json`: `title`, `production_version`, `language`, `voice`, `max_items`, `max_description_chars`, `feeds`, `background`, `presenter`, `station_logo`, `tts_engine`, `piper_length_scale`, `presenter_settings`, `presenter_settings.name`, `presenter_settings.gender`, `presenter_settings.portrait`, `presenter_settings.background`, `presenter_settings.voice_model`, `presenter_settings.lip_sync`, `presenter_settings.lip_sync.enabled`, `presenter_settings.lip_sync.engine`, `presenter_settings.lip_sync.fallback`, `presenter_settings.lip_sync.mouth`, `presenter_settings.lip_sync.mouth.x`, `presenter_settings.lip_sync.mouth.y`, `presenter_settings.lip_sync.mouth.width`, `presenter_settings.lip_sync.mouth.height`, `presenter_settings.lip_sync.note`, `presenter_settings.lip_sync.fps`, `presenter_settings.scenes`, `presenter_settings.scenes.show_headlines`, `presenter_settings.scenes.intro_mode`, `presenter_settings.scenes.intro_text`, `presenter_settings.scenes.outro_text`, `presenter_settings.scenes.intro_static_type`, `presenter_settings.scenes.intro_static_color`, `presenter_settings.scenes.intro_static_image`, `presenter_settings.desk_foreground`, `voice_pitch_semitones`, `telegram`, `telegram.enabled`, `telegram.recipient_type`, `telegram.delivery`, `telegram.caption`, `automation`, `automation.enabled`, `automation.interval_hours`, `automation.start_hour_local`, `automation.timezone`, `automation.days`, `advanced_services`, `advanced_services.processing_region`, `advanced_services.processing_country`, `advanced_services.require_verified_region`, `advanced_services.news_provider`, `advanced_services.voice_provider`, `advanced_services.avatar_provider`, `advanced_services.video_provider`, `advanced_services.max_per_video_eur`, `advanced_services.max_per_month_eur`, `advanced_services.allow_paid`, `editorial`, `editorial.style`, `editorial.max_sentences`, `editorial.crosscheck`, `editorial.crosscheck.enabled`, `editorial.crosscheck.max_sources`, `editorial.crosscheck.method`, `editorial.crosscheck.note`, `editorial.broadcast_sections`, `editorial.broadcast_sections.enabled`, `editorial.broadcast_sections.default`, `editorial.broadcast_sections.sections`, `editorial.broadcast_sections.feed_sections`, `editorial.broadcast_sections.feed_sections.https://www.bmi.gv.at/rss/stmk_presse.xml`, `editorial.broadcast_sections.feed_sections.https://www.kleinezeitung.at/rss/steiermark`, `editorial.pipeline`, `editorial.pipeline.enabled`, `editorial.pipeline.method`, `editorial.pipeline.max_store_age_minutes`, `media`, `media.mode`, `media.max_download_mb`, `media.web_image_fallback`, `media.enhancement`, `media.enhancement_modes`, `media.prefer_article_images`, `fork_config_initialized`, `short_updates`, `short_updates.enabled`, `short_updates.freshness_minutes`, `short_updates.interval_minutes`, `article_enrichment`, `article_enrichment.enabled`, `article_enrichment.max_fetches_per_run`, `production`, `production.parallel_workers`, `feed_categories`, `category_filter`, `source_policy`, `source_policy.blocked_domains`, `source_policy.excluded_keywords`, `source_policy.weights`, `providers`, `provider_tasks`, `provider_budgets`, `provider_budgets.allow_paid`, `provider_budgets.monthly_budget_eur`, `provider_budgets.per_run_budget_eur`, `provider_budgets.unit_limits`.

## Workflows und Laufzeiten

Timeouts sind Obergrenzen. Tatsächliche Dauer hängt von Runner, Modellcache und Eingangsmengen ab; für nicht ausgeführte manuelle Experimente wird keine gemessene Dauer behauptet. Der vorherige Render-CI-Lauf 40903509897 ist nachweislich erfolgreich; lokale Gesamtprüfzeiten sind im Abnahmebericht festgehalten.

- `analyze-rss-topics.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: analyze (Timeout 5 min).
- `avatar-test.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: probe (Timeout 10 min).
- `foundation-ci.yml`: Trigger `{"push": {"branches": ["Full-featured-Newsoutlet"]}, "pull_request": "", "workflow_dispatch": ""}`; Jobs: foundation (Timeout 15 min).
- `lipsync-readiness.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: cpu-readiness (Timeout 8 min).
- `musetalk-25fps-benchmark.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: official-preflight (Timeout 20 min).
- `musetalk-audio-test.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: audio (Timeout 15 min).
- `musetalk-conditioned-unet.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: conditioned-unet (Timeout 15 min).
- `musetalk-cpu-optimize.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: optimize (Timeout 15 min).
- `musetalk-cpu-smoke.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: cpu-compatibility (Timeout 12 min).
- `musetalk-dependency-test.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: dependencies (Timeout 15 min).
- `musetalk-face-detection.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: face (Timeout 15 min).
- `musetalk-first-frame.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: first-frame (Timeout 15 min).
- `musetalk-first-video.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: first-video (Timeout 15 min).
- `musetalk-hybrid-interpolation.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: official-preflight (Timeout 20 min).
- `musetalk-model-load.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: real-model-load (Timeout 12 min).
- `musetalk-official-frame.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: official-preflight (Timeout 15 min).
- `musetalk-official-preflight.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: official-preflight (Timeout 15 min).
- `musetalk-official-video.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: official-preflight (Timeout 15 min).
- `musetalk-pipeline-preflight.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: preflight (Timeout 8 min).
- `musetalk-piper-10fps.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: official-preflight (Timeout 20 min).
- `musetalk-piper-intro.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: official-preflight (Timeout 20 min).
- `musetalk-quality-check.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: quality-check (Timeout 15 min).
- `musetalk-repeat-benchmark.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: repeat (Timeout 15 min).
- `musetalk-unet-forward.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: cpu-forward (Timeout 15 min).
- `musetalk-vae-cpu.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: vae (Timeout 15 min).
- `news.yml`: Trigger `{"workflow_dispatch": "", "schedule": [{"cron": "17 * * * *"}]}`; Jobs: generate (Timeout 40 min).
- `parallel-broadcast.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: prepare (Timeout Runnerstandard min), render (Timeout Runnerstandard min), assemble (Timeout Runnerstandard min).
- `parallel-musetalk-broadcast.yml`: Trigger `{"workflow_dispatch": ""}`; Jobs: prepare (Timeout Runnerstandard min), render (Timeout 35 min), assemble (Timeout Runnerstandard min).
- `render-regression.yml`: Trigger `{"pull_request": {"paths": ["scripts/**", "tests/**", "assets/**", "config.json", "config.example.json", "config.shows.example.json", "config.schema.json", "requirements.txt", ".github/workflows/render-regression.yml"]}, "workflow_dispatch": ""}`; Jobs: render (Timeout 15 min).
- `research-feed-catalogs.yml`: Trigger `{"workflow_dispatch": {"inputs": {"group": {"description": "Welche Quellengruppe recherchieren?", "required": "true", "default": "both", "type": "choice", "options": ["both", "news", "authorities"]}}}}`; Jobs: news (Timeout 25 min), authorities (Timeout 35 min), source-logos (Timeout 20 min).
- `short-updates.yml`: Trigger `{"workflow_dispatch": "", "push": {"branches": ["main"], "paths": [".github/workflows/short-updates.yml", "scripts/video_branding.py", "scripts/short_update_video.py", "assets/logo-video.png", "scripts/article_enrichment.py", "scripts/collect_news.py", "scripts/short_updates.py", "scripts/publish_short_updates_telegram.py"]}, "schedule": [{"cron": "7,22,37,52 * * * *"}]}`; Jobs: updates (Timeout 15 min).
- `telegram-test.yml`: Trigger `{"workflow_dispatch": {"inputs": {"target": {"description": "Secret destination", "type": "choice", "options": ["default", "secondary"], "default": "default"}, "delivery": {"description": "Send a test message or resend the current video", "type": "choice", "options": ["text", "video"], "default": "text"}}}}`; Jobs: test (Timeout 3 min).
- `wiki-sync.yml`: Trigger `{"workflow_dispatch": "", "push": {"branches": ["main"], "paths": ["docs/guide/**", ".github/workflows/wiki-sync.yml"]}}`; Jobs: publish (Timeout Runnerstandard min).

## Externe Datenflüsse und Zugangsdaten

- RSS-/Artikel-/Medien- und Suchabrufe: konfigurierbare öffentliche HTTP(S)-Quellen. Quelltexte sind Daten, keine ausführbaren Anweisungen.
- TTS und Video: lokale Prozesse (Piper/eSpeak/FFmpeg), keine neuen externen Inferenzadapter in 0.1.
- Telegram: optionale bestehende Bot-API über Secrets; Tests mocken den Versand.
- Modelle/Pakete und MuseTalk-Experimente: Downloads u.a. von GitHub, Hugging Face, PyPI und PyTorch. Experimentelle Modellqualität und Laufzeit gehören nicht zur 0.1-Abnahme.
- GitHub-Workflows: Repository-/Pages-Zugriffe gemäß Permissions. Actions sind auf Commit-SHAs festgelegt; direkte Python-Abhängigkeiten in requirements-constraints.txt festgesetzt. Das ist kein vollständiger transitiver GPU-Umgebungslock.
- Neue Provideranalyse: nur explizit aktivierte lokale Mocks, gefilterte öffentliche Eingabefelder; Secretwerte werden nur für Erkennung aus benannten Umgebungsvariablen gelesen, nie in Providerpayloads übertragen.

## Offene PRs und Integrationsbewertung

PR #7 (Renderfortschritt), #8 (Telegram-Themenliste), #13 (parallele Vorbereitung) und #14 (RSS-Quellenverwaltung) wurden aufgrund der ausdrücklichen Nutzeranweisung in Full-featured-Newsoutlet integriert und dort gemeinsam geprüft. Keine Übernahme nach main. PR #25 ist der offene Vergleich dieses Entwicklungsbranches mit main; er wird nicht gemergt. Vorherige vorläufige Zurückstellungsbewertungen sind dadurch für diesen Branch überholt.

Siehe [Architektur](architektur-ist.md), [Version-0.1-Abnahme](abnahme-0.1.md) und [Provider-Laufzeit](provider-runtime.md).
