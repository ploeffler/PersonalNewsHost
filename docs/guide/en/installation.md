# PersonalNewsHost — Step-by-step installation

**Language:** [Deutsch](../installation.md) · English

This guide explains how to run PersonalNewsHost in **your own GitHub fork**, without a dedicated server or permanently open browser. Free GitHub quotas and terms still apply.

## 1. Requirements

You need a GitHub account and a browser. Telegram is optional.

## 2. Fork the repository

1. Open [PersonalNewsHost](https://github.com/ploeffler/PersonalNewsHost).
2. Select **Fork** and create a copy under your GitHub account.
3. Work in **your own fork**. GitHub does not copy the original repository's Actions secrets into forks.

## 3. Enable GitHub Actions

1. Open the **Actions** tab of your fork.
2. Enable workflows if GitHub prompts you to do so.
3. Automatic production is disabled by default; you can trigger a manual test.

## 4. Configure GitHub Pages

1. Open **Settings → Pages** in your fork.
2. Choose **Deploy from a branch**, branch **main**, folder **/docs** and save.
3. Your site will usually be available at `https://YOUR-USERNAME.github.io/PersonalNewsHost/`. Deployment can take a few minutes.

## 5. Open the web configurator

1. Open the GitHub Pages site of your fork and navigate to `settings.html?lang=en`.
2. Initially, the page loads public defaults from `docs/config.json`.
3. Configure RSS feeds, presenter, output and automation. Only use sources and media you are allowed to republish.

## 6. Save your configuration securely

The configurator can encrypt settings and store them in your fork's GitHub Actions secret `PERSONALNEWSHOST_CONFIG`.

1. Create a **fine-grained GitHub personal access token** limited to your fork with **Secrets: Read and write**. Manual workflow dispatch also requires **Actions: Read and write**; image uploads require **Contents: Read and write**.
2. Enter the token on the settings page.
3. Confirm saving and select **Save to GitHub**.
4. Check **Settings → Secrets and variables → Actions** for `PERSONALNEWSHOST_CONFIG`.
5. **Download and keep a local JSON backup.** GitHub does not let you read back secret values after saving.

**Security note:** Browser-side encryption and saving through the GitHub API still require a full end-to-end test with a real token. Use only a trusted site and never put secrets into public `config.json`.

## 7. Generate your first broadcast

1. Open **Actions → Generate news video** in your fork.
2. Choose **Run workflow** on **main**.
3. Wait for the run and inspect job logs if it fails.
4. Open your Pages site to find `latest.mp4` and the video RSS feed `feed.xml`.

## 8. Enable scheduled production

Configure your preferred schedule in the web interface and save the private configuration again. GitHub Actions checks the schedule periodically, but exact execution times are not guaranteed.

## 9. Optional Telegram setup

1. Create your own bot using [@BotFather](https://t.me/BotFather).
2. Start a private chat or add the bot to your channel with only the required permissions.
3. Store `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` as Actions secrets **in your fork**.
4. Enable Telegram in the web settings, save and run a test.

A separate workflow attempts to delete Telegram messages **no earlier than 25 hours after sending**. GitHub scheduling delays may postpone deletion. The Pages video is unaffected. Telegram is disabled by default.

## 10. Troubleshooting and security

- **No broadcast:** Check the Actions logs, feed URLs and configuration validity.
- **Missing secret:** Check `PERSONALNEWSHOST_CONFIG` in your own repository.
- **Saving fails:** Verify the token's repository scope and permissions.
- **Telegram fails:** Check the bot token, chat ID, permissions and workflow logs.
- **Fork security:** Forks do not inherit secrets, but public files and history are copied.
- **Never commit credentials:** Deleting them later may not remove them from Git history.

Continue with [Configuration and privacy](konfiguration.md) · [Operations and security](betrieb-und-sicherheit.md) · [Technical architecture](technik.md).
