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

## Reliable timing with an external scheduler (optional)

GitHub runs `schedule` triggers on a best-effort basis and drops many of them under load. A free external cron service such as [cron-job.org](https://cron-job.org) can start the workflows through the GitHub API instead; the GitHub schedule stays active as a fallback and additionally starts both workflows at 07:05, 12:05 and 20:05 (Europe/Vienna).

1. Create a **fine-grained personal access token** limited to your PersonalNewsHost repository with **Actions: Read and write** only. Store it only in the cron service.
2. Create two POST jobs with the headers `Accept: application/vnd.github+json`, `Authorization: Bearer <TOKEN>`, `X-GitHub-Api-Version: 2022-11-28`:
   - `https://api.github.com/repos/<OWNER>/<REPO>/actions/workflows/news.yml/dispatches` with body `{"ref":"main","inputs":{"trigger":"schedule"}}`, hourly at minute 17.
   - `https://api.github.com/repos/<OWNER>/<REPO>/actions/workflows/short-updates.yml/dispatches` with body `{"ref":"main"}`, at minutes 7, 22, 37 and 52.
3. GitHub answers **HTTP 204** on success.

With `trigger=schedule` the broadcast workflow applies the same due-slot check as the GitHub schedule, so no duplicate editions are produced. Manual starts from the Actions page (default `trigger=manual`) still always produce. Details: [German guide](../betrieb-und-sicherheit.md#zuverlässiger-zeitplan-mit-externem-taktgeber-optional).

## Troubleshooting

1. Open [GitHub Actions](https://github.com/ploeffler/PersonalNewsHost/actions) and select the failed run.
2. Inspect the failing step and its logs.
3. Run `python3 -m unittest discover -s tests` to check Python regression tests.
4. Check RSS URL reachability, optional extraction tools, model downloads and free GitHub runner quotas.
5. Verify that your private configuration is backed up: GitHub Actions secrets cannot be read back.

The interface language (German or English) is independent of the spoken broadcast language. English news narration is not automatically enabled by switching the website language.
