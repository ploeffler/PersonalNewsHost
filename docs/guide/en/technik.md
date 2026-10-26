# Technical architecture and workflows

**Language:** [Deutsch](../technik.md) · English

## Production pipeline

```text
RSS feeds → scripts/generate.py
          → article extraction (local rdrr; RSS fallback)
          → rule-based news editing
          → Piper TTS (eSpeak fallback) + FFmpeg
          → docs/latest.mp4, docs/index.html,
             docs/transcript.txt, docs/feed.xml
          → GitHub Pages
```

The main workflow is [Generate news video](https://github.com/ploeffler/PersonalNewsHost/actions/workflows/news.yml). Production runs on GitHub Actions without a dedicated server. The spoken broadcast remains German; the DE/EN website selector does not change narration.

## Research and source handling

`scripts/generate.py` reads RSS feeds, selects stories and attempts local article extraction with `rdrr`. If extraction fails, it falls back to RSS descriptions. Article extraction does **not** constitute independent fact-checking.

`scripts/research_language.py` currently provides language normalization, language-tagged search terms and source metadata for German and English. This is groundwork only: automated translation and cross-language event matching are not yet connected to the production pipeline. Similar stories must not be treated as corroboration without independent verification.

## Experimental video pipeline

```text
RSS feeds → scripts/analyze_topics.py
          → scripts/build_broadcast_plan.py
          → parallel Piper/FFmpeg segments
          → optional experimental MuseTalk segments
          → scripts/assemble_segments.py
          → test artifact (not automatically published)
```

Experimental MuseTalk and lip-sync workflows are separate from the standard published broadcast. Their presence does not imply production readiness.

## Important files

| Path | Purpose |
| --- | --- |
| `.github/workflows/news.yml` | Scheduled/manual production |
| `scripts/generate.py` | Main news generator |
| `scripts/research_language.py` | DE/EN research groundwork |
| `scripts/analyze_topics.py` | Candidate topic clustering |
| `scripts/build_broadcast_plan.py` | Experimental segment plan |
| `scripts/assemble_segments.py` | Experimental video assembly |
| `docs/settings.html` and `docs/i18n.js` | Web settings and interface language |
| `docs/guide/` | Documentation |
| `docs/` | Published Pages assets |

## Local tests (Ubuntu)

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg espeak-ng fonts-dejavu-core
python3 -m pip install piper-tts
npm install --global rdrr@0.7.0
python3 -m unittest discover -s tests
python3 scripts/generate.py
```

If the Piper model is unavailable, the generator can use eSpeak. Running the full generator creates media files and requires available feed URLs and suitable runtime dependencies.

## Versions and budget

- **v1.0 CPU/free:** Existing local/free pipeline, aiming for €0 additional monthly cost within available quotas.
- **v2.0 GPU/optional paid:** Planned provider architecture only. The production workflow blocks unimplemented paid versions.

Provider selection, data processing region, location evidence and spending limits are preparatory configuration features. A company headquarters is not proof of data residency. Provider location verification and enforceable spending controls are required before paid production can be enabled.

The source of truth for detailed technical implementation remains the repository code and [German technical guide](../technik.md), which may contain additional experimental details.
