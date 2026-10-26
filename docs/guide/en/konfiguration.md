# Configuration and privacy

**Language:** [Deutsch](../konfiguration.md) · English

## Public defaults and private configuration

PersonalNewsHost distinguishes between **public starter settings** and **private production settings**.

- `config.json` and `docs/config.json` are public. They provide defaults and a fallback when no private secret is configured.
- `PERSONALNEWSHOST_CONFIG` is an encrypted GitHub Actions secret containing your JSON configuration. The production workflow prefers it over public defaults.
- GitHub does not allow reading back a stored Actions secret. **Download and keep a private JSON backup** before saving.
- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` must be separate Actions secrets. Never include credentials in public JSON files.

## Getting started

1. Open [Settings](https://ploeffler.github.io/PersonalNewsHost/settings.html?lang=en) or the corresponding GitHub Pages URL of your fork.
2. Review the RSS feeds and other settings loaded from the public `docs/config.json`.
3. Download a local JSON backup.
4. Create a [fine-grained GitHub personal access token](https://github.com/settings/personal-access-tokens/new) limited to your repository with **Secrets: Read and write** permission. Image uploads additionally require **Contents: Read and write**.
5. Confirm the save operation and choose **Save to GitHub**. The browser encrypts the configuration before uploading it as `PERSONALNEWSHOST_CONFIG`.
6. Run the [news workflow](https://github.com/ploeffler/PersonalNewsHost/actions/workflows/news.yml) manually to verify production.

**Important:** The settings page cannot retrieve the saved secret. Reimport your JSON backup for future changes. The browser-based save flow still requires end-to-end verification with a real token.

## Configuration keys

| Key | Purpose |
| --- | --- |
| `feeds` | HTTPS RSS feed URLs |
| `max_items` | Stories per broadcast |
| `editorial.style` | News writing style (`classic` by default) |
| `media.mode` | Media selection (`images_and_videos` by default) |
| `presenter_settings` | Presenter, voice, scenes and lip-sync settings |
| `automation.enabled` | Enable or disable automatic generation |
| `automation.interval_hours` | Interval between scheduled broadcasts |
| `automation.timezone` | IANA time zone, e.g. `Europe/Vienna` |
| `telegram.enabled` | Enable Telegram publishing |

Scheduled GitHub Actions checks run approximately once per hour, but execution times are not guaranteed. Manual runs remain possible.

## Forks, security and costs

Forks do **not** inherit the upstream repository's Actions secrets. Uploaded images and public repository files are visible to others. Never paste tokens into chats, issues or public files.

The free CPU version targets **€0 additional monthly cost**, subject to GitHub free quotas and third-party terms. Paid GPU services are not enabled by default. Before replacing older public configuration files with neutral defaults, first back up the current settings and save them privately to avoid losing working configuration.
