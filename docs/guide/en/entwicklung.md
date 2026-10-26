# Development history and roadmap

**Language:** [Deutsch](../entwicklung.md) · English

## Why PersonalNewsHost exists

PersonalNewsHost explores whether a configurable, cloud-hosted news video workflow can be built iteratively from a prompt, without a personal server, a permanently open browser or additional monthly fees. GitHub Actions and GitHub Pages provide execution and publishing within applicable free quotas.

The project illustrates the practical use of AI-assisted software development. The resulting workflows use conventional software and locally executable models; a continuous ChatGPT session is not required for production.

## Development milestones

| Phase | Development |
| --- | --- |
| Initial concept (21 October 2026) | Configurable RSS sources, hourly video broadcast, replaceable studio background and presenter |
| Zero-cost architecture | GitHub Actions, GitHub Pages and locally executable tools instead of paid APIs |
| First working pipeline | RSS-to-narration, FFmpeg video, website, transcript and video RSS |
| Speech improvements | German Piper voice with eSpeak fallback |
| Topic analysis | Conservative detection of potentially overlapping stories |
| Parallel experiments | Separate intro, news and outro rendering |
| Lip-sync experiments | MuseTalk/Piper test workflows, separate from published production |
| Web configuration | GitHub Pages settings, private Actions secret storage and optional Telegram |
| Source extraction | Local rdrr article extraction with RSS fallback |
| DE/EN groundwork | Bilingual web interface, English documentation and language-aware research metadata |

Milestones describe development and test work, **not a claim that every experimental feature is production-ready**.

## Current priorities

1. Stabilize the main news workflow and verify successful end-to-end generation.
2. Complete and test bilingual HTML controls, help text and error messages.
3. Keep German and English documentation aligned with actual code and tested behavior.
4. Extend research metadata and cautiously match stories across languages without inventing corroboration.
5. Improve visual quality, source handling and presenter integration within available free runner resources.
6. Keep optional paid GPU services disabled until enforceable budgets, provider adapters and data-location evidence are implemented.

## Acceptance principles

The free version should let a user configure RSS sources and produce a video plus video RSS feed through a website and GitHub workflows, without an always-on personal server. GitHub quotas, media licensing, accuracy checks and privacy requirements still apply.

The UI language (DE/EN) is independent of the spoken news language. English spoken broadcasts are a separate future feature.

See the [German development log](../entwicklung.md) for the more detailed historical chronology and test references.
