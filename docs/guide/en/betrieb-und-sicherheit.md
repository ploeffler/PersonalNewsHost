# Operations and security

**Language:** [Deutsch](../betrieb-und-sicherheit.md) · English

## Production and experimental features

PersonalNewsHost runs on GitHub Actions and publishes a video, transcript, news page and video RSS feed via GitHub Pages. The default CPU pipeline uses locally executable open-source tools. RSS processing and article extraction do not imply independent fact-checking.

Some capabilities, including advanced lip sync and MuseTalk, are experimental. A successful experimental build does not automatically publish its video. Check the [workflow runs](https://github.com/ploeffler/PersonalNewsHost/actions) for the current state instead of assuming every feature is production-ready.

## Costs and responsibility

The project targets **€0 additional monthly costs**, but GitHub Actions, GitHub Pages and external services have quotas, terms and limitations. This is not a cost or uptime guarantee. Paid services must remain disabled unless deliberately configured and budget-checked.

Feed content is untrusted input. Publishers and operators must respect copyrights, licenses, image rights and personal rights. Automatically generated summaries are not independent verification of factual accuracy. The operator remains responsible for published material.

## GitHub secrets and forks

A fork does **not** inherit the original repository's Actions secrets. Configure your own secrets under **Settings → Secrets and variables → Actions**:

- `PERSONALNEWSHOST_CONFIG`: optional private JSON configuration
- `TELEGRAM_BOT_TOKEN`: your own Telegram bot token
- `TELEGRAM_CHAT_ID`: your own destination

Never put credentials into `config.json`, commits, issues, pull requests, screenshots or logs. Restrict workflow write access and rotate credentials immediately if exposure is suspected. Uploaded repository images are public.

## Telegram publishing and cleanup

Telegram is optional and disabled by default. Create a bot with [@BotFather](https://t.me/BotFather), grant only the necessary permissions and set the two Telegram secrets in **your own fork**.

Retention and deletion are configured directly in the Telegram destination. PersonalNewsHost does not delete messages.

Telegram integration should be tested with a real bot and destination before relying on it.

## Troubleshooting

1. Open [GitHub Actions](https://github.com/ploeffler/PersonalNewsHost/actions) and select the failed run.
2. Inspect the failing step and its logs.
3. Run `python3 -m unittest discover -s tests` to check Python regression tests.
4. Check RSS URL reachability, optional extraction tools, model downloads and free GitHub runner quotas.
5. Verify that your private configuration is backed up: GitHub Actions secrets cannot be read back.

The interface language (German or English) is independent of the spoken broadcast language. English news narration is not automatically enabled by switching the website language.
