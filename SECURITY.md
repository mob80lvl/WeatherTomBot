# Security checklist

1. Never ship `.env` with the package.
2. Rotate any Telegram token/API key/password that appeared in source code, screenshots, chats or public repositories.
3. Set a long random `SECRET_KEY`.
4. Use a strong unique admin password.
5. Restrict file permissions on `.env` to the service user.
6. Keep database backups outside the public web directory.
7. Review admin routes before public deployment.
8. Use HTTPS for webhooks and admin access.
9. Keep dependencies updated deliberately and test after updates.
10. Before sale, remove logs containing tokens, payment payloads, personal data or other secrets.


## Commercial feature security

- API keys are stored only as SHA-256 hashes.
- `CRON_SECRET` protects the scheduler endpoint when configured.
- Keep `.env`, `features.json`, `api_keys.json`, logs and generated media private.
- Telegram channel posting requires the bot to be granted the required administrator permissions.
- Do not expose `TELEGRAM_TOKEN` or `OPENAI_API_KEY`.
